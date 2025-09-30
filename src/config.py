API_KEY = "sk-9440a2435538408290e2b89d6d3c4e54"
EMBED_NAME = "text-embedding-v3"
DASHSCOPE_EMBED_URL = "https://dashscope.aliyuncs.com/api/v1/services/embeddings/text-embedding/text-embedding"
LLM_NAME="qwen3-coder-plus-2025-09-23"
DASHSCOPE_GENERATION_URL = "http://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"

from pathlib import Path
import xml.etree.ElementTree as ET



# ---------- 新增：配置加载 ----------
CONFIG_FILE = Path(__file__).with_name("config.xml")

def load_config():
    """若 config.xml 不存在则创建默认配置；存在则读取。"""
    if not CONFIG_FILE.exists():
        root = ET.Element("config")
        ET.SubElement(root, "API_KEY").text = "sk-9440a2435538408290e2b89d6d3c4e54"
        ET.SubElement(root, "EMBED_NAME").text = "text-embedding-v3"
        ET.SubElement(root, "EMBED_URL").text = "https://dashscope.aliyuncs.com/api/v1/services/embeddings/text-embedding/text-embedding"
        ET.SubElement(root, "LLM_NAME").text = "qwen3-coder-plus-2025-09-23"
        ET.SubElement(root, "LLM_URL").text = "http://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        ET.SubElement(root, "INDEX_FILE").text = "faiss.index"
        ET.SubElement(root, "META_FILE").text = "meta.json"
        ET.SubElement(root, "MAX_LINES").text = "50"
        ET.SubElement(root, "BATCH_SIZE").text = "6"
        ET.SubElement(root, "TOP_K").text = "5"
        tree = ET.ElementTree(root)
        tree.write(CONFIG_FILE, encoding="utf-8", xml_declaration=True)
        print(f"[INFO] 默认配置已生成：{CONFIG_FILE.resolve()}")

    tree = ET.parse(CONFIG_FILE)
    root = tree.getroot()
    return {child.tag: child.text for child in root}
