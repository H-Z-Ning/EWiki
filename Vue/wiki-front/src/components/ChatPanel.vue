<!-- ChatPanel.vue -->
<template>
  <aside
    class="chat-drawer"
    :style="{ transform: drawerTransform }"
  >
    <!-- 头部 -->
    <header class="chat-header">
      <div class="header-left">
        <h3>💬 项目对话</h3>
        <span class="project-badge" v-if="currentProject">{{ currentProject }}</span>
        <span class="no-project" v-else>未选择项目</span>
      </div>
      <div class="header-actions" v-if="currentProject">
        <button class="knowledge-btn" @click="showKnowledgePanel = !showKnowledgePanel" title="知识库管理">
          📚
        </button>
        <button class="close-btn" @click="closeDrawer">×</button>
      </div>
      <div v-else class="header-actions">
        <button class="close-btn" @click="closeDrawer">×</button>
      </div>
    </header>
    <div v-if="showKnowledgePanel && currentProject" class="knowledge-panel">
      <div class="knowledge-header">
        <h4>📚 知识库管理</h4>
        <button class="close-panel-btn" @click="showKnowledgePanel = false">×</button>
      </div>

      <!-- 文件上传 -->
      <div class="upload-section">
        <input
          type="file"
          ref="fileInput"
          @change="handleFileUpload"
          style="display: none"
          accept=".txt,.md,.pdf,.doc,.docx,.xls,.xlsx,.csv,.json,.xml,.html"
        />
        <button class="upload-btn" @click="$refs.fileInput.click()">
          📁 选择文件
        </button>
        <span class="file-name" v-if="uploadingFile">{{ uploadingFile.name }}</span>
        <button
          class="confirm-upload-btn"
          @click="confirmUpload"
          :disabled="!uploadingFile"
        >
          {{ uploading ? '上传中...' : '上传' }}
        </button>
      </div>

      <!-- 文件列表 -->
      <div class="file-list" v-if="knowledgeFiles.length > 0">
        <h5>已上传文件:</h5>
        <div
          v-for="file in knowledgeFiles"
          :key="file.filename"
          class="file-item"
        >
          <span class="file-info">
            <strong>{{ file.filename }}</strong>
            ({{ formatFileSize(file.size) }})
          </span>
          <button
            class="delete-file-btn"
            @click="deleteKnowledgeFile(file.filename)"
            title="删除文件"
          >
            🗑️
          </button>
        </div>
      </div>
      <div v-else class="no-files">
        <p>暂无知识库文件</p>
      </div>

      <div class="knowledge-tips">
        <small>支持格式: txt, md, pdf, doc, xls, json, xml, html 等</small>
      </div>
    </div>
    <!-- 消息列表 -->
    <div class="chat-messages" ref="msgBox">
      <!-- 欢迎消息 -->
      <div v-if="messages.length === 0" class="welcome-message">
        <div class="welcome-content">
          <div class="welcome-icon">🤖</div>
          <h4>欢迎使用 EWiki 助手</h4>
          <p>我可以帮您：</p>
          <ul>
            <li>解释代码功能和实现</li>
            <li>分析项目结构和模块关系</li>
            <li>回答关于代码逻辑的问题</li>
            <li>提供开发建议和最佳实践</li>
          </ul>
          <p v-if="currentProject">当前项目: <strong>{{ currentProject }}</strong></p>
          <p v-else class="warning-text">请先在左侧选择项目</p>
        </div>
      </div>

      <!-- 对话消息 -->
      <div
        v-for="(m, i) in messages"
        :key="i"
        :class="['bubble', m.role]"
      >
        <div class="avatar">
          {{ m.role === 'user' ? '🧑' : '🤖' }}
        </div>
        <div class="content">
          <span class="name">{{ m.role === 'user' ? '您' : 'EWiki助手' }}</span>
          <div class="text" v-html="render(m.text)"></div>
          <span class="time">{{ formatTime(m.timestamp) }}</span>
        </div>
      </div>

      <!-- 加载状态 -->
      <div v-if="loading" class="bubble assistant loading-bubble">
        <div class="avatar">🤖</div>
        <div class="content">
          <span class="name">EWiki助手</span>
          <div class="text">
            <div class="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </div>
      </div>

      <!-- 项目未选择提示 -->
      <div v-if="!currentProject && messages.length > 0" class="project-warning">
        <div class="warning-content">
          <span>⚠️ 请先在左侧选择项目以获取准确的代码分析</span>
        </div>
      </div>
    </div>
    <div class="knowledge-status" v-if="currentProject && lastResponseHasKnowledge">
      <span class="knowledge-badge">📚 已结合知识库内容</span>
    </div>
    <!-- 底部输入 -->
    <div class="chat-footer">
      <div class="project-info" v-if="currentProject">
        <span class="project-label">当前项目:</span>
        <span class="project-name">{{ currentProject }}</span>
      </div>
      <div class="project-info" v-else>
        <span class="no-project-label">请在左侧选择项目</span>
      </div>

      <form @submit.prevent="send" class="chat-input">
        <input
          v-model="input"
          :disabled="loading || !currentProject"
          :placeholder="inputPlaceholder"
          maxlength="1000"
        />
        <button
          :disabled="loading || !currentProject || !input.trim()"
          type="submit"
          class="send-btn"
        >
          <span v-if="loading">⏳</span>
          <span v-else>➤</span>
        </button>
      </form>

      <div class="chat-tips" v-if="!currentProject">
        <small>请在左侧边栏选择项目以开始对话</small>
      </div>
      <div class="chat-tips" v-else>
        <small>按 Enter 发送，Ctrl+Enter 换行</small>
      </div>
    </div>
  </aside>

  <!-- 触发按钮 -->
  <button
    v-if="!isOpen"
    class="fab"
    @click="openDrawer"
    :title="fabTitle"
  >
    💬
    <span class="fab-badge" v-if="messages.length > 0">{{ messages.length }}</span>
  </button>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import MarkdownIt from 'markdown-it'

