<template>
  <div class="layout">
    <Sidebar :project="project" @select="handleSelect" />
    <main class="main">
      <div class="markdown-body" v-html="renderedContent"></div>
    </main>
    <ChatPanel :project="project" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, computed } from 'vue'
import { useRoute } from 'vue-router'
import MarkdownIt from 'markdown-it'
import Sidebar from '@/components/Sidebar.vue'
import ChatPanel from '@/components/ChatPanel.vue'
import { getModule, getProjectReadme } from '@/api'
import mermaid from 'mermaid'

const route = useRoute()
const project = route.params.project as string
const content = ref('')

// 初始化 markdown-it，配置 Mermaid 支持
const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
  breaks: true,
  highlight: function (str, lang) {
    // 如果是 mermaid 代码块，保留原样（不转义）
    if (lang === 'mermaid') {
      return `<pre class="mermaid">${str}</pre>`
    }
    // 其他代码块正常处理
    return `<pre class="language-${lang}"><code>${md.utils.escapeHtml(str)}</code></pre>`
  }
})

// 计算属性，将 markdown 转换为 HTML
const renderedContent = computed(() => {
  return md.render(content.value)
})

// 初始化 Mermaid
mermaid.initialize({
  startOnLoad: false,
  theme: 'default',
  securityLevel: 'loose',
  flowchart: {
    useMaxWidth: false,
    htmlLabels: true,
    curve: 'basis'
  }
})

// 渲染 Mermaid 图表
async function renderMermaid() {
  await nextTick()

  const els = document.querySelectorAll<HTMLElement>('.mermaid')
  for (const el of els) {
    if (el.hasAttribute('data-processed')) continue

    const def = el.textContent?.trim()
    if (!def) continue

    // 1. 先清空，防止上次错误残留
    el.textContent = ''
    el.setAttribute('data-processed', 'true')

    // 2. 离屏节点
    const sandbox = document.createElement('div')
    sandbox.style.position = 'absolute'
    sandbox.style.left = '-9999px'
    document.body.appendChild(sandbox)

    try {
      const { svg } = await mermaid.render('m' + Math.random().toString(36).slice(2), def)
      el.innerHTML = svg          // 成功 → 真正显示
    } catch (e) {
      // 失败 → 什么也不放，用户看不到任何报错
      el.innerHTML = ''           // 或者你想放一张提示图也行
      console.error('[Mermaid] 图表语法错误：', e, def)
    } finally {
      document.body.removeChild(sandbox)
    }
  }
}

async function handleSelect(key: string) {
  content.value = key === 'project'
    ? await getProjectReadme(project)
    : await getModule(project, key)

  // 内容更新后渲染 Mermaid
  await nextTick()
  await renderMermaid()
}

onMounted(() => handleSelect('project'))
</script>

<style>
* {
  margin: 0;
  box-sizing: border-box;
}
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}
.layout {
  display: flex;
  height: 100vh;
}
.main {
  flex: 1;
  overflow-y: auto;
  width: 100%;
  padding: 20px;
  background: white;
}

/* GitHub Markdown 样式 */
.markdown-body {
  box-sizing: border-box;
  min-width: 200px;
  max-width: 980px;
  margin: 0 auto;
  padding: 45px;
}

@media (max-width: 767px) {
  .markdown-body {
    padding: 15px;
  }
}

.markdown-body h1, .markdown-body h2 {
  border-bottom: 1px solid #eaecef;
  padding-bottom: 0.3em;
}

.markdown-body h1, .markdown-body h2, .markdown-body h3, .markdown-body h4, .markdown-body h5, .markdown-body h6 {
  margin-top: 24px;
  margin-bottom: 16px;
  font-weight: 600;
  line-height: 1.25;
}

.markdown-body p {
  margin-bottom: 16px;
  line-height: 1.6;
}

.markdown-body code {
  padding: 0.2em 0.4em;
  margin: 0;
  font-size: 85%;
  background-color: rgba(175, 184, 193, 0.2);
  border-radius: 6px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

.markdown-body pre {
  padding: 16px;
  overflow: auto;
  font-size: 85%;
  line-height: 1.45;
  background-color: #f6f8fa;
  border-radius: 6px;
  margin-bottom: 16px;
}

.markdown-body pre:not(.mermaid) {
  background-color: #f6f8fa;
}

.markdown-body pre.mermaid {
  background: transparent;
  text-align: center;
  padding: 20px;
}

.markdown-body pre code {
  background: none;
  padding: 0;
}

.markdown-body blockquote {
  padding: 0 1em;
  color: #6a737d;
  border-left: 0.25em solid #dfe2e5;
  margin: 0 0 16px 0;
}

.markdown-body table {
  border-spacing: 0;
  border-collapse: collapse;
  margin-bottom: 16px;
  width: 100%;
}

.markdown-body table th, .markdown-body table td {
  padding: 6px 13px;
  border: 1px solid #dfe2e5;
}

.markdown-body table tr {
  background-color: #fff;
  border-top: 1px solid #c6cbd1;
}

.markdown-body table tr:nth-child(2n) {
  background-color: #f6f8fa;
}

.mermaid-error {
  color: #dc2626;
  background: #fef2f2;
  padding: 12px;
  border-radius: 6px;
  border: 1px solid #fecaca;
  margin: 16px 0;
}

.mermaid-error pre {
  background: #f9f9f9;
  padding: 8px;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 12px;
}
</style>