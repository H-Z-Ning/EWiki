

from typing import List, Dict, Any, Optional
import logging, sys, uuid
from pathlib import Path
from shutil import copytree
import shutil
from fastapi import UploadFile, File
# -------------- 基础 --------------
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from datetime import datetime
import shutil
from fastapi import UploadFile, File
# -------------- 业务模块 --------------

from src.llm import generate
from src.rag import write_page,plan_wiki_structure,write_page_from_dir
import os
os.environ.pop('all_proxy', None)   # 小写
os.environ.pop('ALL_PROXY', None)   # 大写（Unix 下常见）
# -------------- 日志 --------------
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger("EWiki_mini")

# -------------- 可选依赖 --------------
try:
    import numpy as np
except Exception:
    log.exception("numpy is required")
    sys.exit(1)

try:
    from tqdm import tqdm
except Exception:
    def tqdm(x, **k): return x

try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None

try:
    import openai
except Exception:
    openai = None

# -------------- 全局路径与内存缓存 --------------
REPOS_DIR       = Path("./repos")          # 导入的源码
OUTPUT_BASE     = Path("./output")         # 所有 wiki 产物
REPOS_DIR.mkdir(exist_ok=True)
OUTPUT_BASE.mkdir(exist_ok=True)


project_readmes:  Dict[str, str]              = {}
project_modules:  Dict[str, List[str]]        = {}

project_knowledge_bases: Dict[str, List[str]] = {}


# 在 API 定义部分添加知识库相关接口
class KnowledgeBaseUploadReq(BaseModel):
    description: str = ""










def load_existing_projects():
    for project_dir in OUTPUT_BASE.iterdir():
        if not project_dir.is_dir():
            continue
        project = project_dir.name

        # 加载 PROJECT.md
        project_md = project_dir / "PROJECT.md"
        if project_md.exists():
            project_readmes[project] = project_md.read_text(encoding="utf-8")

        # 加载模块列表
        modules_dir = project_dir / "modules"
        if modules_dir.exists():
            modules = [f.stem for f in modules_dir.glob("*.md")]
            project_modules[project] = modules

    log.info("[load_existing_projects] 已加载 %s 个项目", len(project_readmes))



# ==============================================================================
# 工具函数
# ==============================================================================
def import_project(src_path: str) -> str:
    """把本地目录拷贝到 repos/ 下，返回项目名（目录名）"""
    src = Path(src_path).expanduser().resolve()
    if not src.is_dir():
        raise RuntimeError("路径不存在或非目录")
    name = src.name or "untitled"
    dst = REPOS_DIR / name

    # 如果目录已存在，直接使用原名称（不再添加随机串）
    if dst.exists():
        log.info("project already exists, using existing directory: %s", name)
        # >>> 新增：已有 wiki 则直接返回，不再 build
        if (OUTPUT_BASE / name / "PROJECT.md").exists():
            log.info("wiki already exists, skip build for %s", name)
            return name
        return name

    copytree(src, dst)
    log.info("copied %s -> %s", src, dst)
    return name


# app.py 顶部已 import logging，logger 叫 log
# 如你原来没定义，请加一行：
# log = logging.getLogger("EWiki_mini")

