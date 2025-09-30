from pathlib import Path
import sys
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))
from typing import Dict, List
from .embedding import query_code
from .prompts import PLAN_WIKI_PROMPT,WRITE_PAGE_PROMPT
from .llm import generate
# -----------------------------
# RAG pipeline - NO CHANGES HERE
# -----------------------------
import logging
from pathlib import Path
from typing import List, Iterable
log = logging.getLogger("EWikiRAG")
from pathlib import Path
from typing import List
MAX_HEAD_LINES = 300          # 只取前 200 行
MAX_FILE_BYTES = 80 * 1024    # 单文件 50 KB 上限
MAX_TOTAL_BYTES = 400 * 1024  # 整页 200 KB 上限

def head_text(path: Path, max_lines: int, max_bytes: int) -> str:
    """返回前 max_lines 行且不超过 max_bytes 的文本"""
    txt = path.read_text(encoding='utf-8', errors='ignore')[:max_bytes]
    return '\n'.join(txt.splitlines()[:max_lines])

def plan_wiki_structure(repo: str,file_tree: str, readme: str, repo_root: Path,source_code_stone: Path,java_callgraph_stone: Path) -> str:
    codes = query_code(query=file_tree+readme, project_root=str(repo_root), out_path=str(source_code_stone))
    java_callgraph=get_java_callgraph(file_tree+readme,str(repo_root),str(java_callgraph_stone))
    codes = codes + java_callgraph
    """Step-1：让 LLM 决定 wiki 结构"""
    prompt = PLAN_WIKI_PROMPT.format(repo=repo,file_tree=file_tree, readme=readme,code_contents=codes)
    log.info("[plan_wiki_structure] prompt=\n%.10000s...", prompt)
    return generate(prompt, temperature=0.1, max_tokens=20480)

def _iter_docs_under(root: Path) -> Iterable[Path]:
    """递归迭代常见文档文件"""
    CODE_EXT = {".py", ".js", ".ts", ".java", ".cpp", ".c", ".h", ".go", ".rs",
                ".jsx", ".tsx", ".html", ".css", ".php", ".swift", ".cs",
                ".md", ".txt", ".rst", ".json", ".yaml", ".yml"}
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in CODE_EXT:
            yield p

# ---------- 新增入口 ----------
def write_page_from_dir(title: str,
                        description: str,
                        file_dir: str,
                        repo_root: Path,
                        source_code_stone: Path,
                        java_callgraph_stone: Path) -> str:
    """
    从 file_dir 中自动收集所有文档，按 head_text 限制后拼接生成 Wiki 页
    """
    # 1. 语义代码块（与 write_page 完全一致）
    codes = query_code(query=description, project_root=str(repo_root), out_path=str(source_code_stone))
    codes += get_java_callgraph(description, str(repo_root), str(java_callgraph_stone))

    # 2. 遍历目录拼接带限制的文件内容
    chunks, total = [], 0
    for fp in _iter_docs_under(Path(file_dir)):
        content = head_text(fp, MAX_HEAD_LINES, MAX_FILE_BYTES)

        relative_path = fp.relative_to(Path(file_dir))
        seg = f"{relative_path}\n{'-' * 40}\n{content}"

        if total + len(seg.encode('utf-8')) > MAX_TOTAL_BYTES:
            seg = f"{relative_path}\n{'-' * 40}\n... (truncated)"
        chunks.append(seg)
        total += len(seg.encode('utf-8'))

    file_contents = "\n\n".join(chunks)
    prompt = WRITE_PAGE_PROMPT.format(title=title,
                                      file_contents=file_contents,
                                      code_contents=codes)
    log.info("[write_page_from_dir] prompt=%.10000s...", prompt)
    return generate(prompt, temperature=0.1, max_tokens=20480)

def write_page(title: str,
               description: str,
               file_paths: List[str],
               repo_root: Path,
               source_code_stone: Path,
               java_callgraph_stone: Path) -> str:

    # ---- 1. 语义代码块 ----
    codes = query_code(query=description, project_root=str(repo_root), out_path=str(source_code_stone))
    codes += get_java_callgraph(description, str(repo_root), str(java_callgraph_stone))

    # ---- 2. 带限制的文件内容 ----
    chunks, total = [], 0
    for fp in file_paths:
        full = repo_root / fp
        if not full.exists():
            continue
        content = head_text(full, MAX_HEAD_LINES, MAX_FILE_BYTES)
        seg = f"{fp}\n{'-'*40}\n{content}"
        if total + len(seg.encode('utf-8')) > MAX_TOTAL_BYTES:
            seg = f"{fp}\n{'-'*40}\n... (truncated)"
        chunks.append(seg)
        total += len(seg.encode('utf-8'))

    file_contents = "\n\n".join(chunks)
    prompt = WRITE_PAGE_PROMPT.format(title=title,
                                      file_contents=file_contents,
                                      code_contents=codes)
    log.info("[write_page] prompt=%.10000s...", prompt)
    return generate(prompt, temperature=0.1, max_tokens=20480)

def get_java_callgraph(query:str,repo_root: str,out: str):
    from tools.project_parser import save_java_callgraph,get_java_callgraph_from_faiss_store
    save_java_callgraph(repo_root,out)
    get_java_callgraph_from_faiss_store(query,out)
    callgraph = query_code(query=query, project_root=repo_root, out_path=out)
    return callgraph
