# 🚀EWiki

EWiki 是一个自动化工具，用于从本地代码或上传的项目生成详细的 Wiki 文档。它可以分析项目的源代码，生成相关的页面，组织项目的结构，并使用 LLM（大型语言模型）生成文档内容。EWiki 支持多种代码格式，并允许用户上传知识库文件进行进一步的扩展。
## 🌌项目在线访问
[点击访问EWIKI项目](http://123.56.109.84:3000/)

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

## 🎯项目截图
**首页**
<img width="1904" height="957" alt="image" src="https://github.com/user-attachments/assets/b64ff437-f973-4aee-a849-c79cac7516ab" />

**生成项目wiki页面**
<img width="1912" height="952" alt="image" src="https://github.com/user-attachments/assets/aef43765-7148-425b-abe2-cfd926d07ee5" />

**AI助手页面**
<img width="1916" height="951" alt="image" src="https://github.com/user-attachments/assets/d53d0f02-4d17-441e-bfc5-e1f903929ad9" />

**知识库上传页面**
<img width="1915" height="951" alt="image" src="https://github.com/user-attachments/assets/c0613800-bffd-4bdc-b338-1d0573feadb8" />


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

## 📄 License

MIT © DeepWiki-Plus Contributors  
“Standing on the shoulders of giants—and taking one more step.”