def build_wiki(project: str, language: str = "zh") -> None:
    """
    1. 拷贝到 repos/
    2. 解析文件树 + README
    3. RAG 生成 wiki 结构
    4. 逐页生成 markdown
    5. 写 PROJECT.md 总览
    6. 落盘 + 内存缓存
    """
    import xml.etree.ElementTree as ET
    from src.utils import write_markdown

    # ---------- 0. 路径 ----------
    src = REPOS_DIR / project
    out = OUTPUT_BASE / project
    data_out = out / "data"
    source_code_stone = data_out / "source_code_stone"
    java_callgraph_stone = data_out / "java_callgraph_stone"
    out.mkdir(parents=True, exist_ok=True)
    data_out.mkdir(parents=True, exist_ok=True)
    java_callgraph_stone.mkdir(parents=True, exist_ok=True)
    source_code_stone.mkdir(parents=True, exist_ok=True)
    log.info("[build_wiki] >>> project=%s | language=%s | src=%s | out=%s", project, language, src, out)

    # ---------- 1. 文件树 & README ----------
    file_tree = "\n".join(
        str(p.relative_to(src))
        for p in sorted(src.rglob("*"))
        if p.is_file() and not str(p.name).startswith(".")
    )
    readme_file = src / "README.md"
    readme = readme_file.read_text(encoding="utf-8") if readme_file.exists() else "No README"
    log.info("[build_wiki] file_tree=%s lines | readme=%s chars", len(file_tree.splitlines()), len(readme))

    # ---------- 2. RAG 实例 ----------
    # ---------- 3. 生成 wiki 结构 ----------
    try:
        plan_xml = plan_wiki_structure(project, file_tree, readme, src, source_code_stone, java_callgraph_stone, language)
        log.info("[build_wiki] plan_xml=\n%.10000s...", plan_xml)
    except Exception as e:
        log.exception("[build_wiki] plan_wiki_structure failed")
        raise RuntimeError("generate wiki structure failed") from e

    # ---------- 4. 解析 XML ----------
    try:
        root = ET.fromstring(plan_xml)
    except ET.ParseError as e:
        log.error("[build_wiki] XML parse error – %.200s", plan_xml)
        raise RuntimeError("invalid wiki xml") from e

    pages = []
    for page in root.findall("page"):
        pid   = page.get("id")
        title = page.findtext("title")
        description = page.findtext("description")
        files = page.findtext("relevant_files")
        if not (pid and title and files):
            log.warning("[build_wiki] skip incomplete <page>")
            continue
        pages.append((pid, description, title, [f.strip() for f in files.split(",") if f.strip()]))

    if not pages:
        log.warning("[build_wiki] no valid page found")
        return

    log.info("[build_wiki] parsed %s pages", len(pages))

    # ---------- 5. 逐页生成 markdown ----------
    module_docs: Dict[str, str] = {}
    for pid, title, description, file_paths in pages:
        log.info("[build_wiki] ---- generate page | id=%s title=%s files=%s", pid, title, file_paths)
        try:
            md = write_page(title, description, file_paths, src, source_code_stone, java_callgraph_stone, language)
            module_docs[pid] = md
            log.info("[build_wiki] page done | id=%s len=%s", pid, len(md))
        except Exception as e:
            log.exception("[build_wiki] write_page failed | id=%s", pid)
            raise RuntimeError(f"generate page {pid} failed") from e

        # 落盘
        md_path = out / "modules" / f"{pid}.md"
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(f"# {title}\n\n{md}", encoding="utf-8")

    # ---------- 6. 项目总览 PROJECT.md ----------
    project_md = out / "PROJECT.md"
    if project_md.exists():
        readme = project_md.read_text(encoding="utf-8")
        log.info("[build_wiki] use existing PROJECT.md")
    else:
        summaries = []
        for (pid, desc, title, file_list), doc in zip(pages, module_docs.values()):
            lines = doc.splitlines()[:20]  # 前 20 行
            preview = os.linesep.join(lines)  # 拼回字符串
            summaries.append(f"- **{title}**（{desc}）：\n{preview}")

        wiki_lines = "\n".join(summaries)
        log.info("[build_wiki] generating PROJECT.md ...")
        try:
            if language == "en":
                readme = write_page_from_dir("Project Overview", wiki_lines, out / "modules", src, source_code_stone,
                                             java_callgraph_stone, language)
            else:
                readme = write_page_from_dir("项目总览", wiki_lines, out / "modules", src, source_code_stone,
                                             java_callgraph_stone, language)
            project_md.write_text(readme, encoding="utf-8")
            log.info("[build_wiki] PROJECT.md done | len=%s", len(readme))
        except Exception as e:
            log.exception("[build_wiki] generate PROJECT.md failed")
            raise

    # ---------- 7. 索引 & 内存缓存 ----------
    write_markdown(str(out), module_docs, {p[0]: {"title": p[1]} for p in pages})
    project_readmes[project]  = readme
    project_modules[project]  = list(module_docs.keys())
    log.info("[build_wiki] <<< all finished – project=%s | modules=%s", project, len(module_docs))


# ==============================================================================
# FastAPI 初始化
# ==============================================================================
app = FastAPI(title="EWiki-mini-Server")

# -------------- CORS --------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================================================================
# API 定义
# ==============================================================================
@app.on_event("startup")
async def startup_event():
    load_existing_projects()
# ~~~~~~~~~~~~~~ 项目级 ~~~~~~~~~~~~~~
class ImportReq(BaseModel):
    path: str
    language: str = "zh"  # 默认中文

@app.get("/api/projects")
def list_projects():
    """返回 output 下所有已生成 Wiki 的项目名"""
    return [p.name for p in OUTPUT_BASE.iterdir() if p.is_dir()]


from fastapi import WebSocket, WebSocketDisconnect
import json
import asyncio