// 使用路由获取当前项目
const route = useRoute()

// Markdown 渲染器
const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true
})

// 响应式数据 - 确保按正确顺序初始化
const messages = ref<{
  role: 'user' | 'assistant';
  text: string;
  timestamp: number;
}[]>([])
const input = ref('')
const loading = ref(false)
const msgBox = ref<HTMLElement>()
const isOpen = ref(false)

// 计算属性 - 从路由参数获取当前项目
const currentProject = computed(() => {
  return route.params.project as string || ''
})

// 知识库相关响应式数据
const showKnowledgePanel = ref(false)
const knowledgeFiles = ref<{filename: string; size: number; upload_time: string}[]>([])
const uploadingFile = ref<File | null>(null)
const uploading = ref(false)
const lastResponseHasKnowledge = ref(false)

// 其他计算属性
const drawerTransform = computed(() => (isOpen.value ? 'translateX(0)' : 'translateX(100%)'))
const inputPlaceholder = computed(() => {
  if (!currentProject.value) return '请在左侧选择项目...'
  if (loading.value) return '正在思考中...'
  return '输入关于代码的问题，按回车发送'
})
const fabTitle = computed(() => {
  const count = messages.value.length
  const projectInfo = currentProject.value ? ` - ${currentProject.value}` : ''
  return count > 0 ? `对话记录 (${count} 条${projectInfo})` : '打开对话窗口'
})

// 方法
const render = (txt: string) => md.render(txt)

const formatTime = (timestamp: number) => {
  return new Date(timestamp).toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

const scrollToBottom = async () => {
  await nextTick()
  if (msgBox.value) {
    msgBox.value.scrollTop = msgBox.value.scrollHeight
  }
}

// 知识库相关方法
const loadKnowledgeFiles = async () => {
  if (!currentProject.value) return
  
  try {
    const response = await fetch(`/api/${currentProject.value}/knowledge/files`)
    if (response.ok) {
      knowledgeFiles.value = await response.json()
    }
  } catch (error) {
    console.error('加载知识库文件失败:', error)
  }
}

const handleFileUpload = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files && target.files[0]) {
    uploadingFile.value = target.files[0]
  }
}

const confirmUpload = async () => {
  if (!uploadingFile.value || !currentProject.value) return
  
  uploading.value = true
  const formData = new FormData()
  formData.append('file', uploadingFile.value)
  
  try {
    const response = await fetch(`/api/${currentProject.value}/knowledge/upload`, {
      method: 'POST',
      body: formData
    })
    
    if (response.ok) {
      const result = await response.json()
      console.log('文件上传成功:', result)
      // 重新加载文件列表
      await loadKnowledgeFiles()
      // 重置上传状态
      uploadingFile.value = null
      // 清空文件输入框
      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement
      if (fileInput) fileInput.value = ''
    } else {
      throw new Error('上传失败')
    }
  } catch (error) {
    console.error('文件上传失败:', error)
    alert('文件上传失败，请重试')
  } finally {
    uploading.value = false
  }
}

