
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码语义检索 + LLM 问答（异步优化版）
author: kimi
"""
import os
import re
import json
import argparse
import hashlib
import asyncio
import aiohttp
import numpy as np
import faiss
from tqdm import tqdm
from pathlib import Path
import xml.etree.ElementTree as ET
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor

from .config import load_config
import nest_asyncio
nest_asyncio.apply()
cfg = load_config()

# ---------- 配置参数 ----------
API_KEY = cfg["API_KEY"]
EMBED_NAME = cfg["EMBED_NAME"]
DASHSCOPE_EMBED_URL = cfg["EMBED_URL"]
LLM_NAME = cfg["LLM_NAME"]
DASHSCOPE_GENERATION_URL = cfg["LLM_URL"]
INDEX_FILE = cfg["INDEX_FILE"]
META_FILE = cfg["META_FILE"]
MAX_LINES = int(cfg["MAX_LINES"])
BATCH_SIZE = int(cfg["BATCH_SIZE"])
DEFAULT_TOPK = int(cfg["TOP_K"])

# 异步并发配置
MAX_CONCURRENT = int(cfg.get("MAX_CONCURRENT", "5"))  # 最大并发数
EMBED_TIMEOUT = int(cfg.get("EMBED_TIMEOUT", "30"))  # 嵌入超时时间

CODE_EXT = [".py", ".js", ".ts", ".java", ".cpp", ".c", ".h", ".hpp", ".go", ".rs",
            ".jsx", ".tsx", ".html", ".css", ".php", ".swift", ".cs"]
DOC_EXT = [".md", ".txt", ".rst", ".json", ".yaml", ".yml", ".xml", ".csv"]
KNOWLEDGE_EXT = [".pdf", ".doc", ".docx", ".xls", ".xlsx"] + DOC_EXT + CODE_EXT


def md5txt(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def list_files(root: str):
    root_path = Path(root)
    if root_path.is_file():
        yield str(root_path)
    else:
        root = os.path.abspath(root)
        for dirpath, _, filenames in os.walk(root):
            for f in filenames:
                ext = os.path.splitext(f)[1].lower()
                if ext in KNOWLEDGE_EXT:
                    yield os.path.join(dirpath, f)


def read_chunks(path: str, max_lines=MAX_LINES):
    with open(path, encoding="utf-8", errors="ignore") as g:
        lines = g.readlines()
    chunks, buf, start = [], [], 1
    for idx, line in enumerate(lines, 1):
        buf.append(line)
        if re.match(r"^\s*$", line) or re.match(r"^\s*[})\]]\s*$", line):
            if buf:
                chunks.append((start, "".join(buf)))
                buf, start = [], idx
        if len(buf) >= max_lines:
            chunks.append((start, "".join(buf)))
            buf, start = [], idx
    if buf:
        chunks.append((start, "".join(buf)))
    return chunks


def embed_batch(texts: list[str]) -> np.ndarray:
    """同步嵌入批处理（用于查询时的单批次处理）"""
    processed_texts = []
    for text in texts:
        if len(text) > 8192:
            text = text[:8192]
        processed_texts.append(text)

    client = OpenAI(
        api_key=API_KEY,
        base_url=DASHSCOPE_EMBED_URL
    )
    resp = client.embeddings.create(
        model=EMBED_NAME,
        input=processed_texts,
        dimensions=768,
        encoding_format="float"
    )
    vecs = [item.embedding for item in resp.data]
    return np.array(vecs, dtype="float32")


async def async_embed_batch(texts: list[str]) -> np.ndarray:
    """异步嵌入批处理"""
    processed_texts = []
    for text in texts:
        if len(text) > 8192:
            text = text[:8192]
        processed_texts.append(text)

    client = OpenAI(
        api_key=API_KEY,
        base_url=DASHSCOPE_EMBED_URL
    )

    # 使用异步调用
    resp = await asyncio.to_thread(
        client.embeddings.create,
        model=EMBED_NAME,
        input=processed_texts,
        dimensions=768,
        encoding_format="float"
    )

    vecs = [item.embedding for item in resp.data]
    return np.array(vecs, dtype="float32")


async def async_embed_batch_with_retry(texts: list[str], max_retries=3, retry_delay=1):
    """带重试机制的异步嵌入"""
    for attempt in range(max_retries):
        try:
            return await async_embed_batch(texts)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            print(f"嵌入失败，第{attempt + 1}次重试: {e}")
            await asyncio.sleep(retry_delay * (attempt + 1))


async def async_smart_batch_embedding(meta, batch_size=BATCH_SIZE, max_length=8192, max_concurrent=MAX_CONCURRENT):
    """并发批处理embedding"""
    all_vecs = []
    truncation_count = 0
    semaphore = asyncio.Semaphore(max_concurrent)  # 控制并发数

    async def process_batch(batch_meta, batch_idx):
        async with semaphore:
            try:
                batch_texts = []
                for m in batch_meta:
                    text = m["text"]
                    if len(text) > max_length:
                        text = text[:max_length]
                        nonlocal truncation_count
                        truncation_count += 1
                    batch_texts.append(text)

                print(f"处理批次 {batch_idx} ({len(batch_texts)}个文本)")
                return await async_embed_batch_with_retry(batch_texts)
            except Exception as e:
                print(f"批次 {batch_idx} 处理失败: {e}")
                return None

    # 创建所有批次任务
    tasks = []
    batch_idx = 0
    for i in range(0, len(meta), batch_size):
        batch_meta = meta[i:i + batch_size]
        tasks.append(process_batch(batch_meta, batch_idx))
        batch_idx += 1

    # 并发执行并显示进度
    print(f"开始处理 {len(tasks)} 个批次，最大并发数: {max_concurrent}")
    batch_results = []
    for i, task in enumerate(tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="嵌入处理")):
        result = await task
        batch_results.append(result)

    # 处理结果
    valid_vecs = []
    failed_batches = 0

    for i, result in enumerate(batch_results):
        if result is None:
            print(f"批次 {i} 失败")
            failed_batches += 1
        else:
            valid_vecs.append(result)

    if truncation_count > 0:
        print(f"警告: {truncation_count} 个文本被截断到 {max_length} 字符")

    if failed_batches > 0:
        print(f"有 {failed_batches} 个批次处理失败")

    return valid_vecs


def build_index(project_root: str):
    """构建向量索引（修复异步处理问题）"""
    import time
    start_time = time.time()

    # 文件扫描和分块
    files = list(list_files(project_root))
    meta, all_vecs = [], []

    print(f"扫描到 {len(files)} 个文件，开始分块处理...")
    file_start = time.time()
    for fp in tqdm(files, desc="文件分块"):
        for start, text in read_chunks(fp):
            meta.append({"path": fp, "start": start, "text": text})
    file_time = time.time() - file_start

    print(f"分块完成: {len(meta)} 个文本块, 耗时: {file_time:.2f}s")

    if len(meta) == 0:
        print("警告: 没有找到可处理的文本块")
        return

    # 向量化处理 - 修复版本
    print("开始向量化处理...")
    embed_start = time.time()

    try:
        # 检查是否已有运行的事件循环
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 在运行的事件循环中，使用同步方式等待异步任务完成
            async def run_embedding():
                return await async_smart_batch_embedding(meta)

            # 创建新的事件循环来运行异步任务
            new_loop = asyncio.new_event_loop()
            try:
                all_vecs = new_loop.run_until_complete(run_embedding())
            finally:
                new_loop.close()
        else:
            # 如果没有运行的事件循环，使用 asyncio.run
            all_vecs = asyncio.run(async_smart_batch_embedding(meta))
    except RuntimeError as e:
        # 如果上述方法都失败，回退到同步版本
        print(f"异步处理失败: {e}，使用同步处理模式...")
        all_vecs = sync_smart_batch_embedding(meta)

    embed_time = time.time() - embed_start

    if not all_vecs:
        raise RuntimeError("所有批处理都失败了，无法构建索引")

    # 索引构建（后续代码保持不变）
    print("构建FAISS索引...")
    index_start = time.time()
    all_vecs = np.vstack(all_vecs)

    # 检查向量维度一致性
    vector_dim = all_vecs.shape[1]
    print(f"向量维度: {vector_dim}")

    # 根据实际向量维度创建索引
    index = faiss.IndexFlatIP(vector_dim)
    faiss.normalize_L2(all_vecs)
    index.add(all_vecs)

    # 保存索引和元数据
    faiss.write_index(index, INDEX_FILE)
    with open(META_FILE, "w", encoding="utf-8") as g:
        json.dump(meta, g, ensure_ascii=False, indent=2)
    index_time = time.time() - index_start

    total_time = time.time() - start_time

    # 性能统计
    print(f"\n=== 性能统计 ===")
    print(f"文件分块: {file_time:.2f}s ({file_time / total_time * 100:.1f}%)")
    print(f"向量化: {embed_time:.2f}s ({embed_time / total_time * 100:.1f}%)")
    print(f"索引构建: {index_time:.2f}s ({index_time / total_time * 100:.1f}%)")
    print(f"总耗时: {total_time:.2f}s")
    print(f"索引大小: {index.ntotal} 个向量")
    print(f"平均速度: {index.ntotal / total_time:.1f} 向量/秒")


def load_index():
    """加载索引和元数据"""
    if not Path(INDEX_FILE).exists() or not Path(META_FILE).exists():
        raise FileNotFoundError(f"索引文件不存在: {INDEX_FILE} 或 {META_FILE}")

    index = faiss.read_index(INDEX_FILE)
    with open(META_FILE, encoding="utf-8") as g:
        meta = json.load(g)
    return index, meta


def search(query: str, top_k=DEFAULT_TOPK):
    """搜索相似代码片段"""
    top_k = int(top_k)
    index, meta = load_index()

    # 查询向量化
    qvec = embed_batch([query])
    faiss.normalize_L2(qvec)

    # 搜索相似向量
    scores, ids = index.search(qvec, min(top_k, index.ntotal))

    results = []
    for score, idx in zip(scores[0], ids[0]):
        if idx < len(meta):  # 确保索引有效
            m = meta[idx]
            results.append({
                "path": m["path"],
                "start": m["start"],
                "text": m["text"],
                "score": float(score)
            })

    return results


def build_prompt(query: str, snippets: list[dict]) -> str:
    """构建提示词"""
    if not snippets:
        return "未找到相关的代码片段"

    prompt = ["\n=== 检索到的代码片段 ==="]
    for i, s in enumerate(snippets, 1):
        prompt.append(f"\n[片段 {i}] 文件: {s['path']} 行: {s['start']} 相似度: {s['score']:.3f}\n{s['text']}")
    return "\n".join(prompt)


def build_vec_index(project_root: str, out_path: str):
    """构建向量索引入口函数"""
    global INDEX_FILE, META_FILE
    if out_path:
        INDEX_FILE = out_path + "/faiss.index"
        META_FILE = out_path + "/meta.json"

    # 创建输出目录
    Path(out_path).mkdir(parents=True, exist_ok=True)

    if Path(INDEX_FILE).exists() and Path(META_FILE).exists():
        print(f"[跳过] 索引已存在: {INDEX_FILE}, 如需重建请手动删除")
        return

    build_index(project_root)


def query_code(query: str, project_root: str, top_k: int = DEFAULT_TOPK, out_path: str = None):
    """查询代码入口函数"""
    global INDEX_FILE, META_FILE
    if out_path:
        INDEX_FILE = out_path + "/faiss.index"
        META_FILE = out_path + "/meta.json"

    build_vec_index(project_root, out_path)
    snippets = search(query, top_k)
    answer = build_prompt(query, snippets)
    return answer


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description="代码语义检索系统")
    parser.add_argument("--build", action="store_true", help="构建向量索引")
    parser.add_argument("--root", default=".", help="项目根目录")
    parser.add_argument("--query", type=str, help="用户问题")
    parser.add_argument("--top_k", type=int, default=DEFAULT_TOPK, help="返回结果数量")
    parser.add_argument("--out_path", type=str, default=INDEX_FILE, help="索引输出路径")
    parser.add_argument("--concurrent", type=int, default=MAX_CONCURRENT, help="最大并发数")

    args = parser.parse_args()

    if args.build:
        build_vec_index(args.root, args.out_path)
        return
    if args.query:
        ans = query_code(args.query, args.root, args.top_k, args.out_path)
        print("\n----- 检索结果 -----\n")
        print(ans)
        return

    parser.print_help()


if __name__ == "__main__":
    # 清理代理环境变量
    import os

    os.environ.pop('all_proxy', None)
    os.environ.pop('ALL_PROXY', None)
    os.environ.pop('http_proxy', None)
    os.environ.pop('https_proxy', None)

    main()