# 添加进度状态管理
class ProgressManager:
    def __init__(self):
        self.connections = {}

    async def connect(self, websocket: WebSocket, project: str):
        await websocket.accept()
        if project not in self.connections:
            self.connections[project] = []
        self.connections[project].append(websocket)

    def disconnect(self, websocket: WebSocket, project: str):
        if project in self.connections:
            self.connections[project].remove(websocket)
            if not self.connections[project]:
                del self.connections[project]

    async def send_progress(self, project: str, progress: dict):
        if project in self.connections:
            for connection in self.connections[project]:
                try:
                    await connection.send_json(progress)
                except:
                    pass


progress_manager = ProgressManager()

from fastapi import WebSocket, WebSocketDisconnect
import json
import asyncio
from typing import Dict, List


class ConnectionManager:
    def __init__(self):
        # 存储项目到WebSocket连接的映射
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, project: str):
        await websocket.accept()
        if project not in self.active_connections:
            self.active_connections[project] = []
        self.active_connections[project].append(websocket)

    def disconnect(self, websocket: WebSocket, project: str):
        if project in self.active_connections:
            self.active_connections[project].remove(websocket)
            if not self.active_connections[project]:
                del self.active_connections[project]

    async def send_progress(self, project: str, message: dict):
        if project in self.active_connections:
            disconnected = []
            for connection in self.active_connections[project]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    print(f"发送进度失败: {e}")
                    disconnected.append(connection)

            # 移除断开的连接
            for connection in disconnected:
                self.disconnect(connection, project)


manager = ConnectionManager()


# WebSocket 路由
@app.websocket("/ws/progress/{project}")
async def websocket_endpoint(websocket: WebSocket, project: str):
    await manager.connect(websocket, project)
    try:
        while True:
            # 保持连接活跃
            data = await websocket.receive_text()
            # 可以处理客户端发送的消息（如果需要）
    except WebSocketDisconnect:
        manager.disconnect(websocket, project)
        print(f"WebSocket 断开连接: {project}")


