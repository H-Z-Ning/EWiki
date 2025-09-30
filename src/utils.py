import os
import json
from typing import List, Dict, Any
def chunk_text(text: str, max_tokens: int = 300) -> List[str]:
    lines = [l for l in text.splitlines() if l.strip()]
    if not lines:
        return []
    chunks = []
    cur = []
    cur_len = 0
    for ln in lines:
        cur.append(ln)
        cur_len += len(ln.split())
        if cur_len >= max_tokens:
            chunks.append('\n'.join(cur))
            cur = []
            cur_len = 0
    if cur:
        chunks.append('\n'.join(cur))
    return chunks







def write_markdown(out_root: str, module_docs: Dict[str, str], modules_meta: Dict[str, Any]):
    os.makedirs(out_root, exist_ok=True)
    project_name = os.path.basename(os.path.abspath(out_root))

    # 1. modules 子目录
    mod_dir = os.path.join(out_root, 'modules')
    os.makedirs(mod_dir, exist_ok=True)

    # 2. 模块列表索引（放到 modules/README.md）
    readme_modules = [f"# Modules of {project_name}", ""]
    for m in sorted(module_docs.keys()):
        md_name = f"{m.replace('.', '_')}.md"
        readme_modules.append(f"- [{m}]({md_name})")
    # with open(os.path.join(mod_dir, 'README.md'), 'w', encoding='utf-8') as f:
    #     f.write('\n'.join(readme_modules))

    # 3. 每个模块自己的文档
    for m, doc in module_docs.items():
        path = os.path.join(mod_dir, f"{m.replace('.', '_')}.md")
        with open(path, 'w', encoding='utf-8') as f:
            f.write(f"# Module `{m}`\n\n" + doc)

    # 4. 元数据（保留）
    with open(os.path.join(out_root, '_EWiki_meta.json'), 'w', encoding='utf-8') as f:
        json.dump(modules_meta, f, ensure_ascii=False, indent=2)


