[English](./README.md) | [简体中文](./README.zh.md)

# 🚀 EWiki  
EWiki is an automation tool that turns local or uploaded projects into detailed Wiki pages. It analyzes source code, generates relevant pages, organizes project structure, and uses LLMs to produce documentation. Multiple languages are supported, and you can upload extra knowledge-base files to enrich the result.  

<br/>

## 🌌 Live Demo  
[Click to visit EWiki](http://123.56.109.84:3000/)  

<br/>

## 📊 Benchmark: EWiki vs. DeepWiki-Open  

We fixed the input repo to [lenve/vhr](https://github.com/lenve/vhr) and asked **EWiki** and **DeepWiki-Open** to generate an overview document.  
Four third-party LLM judges *(Kimi-k2, Qwen3-max, DeepSeek, ChatGPT-4o)* scored the two anonymous outputs (max 100) **without knowing which tool produced which**.  

| Judge | EWiki | DeepWiki-Open | Δ | Verbatim comment |
|-------|-------|---------------|---|------------------|
| **Kimi-k2** | **92** | 76 | **+16** | “Doc 1 is rich in technical detail and professional visualization; ready-to-use as the official Wiki.” |
| **Qwen3-max** | **92** | 68 | **+24** | “Doc 1 accurately describes multi-modules, stored procs, and ack-mechanisms; Doc 2 only lists nouns.” |
| **DeepSeek** | **92** | 78 | **+14** | “Doc 1 shows deep architectural insight and matches the real code flow; Doc 2 lacks implementation details.” |
| **ChatGPT-4o** | **98** | 85 | **+13** | “Doc 1 is production-grade; Doc 2 is beginner-friendly but shallow.” |
| **Average** | **93.5** | 76.75 | **+16.75** | **EWiki wins across the board** |

> 🧪 Judging rules:  
> 1. Docs were labeled “A / B”; models never saw the tool names.  
> 2. Five equal-weight dimensions (completeness, accuracy, structure, readability, information value) × 20 pts.  
> 3. Raw scores & reasons were collected manually without post-editing.

<details>
<summary><b>🔍 AI judges summary (click to expand)</b></summary>

- **Kimi-k2**:  
  Doc 1 (92): Excellent; shorten a few repeats to raise density.  
  Doc 2 (76): Okay for quick skim; needs flow charts, module interaction, and tech depth.

- **Qwen3-max**:  
  Doc 1 (92): Near-official quality.  
  Doc 2 (68): Too superficial for real work.

- **DeepSeek**:  
  Doc 1 far better on depth, architecture, and coverage.  
  For technical docs depth beats breadth.

- **ChatGPT-4o**:  
  Doc 1 (98): Auto-generated but production-ready.  
  Doc 2 (85): Clear but system-level depth missing.

### 🎯 One-sentence takeaway  
**Four models, four blind rounds, +16.75 avg**—EWiki’s overview beats DeepWiki-Open on **technical depth, architectural accuracy, and visualization**, ready for archiving, hand-over, or teaching.
</details>

<br/>

## ✨ Features
- **Multi-language**: Java, Python, JavaScript, etc.  
- **One-click Wiki**: Auto-parse source and create pages.  
- **AI Q&A**: Chat with an assistant grounded in your code + Wiki.  
- **Knowledge-base upload**: Upload extra docs; auto-indexed.  
- **RAG-based code search**: Call-graph analysis for precision.  
- **LLM tech support**: Ask engineering questions directly.  
- **Concurrent embedding**: Faster vectorization for large codebases.  
- **Upload or local**: Generate from zip or local folder.  
- **i18n**: Chinese/English Wiki & UI.

<br/>

## 🎯 Screenshots
**Home**  
<img width="1904" height="957" alt="image" src="https://github.com/user-attachments/assets/b64ff437-f973-4aee-a849-c79cac7516ab"/>

**Wiki generation**  
<img width="1912" height="952" alt="image" src="https://github.com/user-attachments/assets/aef43765-7148-425b-abe2-cfd926d07ee5"/>

**AI assistant**  
<img width="1916" height="951" alt="image" src="https://github.com/user-attachments/assets/aef43765-7148-425b-abe2-cfd926d07ee5"/>

**Knowledge-base upload**  
<img width="1915" height="951" alt="image" src="https://github.com/user-attachments/assets/c0613800-bffd-4bdc-b338-1d0573feadb8"/>

<br/>

## 🛠️ Quick Start
**1. Clone**
```bash
git clone https://github.com/H-Z-Ning/EWiki.git
```

**2. Fill your key**  
Edit `src/config.xml` and replace `API_KEY` with your Alibaba-Cloud key.

**3. Run backend**  
(Python 3.11.7 used in development)
```bash
pip install -r requirements.txt
python app.py
```

**4. Run frontend**
```bash
cd Vue/wiki-front
npm install
npm run dev
```

Open browser at  
```
http://localhost:3000/
```

<br/>

## 📁 Project Layout
```
├── app.py                  # Backend entry (Flask / FastAPI)
├── requirements.txt        # Python deps
├── LICENSE
├── README.md
├── src                     # Backend core
│   ├── config.py           # Dynamic loader for config.xml
│   ├── config.xml          # Sensitive keys (git-ignored)
│   ├── embedding.py        # Concurrent text embedding
│   ├── llm.py              # Alibaba LLM wrapper
│   ├── prompts.py          # Prompt templates
│   ├── rag.py              # RAG retrieval
│   ├── tools               # Code analyzers
│   │   ├── java_callgraph.py
│   │   └── project_parser.py
│   └── utils.py
└── Vue                     # Vite + Vue3 + TS
    └── wiki-front
        ├── package.json
        ├── vite.config.ts
        ├── index.html
        ├── src
        │   ├── main.ts
        │   ├── App.vue
        │   ├── router.ts
        │   ├── api/index.ts
        │   ├── i18n                # EN / CN
        │   ├── components
        │   │   ├── ChatPanel.vue
        │   │   ├── Sidebar.vue
        │   │   ├── MarkdownViewer.vue
        │   │   └── LanguageSwitcher.vue
        │   └── views
        │       ├── Home.vue
        │       └── Wiki.vue
        └── style.css
```

<br/>

## 📄 License
MIT © DeepWiki-Plus Contributors  
“Standing on the shoulders of giants—and taking one more step.”