# 修改 build_wiki_with_progress 函数
async def build_wiki_with_progress(project: str, language: str = "zh") -> None:
    """
    带进度更新的wiki构建函数
    """
    import xml.etree.ElementTree as ET
    from src.utils import write_markdown

    try:
        # 发送开始进度
        await manager.send_progress(project, {
            "stage": "started",
            "progress": 5,
            "message": "开始构建Wiki..."
        })
        await asyncio.sleep(0.1)  # 确保消息发送

        # ---------- 0. 路径 ----------
        src = REPOS_DIR / project
        out = OUTPUT_BASE / project
        data_out = out / "data"
        source_code_stone = data_out / "source_code_stone"
        java_callgraph_stone = data_out / "java_callgraph_stone"
        out.mkdir(parents=True, exist_ok=True)
        data_out.mkdir(parents=True, exist_ok=True)
        java_callgraph_stone.mkdir(parents=True, exist_ok=True)
        source_code_stone.mkdir(parents=True, exist_ok=True)

        await manager.send_progress(project, {
            "stage": "preparing",
            "progress": 10,
            "message": "初始化目录结构..."
        })
        await asyncio.sleep(0.1)

        # ---------- 1. 文件树 & README ----------
        file_tree = "\n".join(
            str(p.relative_to(src))
            for p in sorted(src.rglob("*"))
            if p.is_file() and not str(p.name).startswith(".")
        )
        readme_file = src / "README.md"
        readme = readme_file.read_text(encoding="utf-8") if readme_file.exists() else "No README"

        await manager.send_progress(project, {
            "stage": "analyzing",
            "progress": 20,
            "message": "分析项目文件结构..."
        })
        await asyncio.sleep(0.1)

        # ---------- 2. 生成 wiki 结构 ----------
        try:
            await manager.send_progress(project, {
                "stage": "planning",
                "progress": 30,
                "message": "规划Wiki结构..."
            })
            await asyncio.sleep(0.1)

            plan_xml = plan_wiki_structure(project, file_tree, readme, src, source_code_stone, java_callgraph_stone,
                                           language)

            await manager.send_progress(project, {
                "stage": "parsing",
                "progress": 40,
                "message": "解析Wiki结构..."
            })
            await asyncio.sleep(0.1)
        except Exception as e:
            log.exception("[build_wiki] plan_wiki_structure failed")
            await manager.send_progress(project, {
                "stage": "error",
                "progress": 0,
                "message": f"生成Wiki结构失败: {str(e)}"
            })
            raise RuntimeError("generate wiki structure failed") from e

        # ---------- 3. 解析 XML ----------
        try:
            root = ET.fromstring(plan_xml)
        except ET.ParseError as e:
            log.error("[build_wiki] XML parse error – %.200s", plan_xml)
            await manager.send_progress(project, {
                "stage": "error",
                "progress": 0,
                "message": f"解析Wiki结构失败: {str(e)}"
            })
            raise RuntimeError("invalid wiki xml") from e

        pages = []
        for page in root.findall("page"):
            pid = page.get("id")
            title = page.findtext("title")
            description = page.findtext("description")
            files = page.findtext("relevant_files")
            if not (pid and title and files):
                log.warning("[build_wiki] skip incomplete <page>")
                continue
            pages.append((pid, description, title, [f.strip() for f in files.split(",") if f.strip()]))

        if not pages:
            log.warning("[build_wiki] no valid page found")
            await manager.send_progress(project, {
                "stage": "error",
                "progress": 0,
                "message": "未找到有效的页面配置"
            })
            return

        await manager.send_progress(project, {
            "stage": "generating_pages",
            "progress": 50,
            "message": f"开始生成 {len(pages)} 个页面...",
            "total_pages": len(pages)
        })
        await asyncio.sleep(0.1)

        # ---------- 4. 逐页生成 markdown ----------
        module_docs: Dict[str, str] = {}
        for i, (pid, title, description, file_paths) in enumerate(pages):
            current_progress = 50 + int((i / len(pages)) * 40)
            await manager.send_progress(project, {
                "stage": "generating_page",
                "progress": current_progress,
                "message": f"正在生成页面: {title}",
                "current_page": i + 1,
                "total_pages": len(pages)
            })
            await asyncio.sleep(0.1)

            log.info("[build_wiki] ---- generate page | id=%s title=%s files=%s", pid, title, file_paths)
            try:
                md = write_page(title, description, file_paths, src, source_code_stone, java_callgraph_stone, language)
                module_docs[pid] = md
                log.info("[build_wiki] page done | id=%s len=%s", pid, len(md))
            except Exception as e:
                log.exception("[build_wiki] write_page failed | id=%s", pid)
                await manager.send_progress(project, {
                    "stage": "error",
                    "progress": 0,
                    "message": f"生成页面 {title} 失败: {str(e)}"
                })
                raise RuntimeError(f"generate page {pid} failed") from e

            # 落盘
            md_path = out / "modules" / f"{pid}.md"
            md_path.parent.mkdir(parents=True, exist_ok=True)
            md_path.write_text(f"# {title}\n\n{md}", encoding="utf-8")

        await manager.send_progress(project, {
            "stage": "finalizing",
            "progress": 90,
            "message": "生成项目总览..."
        })
        await asyncio.sleep(0.1)

        # ---------- 5. 项目总览 PROJECT.md ----------
        project_md = out / "PROJECT.md"
        if project_md.exists():
            readme = project_md.read_text(encoding="utf-8")
            log.info("[build_wiki] use existing PROJECT.md")
        else:
            summaries = []
            for (pid, desc, title, file_list), doc in zip(pages, module_docs.values()):
                lines = doc.splitlines()[:20]  # 前 20 行
                preview = os.linesep.join(lines)  # 拼回字符串
                summaries.append(f"- **{title}**（{desc}）：\n{preview}")

            wiki_lines = "\n".join(summaries)
            log.info("[build_wiki] generating PROJECT.md ...")
            try:
                if language == "en":
                    readme = write_page_from_dir("Project Overview", wiki_lines, out / "modules", src,
                                                 source_code_stone,
                                                 java_callgraph_stone, language)
                else:
                    readme = write_page_from_dir("项目总览", wiki_lines, out / "modules", src, source_code_stone,
                                                 java_callgraph_stone, language)
                project_md.write_text(readme, encoding="utf-8")
                log.info("[build_wiki] PROJECT.md done | len=%s", len(readme))
            except Exception as e:
                log.exception("[build_wiki] generate PROJECT.md failed")
                await manager.send_progress(project, {
                    "stage": "error",
                    "progress": 0,
                    "message": f"生成项目总览失败: {str(e)}"
                })
                raise

        # ---------- 6. 索引 & 内存缓存 ----------
        write_markdown(str(out), module_docs, {p[0]: {"title": p[1]} for p in pages})
        project_readmes[project] = readme
        project_modules[project] = list(module_docs.keys())

        await manager.send_progress(project, {
            "stage": "completed",
            "progress": 100,
            "message": "Wiki生成完成！"
        })
        await asyncio.sleep(0.1)

        log.info("[build_wiki] <<< all finished – project=%s | modules=%s", project, len(module_docs))

    except Exception as e:
        log.exception(f"构建Wiki失败: {e}")
        await manager.send_progress(project, {
            "stage": "error",
            "progress": 0,
            "message": f"构建失败: {str(e)}"
        })
        raise


