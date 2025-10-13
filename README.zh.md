[English](./README.md) | [简体中文](./README.zh.md)    


# 🚀EWiki
EWiki 是一个自动化工具，用于从本地代码或上传的项目生成详细的 Wiki 文档。它可以分析项目的源代码，生成相关的页面，组织项目的结构，并使用 LLM（大型语言模型）生成文档内容。EWiki 支持多种代码格式，并允许用户上传知识库文件进行进一步的扩展。    
<br/>

## 🌌项目在线访问
 [点击访问EWIKI项目](http://123.56.109.84:3000/)     
<br/>

## 📊 效果对比：EWiki vs DeepWiki-Open  

我们固定输入仓库 [lenve/vhr](https://github.com/lenve/vhr)，分别让 **EWiki** 与 **DeepWiki-Open** 生成总览文档，再邀请 4 位「第三方大模型评审」*（Kimi-k2、Qwen3-max、DeepSeek、ChatGPT-4o）* 在 **不知工具来源** 的前提下独立打分（满分 100）。结果如下：

| 评审模型 | EWiki 得分 | DeepWiki-Open 得分 | 分差 | 备注（均摘自模型原话） |
|---|---|---|---|---|
| **Kimi-k2** | **92** | 76 | **+16** | “文档1技术细节丰富、可视化专业，可直接作为官方 Wiki。” |
| **Qwen3-max** | **92** | 68 | **+24** | “文档1对多模块、存储过程、消息确认机制描述精准；文档2仅停留在罗列名词。” |
| **DeepSeek** | **92** | 78 | **+14** | “文档1架构理解深刻，功能流程与源码一致；文档2缺少实现机制。” |
| **ChatGPT-4o** | **98** | 85 | **+13** | “文档1接近生产级技术文档，文档2适合入门但深度不足。” |
| **平均得分** | **93.5** | 76.75 | **+16.75** | **EWiki 领先近 17 分，全部模型一致胜出** |

&gt; 🧪 评审规则：  
&gt; 1. 每份文档匿名编号，模型仅见「文档 A / 文档 B」；  
&gt; 2. 统一 5 维度（完整性、准确性、结构、可读、信息价值）× 20 分；  
&gt; 3. 模型输出原始评分与理由后人工汇总，无事后润色。


<details>
<summary><b>🔍 AI评审总结（点击展开）</b></summary>

- **Kimi-k2**：  
  文档1 92分 已经非常优秀，建议略作精简，避免重复总结，提升信息密度与阅读节奏。  
  文档2 76分 适合入门者快速了解项目，但建议增加功能流程图、模块交互说明、关键技术细节，提升技术深度与实用性。

- **Qwen3-max**：  
  文档1：92分 —— 高质量技术总览，接近官方文档水平，适合开发者深入理解项目。  
  文档2：68分 —— 基础介绍尚可，但缺乏技术深度和架构洞察，难以支撑实际开发或学习。

- **DeepSeek**：  
  文档1明显优于文档2，主要体现在技术深度、架构理解和功能覆盖的全面性上。文档1的作者对vhr项目有深入的理解，能够准确描述项目的技术实现细节和架构设计思想，而文档2更多是对项目表面的概括性描述。  
  对于技术项目的wiki文档，深度和准确性比广度更重要，这也是文档1获得更高评分的主要原因。

- **ChatGPT-4o**：  
  文档1（98分）：专业级自动化生成成果，结构完备、信息丰富、技术准确。  
  文档2（85分）：简明清晰、适合快速上手，但缺乏系统深度与细节。

### 🎯 一句话结论

**4 大模型、4 轮盲评、平均领先 16.75 分**——EWiki 生成的 Wiki 总览在**技术深度、架构准确性、可视化表达**上全面优于 DeepWiki-Open，可直接用于项目归档、团队交接或教学参考。
</details>    

<br/>

## ✨特性和功能
- **支持多种语言**：支持生成 Java、Python、JavaScript 等编程语言的 Wiki 文档。
- **自动化 Wiki 生成**：自动分析项目的源代码，生成相关页面。
- **AI智能问答**：AI助手结合项目源码和wiki进行问题回答。
- **灵活的知识库上传**：用户可以上传知识库文件并自动构建索引。
- **基于 RAG 模型的代码查询**：使用代码搜索和调用链分析功能来提升文档的准确性。
- **集成 LLM 查询**：支持通过 LLM 模型回答开发者的技术问题。
- **使用并发提高文本向量化**：通过在文本embedding向量化过程中使用并发方式提高中大型项目wiki生成速度。
- **上传项目/本地项目生成Wiki功能**:支持上传项目代码或本地代码的wiki生成。
- **国际化**:支持生成中文/英文wiki,前端页面支持国际化  
<br/>

## 🎯项目截图
**首页**
<img width="1904" height="957" alt="image" src="https://github.com/user-attachments/assets/b64ff437-f973-4aee-a849-c79cac7516ab" />

**生成项目wiki页面**
<img width="1912" height="952" alt="image" src="https://github.com/user-attachments/assets/aef43765-7148-425b-abe2-cfd926d07ee5" />

**AI助手页面**
<img width="1916" height="951" alt="image" src="https://github.com/user-attachments/assets/d53d0f02-4d17-441e-bfc5-e1f903929ad9" />

**知识库上传页面**
<img width="1915" height="951" alt="image" src="https://github.com/user-attachments/assets/c0613800-bffd-4bdc-b338-1d0573feadb8" />
<br/>

## 🛠️使用说明
**第一步 clone 项目**
```shell
git clone https://github.com/H-Z-Ning/EWiki.git
```

**第二步 修改配置文件src/config.xml**

将src/config.xml中的API_KEY改为自己阿里云的API_KEY

**第三步 执行后端**

创建项目时使用的是python3.11.7

```shell
pip install -r requirements.txt
```
```shell
python app.py
```

**第四步 执行前端**
```shell
cd Vue/wiki-front
```
```shell
npm install
```
```shell
npm run dev
```

访问前端的
```shell
http://localhost:3000/
```

<br/>

## 📁 项目结构一览

```text
├── app.py                  # 后端入口（Flask / FastAPI）
├── requirements.txt        # Python 依赖
├── LICENSE
├── README.md
├── src                     # 后端核心包
│   ├── config.py           # 全局配置（动态读取 config.xml）
│   ├── config.xml          # 阿里云 API_KEY 等敏感配置（不纳入版本控制）
│   ├── embedding.py        # 文本向量化（并发加速 Embedding）
│   ├── llm.py              # LLM 调用封装（阿里云大模型）
│   ├── prompts.py          # 提示词模板
│   ├── rag.py              # RAG 检索增强生成
│   ├── tools               # 代码分析工具集
│   │   ├── java_callgraph.py   # Java 调用链解析
│   │   └── project_parser.py   # 多语言项目结构扫描
│   └── utils.py            # 通用工具函数
└── Vue                     # 前端工程（Vite + Vue3 + TS）
    └── wiki-front
        ├── package.json
        ├── vite.config.ts
        ├── index.html
        ├── src
        │   ├── main.ts
        │   ├── App.vue
        │   ├── router.ts
        │   ├── api/index.ts        # 后端接口封装
        │   ├── i18n                # 国际化（中英）
        │   ├── components          # 业务组件
        │   │   ├── ChatPanel.vue       # AI 问答面板
        │   │   ├── Sidebar.vue         # 目录侧栏
        │   │   ├── MarkdownViewer.vue  # MD 渲染
        │   │   └── LanguageSwitcher.vue
        │   └── views
        │       ├── Home.vue          # 首页（上传/本地项目入口）
        │       └── Wiki.vue          # Wiki 正文与 AI 助手
        └── style.css
```
<br/>

## 📄 License

MIT © DeepWiki-Plus Contributors  
“Standing on the shoulders of giants—and taking one more step.”