const deleteKnowledgeFile = async (filename: string) => {
  if (!currentProject.value || !confirm('确定要删除这个文件吗？')) return
  
  try {
    const response = await fetch(`/api/${currentProject.value}/knowledge/files/${filename}`, {
      method: 'DELETE'
    })
    
    if (response.ok) {
      await loadKnowledgeFiles()
    } else {
      throw new Error('删除失败')
    }
  } catch (error) {
    console.error('文件删除失败:', error)
    alert('文件删除失败，请重试')
  }
}

const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 原有的send方法（修改以支持知识库）
const send = async () => {
  if (!input.value.trim() || !currentProject.value || loading.value) return

  const question = input.value.trim()
  input.value = ''

  // 添加用户消息
  const userMessage = {
    role: 'user' as const,
    text: question,
    timestamp: Date.now()
  }
  messages.value.push(userMessage)
  await scrollToBottom()

  loading.value = true
  lastResponseHasKnowledge.value = false

  try {
    // 构建历史记录（排除当前用户消息）
    const history = messages.value
      .slice(0, -1)
      .map(msg => ({
        role: msg.role,
        text: msg.text
      }))

    // 调用聊天API
    const response = await fetch(`/api/${currentProject.value}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        question: question,
        topk: 5,
        history: history
      })
    })

    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`HTTP ${response.status}: ${errorText}`)
    }

    const data = await response.json()

    // 设置知识库状态
    lastResponseHasKnowledge.value = data.has_knowledge || false

    // 添加助手回复
    messages.value.push({
      role: 'assistant',
      text: data.answer,
      timestamp: Date.now()
    })

  } catch (error) {
    console.error('Chat error:', error)
    // 原有的错误处理逻辑保持不变
    let errorMessage = '抱歉，暂时无法回答问题。'
    if (error instanceof Error) {
      if (error.message.includes('404')) {
        errorMessage = '项目未找到，请确保项目已正确导入。'
      } else if (error.message.includes('500')) {
        errorMessage = '服务器暂时不可用，请稍后重试。'
      } else {
        errorMessage = `请求失败: ${error.message}`
      }
    }

    messages.value.push({
      role: 'assistant',
      text: errorMessage,
      timestamp: Date.now()
    })
  } finally {
    loading.value = false
    await scrollToBottom()
  }
}

// 其他原有方法保持不变...
const openDrawer = () => {
  isOpen.value = true
  // 打开时如果有项目，添加欢迎消息并加载知识库
  if (currentProject.value) {
    if (messages.value.length === 0) {
      addWelcomeMessage()
    }
    loadKnowledgeFiles()
  }
}

const closeDrawer = () => {
  isOpen.value = false
}

const addWelcomeMessage = () => {
  if (currentProject.value && messages.value.length === 0) {
    messages.value.push({
      role: 'assistant',
      text: `您好！我已准备好分析项目 **${currentProject.value}** 的代码。\n\n您可以问我：\n- 这个项目的整体结构和功能\n- 特定模块或类的实现细节\n- 代码逻辑和业务流程\n- 技术架构和设计模式\n\n请提出您的第一个问题吧！`,
      timestamp: Date.now()
    })
  }
}

// 监听器和生命周期保持不变...
watch(isOpen, (newVal) => {
  if (newVal) {
    setTimeout(() => scrollToBottom(), 100)
  }
})

watch(currentProject, (newProject, oldProject) => {
  if (newProject && newProject !== oldProject) {
    messages.value = []
    loadKnowledgeFiles() // 新增：加载知识库文件
    addWelcomeMessage()
    if (isOpen.value) {
      setTimeout(() => scrollToBottom(), 100)
    }
  }
})

// 键盘快捷键和生命周期保持不变...
const handleKeydown = (event: KeyboardEvent) => {
  if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
    event.preventDefault()
    send()
  } else if (event.key === 'Escape' && isOpen.value) {
    event.preventDefault()
    closeDrawer()
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
  if (currentProject.value) {
    addWelcomeMessage()
    loadKnowledgeFiles() // 新增：加载知识库文件
  }
})
</script>

<style scoped>
.chat-drawer {
  position: fixed;
  top: 0;
  right: 0;
  width: 33vw;
  min-width: 400px;
  max-width: 600px;
  height: 100vh;
  background: #f6f8fa;
  border-left: 1px solid #d0d7de;
  display: flex;
  flex-direction: column;
  transition: transform 0.3s ease;
  z-index: 9999;
  box-shadow: -2px 0 12px rgba(0, 0, 0, 0.1);
}

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  background: #fff;
  border-bottom: 1px solid #d0d7de;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-left h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #24292f;
}

.project-badge {
  background: #0969da;
  color: white;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.no-project {
  background: #656d76;
  color: white;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #656d76;
  width: 32px;
  height: 32px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  background: #f6f8fa;
  color: #24292f;
}

.chat-messages {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
  scroll-behavior: smooth;
}

/* 欢迎消息 */
.welcome-message {
  display: flex;
  justify-content: center;
  margin: 20px 0;
}

.welcome-content {
  background: white;
  border: 1px solid #d0d7de;
  border-radius: 12px;
  padding: 20px;
  text-align: center;
  max-width: 320px;
}

.welcome-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.welcome-content h4 {
  margin: 0 0 12px 0;
  color: #24292f;
  font-size: 16px;
}

.welcome-content p {
  margin: 8px 0;
  color: #656d76;
  font-size: 14px;
}

.welcome-content .warning-text {
  color: #cf222e;
  font-weight: 500;
}

.welcome-content ul {
  text-align: left;
  margin: 12px 0;
  padding-left: 20px;
}

.welcome-content li {
  margin: 4px 0;
  color: #656d76;
  font-size: 13px;
}

/* 消息气泡 */
.bubble {
  display: flex;
  margin-bottom: 16px;
  align-items: flex-start;
  animation: fadeIn 0.3s ease;
}

.bubble.user {
  flex-direction: row-reverse;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  margin: 0 8px;
  flex-shrink: 0;
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid #e1e4e8;
}

.bubble.user .avatar {
  background: #0969da;
  border-color: #0969da;
}

.content {
  max-width: 70%;
  position: relative;
}

.bubble.user .content {
  background: #0969da;
  color: #fff;
}

.bubble.assistant .content {
  background: #fff;
  color: #24292f;
  border: 1px solid #d0d7de;
}

.content {
  padding: 12px 16px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.5;
  word-wrap: break-word;
}

.name {
  font-weight: 600;
  font-size: 12px;
  margin-bottom: 4px;
  display: block;
  opacity: 0.8;
}

.bubble.user .name {
  text-align: right;
}

.text {
  word-break: break-word;
}

.text :deep(code) {
  background: rgba(175, 184, 193, 0.2);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
}

.text :deep(pre) {
  background: #f6f8fa;
  border: 1px solid #e1e4e8;
  border-radius: 6px;
  padding: 12px;
  overflow-x: auto;
  margin: 8px 0;
}

.text :deep(pre code) {
  background: none;
  padding: 0;
}

.time {
  font-size: 11px;
  opacity: 0.6;
  margin-top: 6px;
  display: block;
}

.bubble.user .time {
  text-align: right;
}

/* 加载状态 */
.loading-bubble .text {
  display: flex;
  align-items: center;
  min-height: 20px;
}

.typing-indicator {
  display: flex;
  align-items: center;
  gap: 4px;
}

.typing-indicator span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #656d76;
  animation: typing 1.4s infinite ease-in-out;
}

.typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator span:nth-child(2) { animation-delay: -0.16s; }

@keyframes typing {
  0%, 80%, 100% { opacity: 0.3; }
  40% { opacity: 1; }
}

/* 项目警告 */
.project-warning {
  display: flex;
  justify-content: center;
  margin: 12px 0;
}

.warning-content {
  background: #fff8c5;
  border: 1px solid #d4a72c;
  border-radius: 8px;
  padding: 12px 16px;
  font-size: 13px;
  color: #7d4e00;
}

/* 底部区域 */
.chat-footer {
  border-top: 1px solid #d0d7de;
  background: white;
  flex-shrink: 0;
}

.project-info {
  padding: 12px 16px;
  border-bottom: 1px solid #f6f8fa;
  display: flex;
  align-items: center;
  gap: 8px;
}

.project-label {
  font-size: 13px;
  color: #656d76;
}

.project-name {
  font-size: 13px;
  font-weight: 600;
  color: #0969da;
  background: #f6f8fa;
  padding: 2px 8px;
  border-radius: 4px;
}

.no-project-label {
  font-size: 13px;
  color: #656d76;
  font-style: italic;
}

.chat-input {
  display: flex;
  align-items: center;
  padding: 16px;
  gap: 8px;
}

.chat-input input {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid #d0d7de;
  border-radius: 20px;
  font-size: 14px;
  outline: none;
  transition: all 0.2s ease;
}

.chat-input input:focus {
  border-color: #0969da;
  box-shadow: 0 0 0 3px rgba(9, 105, 218, 0.1);
}

.chat-input input:disabled {
  background: #f6f8fa;
  color: #656d76;
  cursor: not-allowed;
}

.send-btn {
  background: #0969da;
  color: #fff;
  border: none;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.send-btn:hover:not(:disabled) {
  background: #0550ae;
  transform: scale(1.05);
}

.send-btn:disabled {
  background: #d0d7de;
  cursor: not-allowed;
  transform: none;
}

.chat-tips {
  padding: 8px 16px 16px;
  text-align: center;
}

.chat-tips small {
  color: #656d76;
  font-size: 12px;
}

/* 触发按钮 */
.fab {
  position: fixed;
  bottom: 24px;
  right: 24px;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  border: none;
  background: #0969da;
  color: #fff;
  font-size: 24px;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(9, 105, 218, 0.3);
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1001;
}

.fab:hover {
  background: #0550ae;
  transform: scale(1.1);
  box-shadow: 0 6px 16px rgba(9, 105, 218, 0.4);
}

.fab-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  background: #cf222e;
  color: white;
  border-radius: 10px;
  min-width: 18px;
  height: 18px;
  font-size: 11px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid white;
}

/* 动画 */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .chat-drawer {
    width: 100vw;
    min-width: unset;
    max-width: unset;
  }

  .content {
    max-width: 85%;
  }
}

/* 滚动条样式 */
.chat-messages::-webkit-scrollbar {
  width: 6px;
}

.chat-messages::-webkit-scrollbar-track {
  background: #f6f8fa;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: #d0d7de;
  border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-thumb:hover {
  background: #afb8c1;
}


/* 知识库面板样式 */
.knowledge-panel {
  background: white;
  border: 1px solid #d0d7de;
  border-radius: 8px;
  margin: 16px;
  padding: 0;
  max-height: 400px;
  overflow-y: auto;
}

.knowledge-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid #f6f8fa;
}

.knowledge-header h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #24292f;
}

.close-panel-btn {
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  color: #656d76;
  width: 24px;
  height: 24px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-panel-btn:hover {
  background: #f6f8fa;
  color: #24292f;
}

.upload-section {
  padding: 16px;
  border-bottom: 1px solid #f6f8fa;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.upload-btn, .confirm-upload-btn {
  padding: 8px 12px;
  border: 1px solid #d0d7de;
  border-radius: 6px;
  background: white;
  color: #24292f;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s ease;
}

.upload-btn:hover, .confirm-upload-btn:hover:not(:disabled) {
  background: #f6f8fa;
  border-color: #afb8c1;
}

.confirm-upload-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.file-name {
  font-size: 12px;
  color: #656d76;
  flex: 1;
  min-width: 120px;
}

.file-list {
  padding: 16px;
}

.file-list h5 {
  margin: 0 0 12px 0;
  font-size: 13px;
  color: #24292f;
}

.file-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #f6f8fa;
}

.file-item:last-child {
  border-bottom: none;
}

.file-info {
  font-size: 12px;
  color: #656d76;
  flex: 1;
}

.delete-file-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  font-size: 14px;
}

.delete-file-btn:hover {
  background: #f6f8fa;
}

.no-files {
  padding: 20px;
  text-align: center;
  color: #656d76;
  font-size: 13px;
}

.knowledge-tips {
  padding: 12px 16px;
  border-top: 1px solid #f6f8fa;
  background: #f6f8fa;
}

.knowledge-tips small {
  color: #656d76;
  font-size: 11px;
}

/* 知识库状态提示 */
.knowledge-status {
  padding: 8px 16px;
  background: #f0f9ff;
  border-bottom: 1px solid #e1f5fe;
}

.knowledge-badge {
  font-size: 12px;
  color: #0366d6;
  font-weight: 500;
}

/* 头部操作按钮 */
.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.knowledge-btn {
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  width: 32px;
  height: 32px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.knowledge-btn:hover {
  background: #f6f8fa;
}
</style>