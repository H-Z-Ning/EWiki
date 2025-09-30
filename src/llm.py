import sys
import os
# -----------------------------
# LLM client - MAJOR CHANGES HERE
# -----------------------------
import torch
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
from typing import List, Dict, Any, Optional, Tuple, Set
import requests
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# HF generation
# try:
#     # KAGGLE CHANGE: Import necessary libraries for quantized loading
#     import torch
#     from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
#
#     HF_AVAILABLE = True
# except Exception:
#     HF_AVAILABLE = False
PROXY = {
    "https": "http://xxx:80",
    "http": "http://xxx:80"
}
from .config import load_config
import logging
from openai import OpenAI


cfg = load_config()          # 全局配置字典
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



def generate( prompt: str, temperature: float = 0.0, max_tokens: int = 20480) -> str:

    logger = logging.getLogger("LLMClient")

    client = OpenAI(
        api_key=API_KEY,
        base_url=DASHSCOPE_GENERATION_URL,
    )

    messages = [
        {"role": "system", "content": "You are an expert technical writer and software architect, capable of completing tasks in full according to user requirements."},
        {"role": "user", "content": prompt},
    ]
    logger.info("[LLM] >>> model=qwen-plus | max_tokens=%s | temperature=%s", max_tokens, temperature)
    logger.debug("[LLM] >>> messages=%s", messages)

    resp = client.chat.completions.create(
        model=LLM_NAME,
        messages=messages,
        temperature=temperature or 0.7,
        max_tokens=max_tokens,
    )

    content = resp.choices[0].message.content.strip()
    logger.info("[LLM] <<< content(length=%s)=%.10000s...", len(content), content)
    return content