@app.post("/api/import")
async def import_and_build(req: ImportReq):
    try:
        name = import_project(req.path)
        if (OUTPUT_BASE / name / "PROJECT.md").exists():
            return {"project": name, "message": "wiki already exists"}

        # 使用带进度的构建函数
        await build_wiki_with_progress(name, req.language)
        return {"project": name}
    except Exception as e:
        log.exception("import failed")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/{project}/knowledge/upload")
async def upload_knowledge_file(
        project: str,
        file: UploadFile = File(...),
        description: str = ""
):
    """上传知识库文件"""
    try:
        if project not in project_readmes:
            raise HTTPException(status_code=404, detail="Project not found")

        # 创建知识库目录
        kb_dir = OUTPUT_BASE / project / "knowledge_base"
        kb_dir.mkdir(exist_ok=True)

        # 保存文件
        file_path = kb_dir / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 初始化项目知识库列表
        if project not in project_knowledge_bases:
            project_knowledge_bases[project] = []

        # 记录文件信息
        file_info = {
            "filename": file.filename,
            "description": description,
            "upload_time": datetime.now().isoformat(),
            "size": file_path.stat().st_size
        }
        project_knowledge_bases[project].append(file.filename)

        # 构建整个知识库目录的向量索引
        await build_knowledge_index(project, str(kb_dir))  # 传入目录路径而不是文件路径

        return {
            "filename": file.filename,
            "message": "文件上传成功并已更新知识库索引",
            "description": description
        }

    except Exception as e:
        log.exception("知识库文件上传失败")
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")

@app.get("/api/{project}/knowledge/files")
def list_knowledge_files(project: str):
    """列出项目的知识库文件"""
    if project not in project_readmes:
        raise HTTPException(status_code=404, detail="Project not found")

    kb_dir = OUTPUT_BASE / project / "knowledge_base"
    if not kb_dir.exists():
        return []

    files = []
    for file_path in kb_dir.iterdir():
        if file_path.is_file():
            files.append({
                "filename": file_path.name,
                "size": file_path.stat().st_size,
                "upload_time": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
            })

    return files


@app.delete("/api/{project}/knowledge/files/{filename}")
async def delete_knowledge_file(project: str, filename: str):
    """删除知识库文件"""
    try:
        if project not in project_readmes:
            raise HTTPException(status_code=404, detail="Project not found")

        kb_dir = OUTPUT_BASE / project / "knowledge_base"
        file_path = kb_dir / filename

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")

        # 删除文件
        file_path.unlink()

        # 从内存缓存中移除
        if project in project_knowledge_bases and filename in project_knowledge_bases[project]:
            project_knowledge_bases[project].remove(filename)

        # 检查知识库目录中是否还有其他文件
        remaining_files = [f for f in kb_dir.iterdir()
                           if f.is_file() and f.name not in ['faiss.index', 'meta.json']]

        if remaining_files:
            # 如果还有文件，重新构建整个知识库的索引
            await build_knowledge_index(project, str(kb_dir))
            return {"message": "文件删除成功，知识库索引已更新"}
        else:
            # 如果没有文件了，删除索引文件
            index_file = kb_dir / "faiss.index"
            meta_file = kb_dir / "meta.json"
            if index_file.exists():
                index_file.unlink()
            if meta_file.exists():
                meta_file.unlink()
            return {"message": "文件删除成功，知识库已清空"}

    except Exception as e:
        log.exception("知识库文件删除失败")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


async def build_knowledge_index(project: str, kb_dir_path: str):
    """为整个知识库目录构建向量索引"""
    try:
        from src.embedding import build_vec_index
        kb_dir = OUTPUT_BASE / project / "knowledge_base"

        # 删除旧的索引文件（如果存在）
        index_file = kb_dir / "faiss.index"
        meta_file = kb_dir / "meta.json"
        if index_file.exists():
            index_file.unlink()
        if meta_file.exists():
            meta_file.unlink()

        # 使用现有的 build_vec_index 方法
        # 它会自动在指定路径创建 faiss.index 和 meta.json
        build_vec_index(
            project_root=kb_dir_path,  # 知识库目录作为项目根目录
            out_path=str(kb_dir)  # 输出到知识库目录
        )

        log.info(f"[build_knowledge_index] 知识库索引构建成功: {kb_dir_path}")

    except Exception as e:
        log.error(f"[build_knowledge_index] 索引构建失败: {e}")
        raise


