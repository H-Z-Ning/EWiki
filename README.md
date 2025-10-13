# 🚀 EWiki

EWiki is an automation tool that generates detailed Wiki documentation from local or uploaded projects. It analyzes source code, creates relevant pages, structures the project, and uses LLM (Large Language Model) to produce documentation. EWiki supports multiple code formats and allows users to upload knowledge-base files for further enrichment.

## 🌌 Live Demo
[Click to visit EWiki](http://123.56.109.84:3000/)

[English](./README.md) | [简体中文](./README.zh.md) 
---
## ✨ Features
- **Multi-language support**: Generate Wiki docs for Java, Python, JavaScript and more.
- **Automated Wiki generation**: Automatically analyze source code and create corresponding pages.
- **AI-powered Q&A**: An AI assistant answers questions based on both source code and generated Wiki.
- **Flexible knowledge-base upload**: Upload knowledge files and auto-index them.
- **RAG-based code search**: Improve accuracy with code search and call-chain analysis.
- **Integrated LLM queries**: Ask technical questions through an LLM.
- **Concurrent text embedding**: Speed up Wiki generation for medium/large projects by parallelizing text vectorization.
- **Upload / local project support**: Generate Wiki from uploaded or local codebases.
- **Internationalization**: Generate Chinese or English Wiki; frontend UI supports i18n.

## 🎯 Screenshots
**Homepage**  
<img width="1904" height="957" alt="image" src="https://github.com/user-attachments/assets/b64ff437-f973-4aee-a849-c79cac7516ab" />

**Generate Wiki page**  
<img width="1912" height="952" alt="image" src="https://github.com/user-attachments/assets/aef43765-7148-425b-abe2-cfd926d07ee5" />

**AI Assistant page**  
<img width="1916" height="951" alt="image" src="https://github.com/user-attachments/assets/d53d0f02-4d17-441e-bfc5-e1f903929ad9" />

**Knowledge-base upload page**  
<img width="1915" height="951" alt="image" src="https://github.com/user-attachments/assets/c0613800-bffd-4bdc-b338-1d0573feadb8" />

## 🛠️ Quick Start
**1. Clone the repo**
```shell
git clone https://github.com/H-Z-Ning/EWiki.git
```

**2. Update config**  
Replace the `API_KEY` in `src/config.xml` with your own Alibaba Cloud API key.

**3. Run backend**  
(Tested with Python 3.11.7)
```shell
pip install -r requirements.txt
python app.py
```

**4. Run frontend**
```shell
cd Vue/wiki-front
npm install
npm run dev
```

Visit the frontend at:
```
http://localhost:3000/
```

## 🔍 Directory Structure

## 📄 License

MIT © DeepWiki-Plus Contributors  
“Standing on the shoulders of giants—and taking one more step.”
