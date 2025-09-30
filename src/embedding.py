#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码语义检索 + LLM 问答（config.xml 版）
author: kimi
"""
import os
import re
import json
import argparse
import hashlib
import requests
import numpy as np
import faiss
from tqdm import tqdm
from pathlib import Path
import xml.etree.ElementTree as ET
import os
from openai import OpenAI   # 新增

from .config import load_config

cfg = load_config()          # 全局配置字典

# ---------- 从 cfg 取参 ----------
API_KEY       = cfg["API_KEY"]
EMBED_NAME    = cfg["EMBED_NAME"]
DASHSCOPE_EMBED_URL = cfg["EMBED_URL"]
LLM_NAME      = cfg["LLM_NAME"]
DASHSCOPE_GENERATION_URL = cfg["LLM_URL"]
INDEX_FILE    = cfg["INDEX_FILE"]
META_FILE     = cfg["META_FILE"]
MAX_LINES     = int(cfg["MAX_LINES"])
BATCH_SIZE    = int(cfg["BATCH_SIZE"])
DEFAULT_TOPK  = int(cfg["TOP_K"])

CODE_EXT = [".py", ".js", ".ts", ".java", ".cpp", ".c", ".h", ".hpp", ".go", ".rs",
            ".jsx", ".tsx", ".html", ".css", ".php", ".swift", ".cs"]
DOC_EXT  = [".md", ".txt", ".rst", ".json", ".yaml", ".yml", ".xml", ".csv"]
KNOWLEDGE_EXT = [".pdf", ".doc", ".docx", ".xls", ".xlsx"] + DOC_EXT + CODE_EXT

# ---------- 以下代码与之前完全一致，仅把常量换成 cfg 变量 ----------
def md5txt(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()

def list_files(root: str):
    root_path = Path(root)
    if root_path.is_file():
        # 如果是单个文件，直接返回该文件
        yield str(root_path)
    else:
        # 如果是目录，遍历所有文件
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
    # headers = {
    #     "Authorization": f"Bearer {API_KEY}",
    #     "Content-Type": "application/json"
    # }
    # payload = {
    #     "model": EMBED_NAME,
    #     "input": {"texts": texts},
    #     "parameters": {"text_type": "document"}
    # }
    # resp = requests.post(DASHSCOPE_EMBED_URL, headers=headers, json=payload)
    # if resp.status_code != 200:
    #     raise RuntimeError(f"embed error: {resp.text}")
    # data = resp.json()
    # vecs = [item["embedding"] for item in data["output"]["embeddings"]]
    # return np.array(vecs, dtype="float32")


    client = OpenAI(
        api_key=API_KEY,  # 如果您没有配置环境变量，请在此处用您的API Key进行替换
        base_url=DASHSCOPE_EMBED_URL  # 百炼服务的base_url
    )
    resp = client.embeddings.create(
        model=EMBED_NAME,
        input=texts,
        dimensions=1024,  # 指定向量维度（仅 text-embedding-v3及 text-embedding-v4支持该参数）
        encoding_format="float"
    )
    # 提取向量
    vecs = [item.embedding for item in resp.data]
    return np.array(vecs, dtype="float32")

def build_index(project_root: str):
    files = list(list_files(project_root))
    meta, all_vecs = [], []
    for fp in tqdm(files, desc="File"):
        for start, text in read_chunks(fp):
            meta.append({"path": fp, "start": start, "text": text})
    for i in tqdm(range(0, len(meta), BATCH_SIZE), desc="Embedding"):
        batch_text = [m["text"] for m in meta[i:i+BATCH_SIZE]]
        all_vecs.append(embed_batch(batch_text))
    all_vecs = np.vstack(all_vecs)
    assert len(meta) == all_vecs.shape[0]
    index = faiss.IndexFlatIP(1024)
    faiss.normalize_L2(all_vecs)
    index.add(all_vecs)
    faiss.write_index(index, INDEX_FILE)
    with open(META_FILE, "w", encoding="utf-8") as g:
        json.dump(meta, g, ensure_ascii=False, indent=2)
    print(f"Index built: {index.ntotal} vectors")

def load_index():
    index = faiss.read_index(INDEX_FILE)
    with open(META_FILE, encoding="utf-8") as g:
        meta = json.load(g)
    return index, meta

def search(query: str, top_k=DEFAULT_TOPK):
    top_k = int(top_k)
    index, meta = load_index()
    qvec = embed_batch([query])
    faiss.normalize_L2(qvec)
    scores, ids = index.search(qvec, top_k)
    results = []
    for score, idx in zip(scores[0], ids[0]):
        m = meta[idx]
        results.append({
            "path": m["path"], "start": m["start"],
            "text": m["text"], "score": float(score)
        })
    return results



def build_prompt(query: str, snippets: list[dict]) -> str:
    prompt = ["\n=== Retrieved Code Snippets ==="]
    for i, s in enumerate(snippets, 1):
        prompt.append(f"\n[Snippet {i}] File: {s['path']}  Line: {s['start']}  Score: {s['score']:.3f}\n{s['text']}")
    return "\n".join(prompt)



# ==================== 1. 向量化建库 ====================
def build_vec_index(project_root: str,
                    out_path: str):
    """
    将项目代码向量化并持久化
    :param project_root: 项目根目录
    :param index_file:   保存 faiss 索引路径（None=用 config.xml 值）
    :param meta_file:    保存元数据 json 路径（None=用 config.xml 值）
    """
    global INDEX_FILE, META_FILE
    if out_path:
        INDEX_FILE = out_path + "/faiss.index"
        META_FILE = out_path + "/meta.json"
    if Path(INDEX_FILE).exists() and Path(META_FILE).exists():
        print(f"[SKIP] 索引已存在：{INDEX_FILE} 与 {META_FILE}，如需重建请手动删除后重试。")
        return
    build_index(project_root)          # 沿用之前实现


# ==================== 2. 查询代码 ====================
def query_code(query: str,
               project_root: str,
               top_k: int = DEFAULT_TOPK,
               out_path: str = None):
    """
    根据问题检索最相似代码
    :param query:       用户问题
    :param top_k:       返回条数
    :param index_file:  指定索引文件（None=用 config.xml 值）
    :param meta_file:   指定元数据文件（None=用 config.xml 值）
    :return:            (answer:str, snippets:list[dict])
    """
    global INDEX_FILE, META_FILE
    if out_path:
        INDEX_FILE = out_path + "/faiss.index"
        META_FILE = out_path + "/meta.json"
    build_vec_index(project_root,out_path)
    snippets = search(query, top_k)
    answer   = build_prompt(query, snippets)
    return answer


# ==================== 3. 可选：保留命令行入口 ====================
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true", help="构建向量索引")
    parser.add_argument("--root", default=".", help="项目根目录")
    parser.add_argument("--query", type=str, help="用户问题")
    parser.add_argument("--top_k", type=int, default=DEFAULT_TOPK)
    parser.add_argument("--out_path", type=str, default=INDEX_FILE,
                        help="faiss索引文件路径(默认取config.xml)")
    args = parser.parse_args()

    if args.build:
        build_vec_index(args.root, args.out_path)
        return
    if args.query:
        ans = query_code(args.query,args.root, args.top_k, args.out_path)
        print("\n----- LLM 回答 -----\n")
        print(ans)
        return
    parser.print_help()


if __name__ == "__main__":
    import os

    os.environ.pop('all_proxy', None)  # 小写
    os.environ.pop('ALL_PROXY', None)  # 大写（Unix 下常见）
    main()