def query_knowledge_base(project: str, query: str, topk: int = 3) -> str:
    """查询知识库 - 使用统一的索引文件"""
    try:
        kb_dir = OUTPUT_BASE / project / "knowledge_base"
        if not kb_dir.exists():
            return ""

        # 检查索引文件是否存在
        index_file = kb_dir / "faiss.index"
        meta_file = kb_dir / "meta.json"

        if not (index_file.exists() and meta_file.exists()):
            log.info(f"[query_knowledge_base] 知识库索引文件不存在")
            return ""

        try:
            from src.embedding import search
            # 临时设置索引文件路径
            import src.embedding as emb
            emb.INDEX_FILE = str(index_file)
            emb.META_FILE = str(meta_file)

            results = search(query, topk)

            if not results:
                return ""

            # 构建知识库上下文
            context = "## 相关知识库内容\n\n"
            for i, result in enumerate(results, 1):
                context += f"### 片段 {i} (来自 {result['path']}, 相似度: {result['score']:.3f})\n"
                context += f"```\n{result['text']}\n```\n\n"

            return context

        except Exception as e:
            log.warning(f"[query_knowledge_base] 知识库查询失败: {e}")
            return ""

    except Exception as e:
        log.error(f"[query_knowledge_base] 查询失败: {e}")
        return ""

# ~~~~~~~~~~~~~~ 单个项目文档 ~~~~~~~~~~~~~~
@app.get("/api/{project}/project")
def get_project(project: str):
    if project not in project_readmes:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"file": "PROJECT.md", "content": project_readmes[project]}


@app.get("/api/{project}/modules")
def list_modules(project: str):
    if project not in project_modules:
        raise HTTPException(status_code=404, detail="Project not found")
    return project_modules[project]


@app.get("/api/{project}/modules/{name}")
def get_module(project: str, name: str):
    md_path = OUTPUT_BASE / project / "modules" / f"{name.replace('.', '_')}.md"
    if not md_path.exists():
        raise HTTPException(status_code=404, detail="Module not found")
    return {"file": f"{name}.md", "content": md_path.read_text(encoding="utf-8")}


# ~~~~~~~~~~~~~~ 聊天接口 ~~~~~~~~~~~~~~
class ChatRequest(BaseModel):
    question: str
    topk: int = 5
    history: List[Dict[str, str]] = []


def build_chat_prompt(question: str, history: List[Dict[str, str]], contexts: List[str]) -> str:
    """构建专业的软件开发助手提示词"""

    system_prompt = """你是一位专业的软件开发助手和软件架构师，专门帮助开发者理解和分析代码项目。

你的任务是基于提供的代码上下文，准确、全面地回答技术问题。

**核心原则：**
1. **准确性优先**：所有技术信息必须基于提供的代码上下文，不推断、不发明
2. **深度分析**：提供架构层面的理解和分析，而不仅仅是表面描述
3. **可视化表达**：尽可能使用图表、表格等可视化方式解释复杂概念
4. **源码引用**：对于关键信息，必须引用具体的源码文件和位置

**回答结构要求：**
1. **问题理解**：首先确认对问题的理解，确保回答方向正确
2. **架构概述**：从系统架构角度提供高层次概述
3. **详细分析**：深入分析具体实现，包括关键类、函数、数据流等
4. **可视化辅助**：使用Mermaid图表展示架构、流程、关系等
5. **源码证据**：关键结论必须提供具体的源码引用
6. **实践建议**：基于代码分析提供开发或优化建议

**图表规范：**
- 流程图：使用 `graph TD` (从上到下)
- 序列图：使用 `sequenceDiagram`，正确定义参与者和消息类型
- 类图：使用 `classDiagram` 展示类关系
- 表格：使用Markdown表格总结配置、API、数据结构等

**引用格式：**
使用格式：`[文件名:起始行-结束行]` 或 `[文件名:行号]`
"""

    # 构建上下文部分
    if contexts:
        context_section = "## 可用的代码上下文\n\n" + "\n\n".join([
            f"### 上下文片段 {i + 1}\n{ctx}"
            for i, ctx in enumerate(contexts)
        ])
    else:
        context_section = "## 注意：当前没有可用的代码上下文\n请基于通用知识回答，并明确说明信息来源的局限性。"

    # 构建对话历史
    conversation_history = ""
    if history:
        conversation_parts = []
        for turn in history[-6:]:  # 保留最近6轮对话
            role = "用户" if turn.get("role") == "user" else "助手"
            text = turn.get("text", "")
            conversation_parts.append(f"**{role}**：{text}")

        conversation_history = "## 对话历史\n\n" + "\n\n".join(conversation_parts) + "\n\n"

    # 当前问题
    current_question = f"## 当前问题\n\n**用户**：{question}"

    # 最终提示词
    prompt_parts = [
        system_prompt,
        "\n" + "=" * 50 + "\n",
        context_section,
        "\n" + "=" * 50 + "\n",
        conversation_history,
        current_question,
        "\n" + "=" * 50 + "\n",
        "## 助手回答\n\n请基于以上信息提供专业、准确的技术分析："
    ]

    return "\n".join(prompt_parts)


