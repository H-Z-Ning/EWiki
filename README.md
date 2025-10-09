# 🚀EWiki

EWiki 是一个自动化工具，用于从本地代码或上传的项目生成详细的 Wiki 文档。它可以分析项目的源代码，生成相关的页面，组织项目的结构，并使用 LLM（大型语言模型）生成文档内容。EWiki 支持多种代码格式，并允许用户上传知识库文件进行进一步的扩展。

## ✨特性

- **支持多种语言**：支持生成 Java、Python、JavaScript 等编程语言的 Wiki 文档。
- **自动化 Wiki 生成**：自动分析项目的源代码，生成相关页面。
- **灵活的知识库上传**：用户可以上传知识库文件并自动构建索引。
- **基于 RAG 模型的代码查询**：使用代码搜索和调用链分析功能来提升文档的准确性。
- **集成 LLM 查询**：支持通过 LLM 模型回答开发者的技术问题。

## 🎯项目截图


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

## 🔍目录结构