# 修改现有的聊天接口
@app.post("/api/{project}/chat")
async def chat(project: str, req: ChatRequest):
    """基于项目代码和知识库的智能问答 - 专业版本"""
    try:
        # 检查项目是否存在
        if project not in project_readmes:
            raise HTTPException(status_code=404, detail="Project not found")

        # 获取项目路径
        project_path = OUTPUT_BASE / project
        repo_path = REPOS_DIR / project

        if not repo_path.exists():
            raise HTTPException(status_code=404, detail="Source repository not found")

        # 1. 使用RAG检索相关代码片段
        search_query = req.question
        if req.history:
            # 结合最近的历史来改进检索
            recent_context = " ".join([
                turn.get("text", "")
                for turn in req.history[-2:]
                if turn.get("role") == "user"
            ])
            if recent_context:
                search_query = f"{recent_context} {req.question}"

        all_contexts = []

        # 2. 查询知识库
        knowledge_context = query_knowledge_base(project, search_query, topk=2)
        if knowledge_context:
            all_contexts.append(knowledge_context)
            log.info(f"[chat] Retrieved knowledge context, length: {len(knowledge_context)}")

        # 3. 检索主要代码（原有逻辑）
        source_code_stone = project_path / "data" / "source_code_stone"
        java_callgraph_stone = project_path / "data" / "java_callgraph_stone"

        source_code_stone.mkdir(parents=True, exist_ok=True)
        java_callgraph_stone.mkdir(parents=True, exist_ok=True)

        # 检索主要代码
        try:
            from src.embedding import query_code
            code_contexts = query_code(
                query=search_query,
                project_root=str(repo_path),
                topk=req.topk,
                out_path=str(source_code_stone)
            )
            log.info(f"[chat] Retrieved code contexts, length: {len(code_contexts)}")

            if code_contexts and "代码检索暂时不可用" not in code_contexts and "未找到相关的代码片段" not in code_contexts:
                all_contexts.append(f"**语义检索的代码片段**：\n{code_contexts}")
            else:
                log.warning(f"[chat] Code retrieval returned limited results: {code_contexts}")

        except Exception as e:
            log.error(f"[chat] Code retrieval failed: {e}")

        # 检索Java调用图信息
        try:
            from src.rag import get_java_callgraph
            java_context = get_java_callgraph(
                search_query,
                str(repo_path),
                str(java_callgraph_stone)
            )
            if java_context and java_context.strip():
                all_contexts.append(f"**调用关系分析**：\n{java_context}")
                log.info(f"[chat] Retrieved Java callgraph, length: {len(java_context)}")
        except Exception as e:
            log.warning(f"[chat] Java callgraph retrieval failed: {e}")

        # 如果没有检索到任何上下文，添加项目基本信息
        if not all_contexts:
            project_info = f"**项目基本信息**：\n- 项目名称：{project}\n- 项目描述：{project_readmes.get(project, '无详细描述')[:500]}..."
            all_contexts.append(project_info)
            log.warning(f"[chat] No contexts retrieved, using basic project info")

        # 4. 构建专业提示词
        prompt = build_chat_prompt(
            question=req.question,
            history=req.history,
            contexts=all_contexts
        )

        log.info(f"[chat] Final prompt length: {len(prompt)}")

        # 5. 调用LLM生成专业回答
        from src.llm import generate
        answer = generate(
            prompt=prompt,
            temperature=0.1,
            max_tokens=4096
        )

        # 6. 返回结果
        return {
            "answer": answer,
            "sources": all_contexts,
            "project": project,
            "context_count": len(all_contexts),
            "has_knowledge": bool(knowledge_context)
        }

    except HTTPException:
        raise
    except Exception as e:
        log.exception(f"Chat failed for project {project}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


# 在 ImportReq 模型后添加
import zipfile
import tarfile
import py7zr
import os
from pathlib import Path


class FileUploadReq(BaseModel):
    filename: str


@app.post("/api/upload")
async def upload_and_build(file: UploadFile = File(...), language: str = "zh"):
    """上传压缩文件并生成 Wiki（带进度）"""
    try:
        # 检查文件类型
        allowed_extensions = {'.zip', '.rar', '.7z', '.tar', '.gz'}
        file_extension = Path(file.filename).suffix.lower()

        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件格式。支持格式: {', '.join(allowed_extensions)}"
            )

        # 使用文件名作为项目名
        project_name = Path(file.filename).stem

        # 创建项目目录
        project_dir = REPOS_DIR / project_name
        project_dir.mkdir(parents=True, exist_ok=True)

        # 如果项目已存在，直接使用现有目录
        if any(project_dir.iterdir()):
            log.info("project already exists, rebuilding wiki: %s", project_name)
        else:
            # 保存上传的文件
            uploaded_file_path = project_dir / file.filename
            with open(uploaded_file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)

            # 解压文件
            extract_success = False
            try:
                if file_extension == '.zip':
                    extract_success = extract_zip(uploaded_file_path, project_dir)
                elif file_extension == '.rar':
                    extract_success = extract_rar(uploaded_file_path, project_dir)
                elif file_extension in ['.7z']:
                    extract_success = extract_7z(uploaded_file_path, project_dir)
                elif file_extension in ['.tar', '.gz']:
                    extract_success = extract_tar(uploaded_file_path, project_dir)

                if not extract_success:
                    raise HTTPException(status_code=400, detail="文件解压失败")

            except Exception as extract_error:
                # 清理失败的文件
                import shutil
                shutil.rmtree(project_dir, ignore_errors=True)
                raise HTTPException(status_code=400, detail=f"解压失败: {str(extract_error)}")

            # 删除原始压缩文件
            uploaded_file_path.unlink()

        if (OUTPUT_BASE / project_name / "PROJECT.md").exists():
            return {"project": project_name, "message": "wiki already exists"}

        # 使用带进度的构建函数
        await build_wiki_with_progress(project_name, language)

        return {"project": project_name}
    except HTTPException:
        raise
    except Exception as e:
        log.exception("file upload failed")
        raise HTTPException(status_code=400, detail=str(e))


import shutil
from pathlib import Path


@app.delete("/api/projects/{project_name}")
async def delete_project(project_name: str):
    """删除项目及其 Wiki"""
    try:
        # 安全检查：防止路径遍历攻击
        if ".." in project_name or "/" in project_name:
            raise HTTPException(status_code=400, detail="无效的项目名称")

        project_dir = REPOS_DIR / project_name
        project_out_dir = OUTPUT_BASE / project_name
        # 检查项目是否存在
        if not project_dir.exists():
            raise HTTPException(status_code=404, detail="项目不存在")

        # 删除项目目录
        shutil.rmtree(project_dir)

        shutil.rmtree(project_out_dir)

        return {"message": f"项目 {project_name} 删除成功"}

    except HTTPException:
        raise
    except Exception as e:
        log.exception(f"删除项目失败: {project_name}")
        raise HTTPException(status_code=500, detail=f"删除项目失败: {str(e)}")

def extract_zip(zip_path: Path, extract_to: Path) -> bool:
    """解压 ZIP 文件"""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        return True
    except Exception as e:
        log.error(f"ZIP extraction failed: {e}")
        return False


def extract_rar(rar_path: Path, extract_to: Path) -> bool:
    """解压 RAR 文件"""
    try:
        # 需要安装 rarfile: pip install rarfile
        import rarfile
        with rarfile.RarFile(rar_path) as rar_ref:
            rar_ref.extractall(extract_to)
        return True
    except ImportError:
        raise HTTPException(status_code=400, detail="RAR 解压支持未安装，请安装 rarfile")
    except Exception as e:
        log.error(f"RAR extraction failed: {e}")
        return False


def extract_7z(sevenz_path: Path, extract_to: Path) -> bool:
    """解压 7z 文件"""
    try:
        # 需要安装 py7zr: pip install py7zr
        with py7zr.SevenZipFile(sevenz_path, mode='r') as sevenz_ref:
            sevenz_ref.extractall(extract_to)
        return True
    except ImportError:
        raise HTTPException(status_code=400, detail="7z 解压支持未安装，请安装 py7zr")
    except Exception as e:
        log.error(f"7z extraction failed: {e}")
        return False


def extract_tar(tar_path: Path, extract_to: Path) -> bool:
    """解压 tar/tar.gz 文件"""
    try:
        if tar_path.suffix == '.gz':
            # tar.gz 文件
            with tarfile.open(tar_path, 'r:gz') as tar_ref:
                tar_ref.extractall(extract_to)
        else:
            # 普通 tar 文件
            with tarfile.open(tar_path, 'r') as tar_ref:
                tar_ref.extractall(extract_to)
        return True
    except Exception as e:
        log.error(f"TAR extraction failed: {e}")
        return False


# ~~~~~~~~~~~~~~ 静态文件（可选） ~~~~~~~~~~~~~~
app.mount("/static", StaticFiles(directory=str(OUTPUT_BASE), html=False), name="static")

# ==============================================================================
# 启动
# ==============================================================================
if __name__ == "__main__":

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
