<!-- ChatPanel.vue -->
<template>
  <!-- 底部聊天面板 -->
  <div class="chat-panel" :class="{ 'panel-open': isOpen }">
    <!-- 聊天弹窗 -->
    <div class="chat-modal" v-if="isOpen">
      <!-- 头部 -->
  <header class="chat-header">
    <div class="header-left">
      <h3>{{ $t('chat.projectChat') }}</h3>
      <span class="project-badge" v-if="currentProject">{{ currentProject }}</span>
      <span class="no-project" v-else>{{ $t('chat.noProjectSelected') }}</span>
    </div>
    <div class="header-actions" v-if="currentProject">
      <button
        class="knowledge-btn"
        @click="showKnowledgePanel = !showKnowledgePanel"
        :title="$t('chat.knowledgeManagement')"
      >
        <span class="knowledge-text">{{ $t('chat.uploadKnowledge') }}</span>
      </button>
      <button class="close-btn" @click="closePanel">{{ $t('common.close') }}</button>
    </div>
    <div v-else class="header-actions">
      <button class="close-btn" @click="closePanel">{{ $t('common.close') }}</button>
    </div>
  </header>

  <!-- 知识库面板 -->
  <div v-if="showKnowledgePanel && currentProject" class="knowledge-panel">
    <div class="knowledge-header">
      <h4>{{ $t('chat.knowledgeManagement') }}</h4>
      <button class="close-panel-btn" @click="showKnowledgePanel = false">{{ $t('common.close') }}</button>
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
        {{ $t('chat.selectFile') }}
      </button>
      <span class="file-name" v-if="uploadingFile">{{ uploadingFile.name }}</span>
      <button
        class="confirm-upload-btn"
        @click="confirmUpload"
        :disabled="!uploadingFile"
      >
        {{ uploading ? $t('common.uploading') : $t('common.upload') }}
      </button>
    </div>

    <!-- 文件列表 -->
    <div class="file-list" v-if="knowledgeFiles.length > 0">
      <h5>{{ $t('chat.uploadedFiles') }}</h5>
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
          :title="$t('common.delete')"
        >
          🗑️
        </button>
      </div>
    </div>
    <div v-else class="no-files">
      <p>{{ $t('chat.noFiles') }}</p>
    </div>

    <div class="knowledge-tips">
      <small>{{ $t('chat.supportedFormats') }}</small>
    </div>
  </div>

      <!-- 消息列表 -->
      <div class="chat-messages" ref="msgBox">
        <!-- 欢迎消息 -->
          <div v-if="messages.length === 0" class="welcome-message">
            <div class="welcome-content">
              <div class="welcome-icon">🚀</div>
              <h4>{{ $t('chat.welcome') }}</h4>
              <p>{{ $t('chat.welcomeCapabilities') }}</p>
              <ul>
                <li>{{ $t('chat.explainCode') }}</li>
                <li>{{ $t('chat.analyzeStructure') }}</li>
                <li>{{ $t('chat.answerQuestions') }}</li>
                <li>{{ $t('chat.provideAdvice') }}</li>
              </ul>
              <p v-if="currentProject">{{ $t('chat.currentProject') }} <strong>{{ currentProject }}</strong></p>
              <p v-else class="warning-text">{{ $t('chat.selectProjectLeft') }}</p>
            </div>
          </div>

        <!-- 对话消息 -->
        <div
          v-for="(m, i) in messages"
          :key="i"
          :class="['bubble', m.role]"
        >
          <div class="avatar">
            {{ m.role === 'user' ? '⛄' : '🚀' }}
          </div>
          <div class="content">
            <span class="name">{{ m.role === 'user' ? '' : 'EWiki助手' }}</span>
            <div class="text" v-html="render(m.text)"></div>
            <span class="time">{{ formatTime(m.timestamp) }}</span>
          </div>
        </div>

        <!-- 加载状态 -->
        <div v-if="loading" class="bubble assistant loading-bubble">
          <div class="avatar">🚀</div>
          <div class="content">
           <span class="name">{{ $t('chat.assistant') }}</span>
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

      <!-- 知识库状态 -->
      <div class="knowledge-status" v-if="currentProject && lastResponseHasKnowledge">
        <span class="knowledge-badge">{{ $t('chat.knowledgeApplied') }}</span>
      </div>

      <!-- 底部输入 -->
      <div class="chat-footer">
      <div class="project-info" v-if="currentProject">
        <span class="project-label">{{ $t('chat.currentProject') }}</span>
        <span class="project-name">{{ currentProject }}</span>
      </div>
      <div class="project-info" v-else>
        <span class="no-project-label">{{ $t('chat.selectProjectToStart') }}</span>
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
            <small>{{ $t('chat.selectProjectToStart') }}</small>
          </div>
          <div class="chat-tips" v-else>
            <small>{{ $t('chat.pressEnter') }}</small>
          </div>
      </div>
    </div>

 <div class="chat-trigger" @click="togglePanel" :class="{ 'trigger-active': isOpen }">
      <div class="trigger-container">
        <div class="trigger-main">
          <!-- 左侧图标和状态 -->
          <div class="trigger-left">
            <div class="trigger-icon-wrapper">
              <span class="trigger-icon">💬</span>
              <div class="online-indicator" v-if="currentProject"></div>
            </div>
              <div class="trigger-info">
                <span class="trigger-title">{{ $t('chat.aiAssistant') }}</span>
                <span class="trigger-status" :class="{ 'status-online': currentProject, 'status-offline': !currentProject }">
                  {{ currentProject ? $t('chat.onlineWithProject', { project: currentProject }) : $t('chat.offline') }}
                </span>
              </div>
          </div>

          <!-- 右侧状态和箭头 -->
          <div class="trigger-right">
            <div class="message-indicator" v-if="messages.length > 0">
                <span class="message-count">{{ messages.length }}</span>
                <span class="message-text">{{ $t('chat.messages') }}</span>
              </div>
            <div class="trigger-arrow" :class="{ 'arrow-up': isOpen }">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <path d="M6 9L12 15L18 9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
          </div>
        </div>

        <!-- 进度条效果 -->
        <div class="trigger-progress" :class="{ 'progress-active': isOpen }"></div>
      </div>
    </div>

    <!-- 遮罩层 -->
    <div v-if="isOpen" class="chat-overlay" @click="closePanel"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import MarkdownIt from 'markdown-it'

const { t } = useI18n()
const route = useRoute()

// 在计算属性中使用国际化
const inputPlaceholder = computed(() => {
  if (!currentProject.value) return t('chat.selectProjectFirst')
  if (loading.value) return t('chat.thinking')
  return t('chat.inputPlaceholder')
})

// 使用路由获取当前项目


// Markdown 渲染器
const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true
})

// 响应式数据
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
// const inputPlaceholder = computed(() => {
//   if (!currentProject.value) return '请在左侧选择项目...'
//   if (loading.value) return '正在思考中...'
//   return '输入关于代码的问题，按回车发送'
// })

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
    let errorMessage = t('errors.requestFailed')
    if (error instanceof Error) {
      if (error.message.includes('404')) {
        errorMessage = t('errors.projectNotFound')
      } else if (error.message.includes('500')) {
        errorMessage = t('errors.serverError')
      } else {
        errorMessage = `${t('errors.requestFailed')}: ${error.message}`
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

// 面板控制方法
const togglePanel = () => {
  isOpen.value = !isOpen.value
  if (isOpen.value && currentProject.value) {
    if (messages.value.length === 0) {
      addWelcomeMessage()
    }
    loadKnowledgeFiles()
    setTimeout(() => scrollToBottom(), 100)
  }
}

const closePanel = () => {
  isOpen.value = false
}

const addWelcomeMessage = () => {
  if (currentProject.value && messages.value.length === 0) {
    const welcomeText = `${t('chat.welcome')}! ${t('chat.welcomeCapabilities')}:\n\n• ${t('chat.welcomeStructure')}\n• ${t('chat.welcomeImplementation')}\n• ${t('chat.welcomeLogic')}\n• ${t('chat.welcomeArchitecture')}\n\n${t('chat.askFirstQuestion')}`

    messages.value.push({
      role: 'assistant',
      text: welcomeText.replace('{project}', currentProject.value),
      timestamp: Date.now()
    })
  }
}

// 监听器和生命周期
watch(currentProject, (newProject, oldProject) => {
  if (newProject && newProject !== oldProject) {
    messages.value = []
    loadKnowledgeFiles()
    addWelcomeMessage()
    if (isOpen.value) {
      setTimeout(() => scrollToBottom(), 100)
    }
  }
})

// 键盘快捷键和生命周期
const handleKeydown = (event: KeyboardEvent) => {
  if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
    event.preventDefault()
    send()
  } else if (event.key === 'Escape' && isOpen.value) {
    event.preventDefault()
    closePanel()
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
  if (currentProject.value) {
    addWelcomeMessage()
    loadKnowledgeFiles()
  }
})
</script>

<style scoped>
/* 底部触发条 */
.chat-trigger {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 12px 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  z-index: 1000;
  box-shadow: 0 -2px 20px rgba(0, 0, 0, 0.15);
}

.chat-trigger:hover {
  background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%);
  transform: translateY(-2px);
  box-shadow: 0 -4px 25px rgba(0, 0, 0, 0.2);
}

.trigger-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  max-width: 1200px;
  margin: 0 auto;
}

.trigger-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.trigger-icon {
  font-size: 24px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(10px);
}

.trigger-info {
  display: flex;
  flex-direction: column;
}

.trigger-title {
  font-weight: 600;
  font-size: 16px;
}

.trigger-subtitle {
  font-size: 12px;
  opacity: 0.9;
  margin-top: 2px;
}

.trigger-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.message-count {
  background: rgba(255, 255, 255, 0.3);
  border-radius: 12px;
  padding: 4px 8px;
  font-size: 12px;
  font-weight: 600;
  backdrop-filter: blur(10px);
}

.trigger-arrow {
  font-size: 16px;
  transition: transform 0.3s ease;
}

.arrow-up {
  transform: rotate(180deg);
}

/* 聊天弹窗 */
.chat-modal {
  position: fixed;
  bottom: 80px;
  left: 50%;
  transform: translateX(-50%);
  width: 90%;
  max-width: 800px;
  height: 70vh;
  max-height: 600px;
  background: white;
  border-radius: 16px 16px 0 0;
  box-shadow: 0 -10px 50px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
  z-index: 1002;
  overflow: hidden;
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from {
    transform: translateX(-50%) translateY(100%);
    opacity: 0;
  }
  to {
    transform: translateX(-50%) translateY(0);
    opacity: 1;
  }
}

/* 遮罩层 */
.chat-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 1001;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* 头部样式调整 */
.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  background: white;
  border-bottom: 1px solid #e1e5e9;
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

/* 消息区域调整 */
.chat-messages {
  flex: 1;
  padding: 16px 20px;
  overflow-y: auto;
  scroll-behavior: smooth;
}

/* 底部输入区域调整 */
.chat-footer {
  border-top: 1px solid #e1e5e9;
  background: white;
  flex-shrink: 0;
}

.project-info {
  padding: 12px 20px;
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
  padding: 16px 20px;
  gap: 12px;
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
  padding: 8px 20px 16px;
  text-align: center;
}

.chat-tips small {
  color: #656d76;
  font-size: 12px;
}

/* 保留原有的消息气泡样式 */
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

/* 知识库相关样式保持不变 */
.knowledge-panel {
  background: white;
  border: 1px solid #d0d7de;
  border-radius: 8px;
  margin: 16px;
  padding: 0;
  max-height: 300px;
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

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.knowledge-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: #eef4ff;
  border: 1px solid #d0dfff;
  border-radius: 6px;
  font-size: 14px;
  color: #0969da;
  cursor: pointer;
  transition: all .2s ease;
}

.knowledge-btn:hover {
  background: #d0e2ff;
  border-color: #a6c7ff;
}

.knowledge-icon {
  font-size: 16px;
}

.knowledge-text {
  font-weight: 610;
  white-space: nowrap;
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

/* 响应式设计 */
@media (max-width: 768px) {
  .chat-modal {
    width: 95%;
    height: 80vh;
    max-height: none;
    bottom: 70px;
  }

  .trigger-content {
    padding: 0 10px;
  }

  .trigger-title {
    font-size: 14px;
  }

  .trigger-subtitle {
    font-size: 11px;
  }

  .content {
    max-width: 85%;
  }
}

/* 重新设计的底部触发条 */
.chat-trigger {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  width: 90%;
  max-width: 400px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  padding: 0;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  z-index: 1000;
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.1),
    0 2px 8px rgba(0, 0, 0, 0.05),
    inset 0 1px 0 rgba(255, 255, 255, 0.6);
}

.chat-trigger:hover {
  transform: translateX(-50%) translateY(-2px);
  box-shadow:
    0 12px 40px rgba(0, 0, 0, 0.15),
    0 4px 12px rgba(0, 0, 0, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.8);
  background: rgba(255, 255, 255, 0.98);
}

.chat-trigger.trigger-active {
  background: rgba(255, 255, 255, 0.98);
  border-color: rgba(9, 105, 218, 0.2);
  box-shadow:
    0 8px 32px rgba(9, 105, 218, 0.15),
    0 2px 8px rgba(9, 105, 218, 0.1);
}

.trigger-container {
  position: relative;
  overflow: hidden;
  border-radius: 16px;
}

.trigger-main {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  position: relative;
  z-index: 2;
}

/* 左侧内容 */
.trigger-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.trigger-icon-wrapper {
  position: relative;
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.trigger-icon {
  font-size: 18px;
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.1));
}

.online-indicator {
  position: absolute;
  top: -2px;
  right: -2px;
  width: 12px;
  height: 12px;
  background: #10b981;
  border: 2px solid white;
  border-radius: 50%;
  box-shadow: 0 2px 4px rgba(16, 185, 129, 0.3);
}

.trigger-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.trigger-title {
  font-weight: 700;
  font-size: 16px;
  color: #1f2937;
  letter-spacing: -0.01em;
}

.trigger-status {
  font-size: 13px;
  font-weight: 610;
  transition: color 0.3s ease;
}

.status-online {
  color: #10b981;
}

.status-offline {
  color: #6b7280;
}

/* 右侧内容 */
.trigger-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.message-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  background: rgba(9, 105, 218, 0.08);
  padding: 6px 10px;
  border-radius: 20px;
  transition: all 0.3s ease;
}

.message-count {
  font-weight: 700;
  font-size: 13px;
  color: #0969da;
  min-width: 16px;
  text-align: center;
}

.message-text {
  font-size: 12px;
  color: #0969da;
  font-weight: 610;
  white-space: nowrap;
}

.trigger-arrow {
  color: #6b7280;
  transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: rgba(107, 114, 128, 0.05);
}

.trigger-arrow:hover {
  background: rgba(107, 114, 128, 0.1);
  color: #374151;
}

.trigger-arrow.arrow-up {
  transform: rotate(180deg);
  color: #0969da;
  background: rgba(9, 105, 218, 0.1);
}

/* 进度条效果 */
.trigger-progress {
  position: absolute;
  bottom: 0;
  left: 0;
  height: 2px;
  background: linear-gradient(90deg, #667eea, #764ba2);
  border-radius: 0 0 16px 16px;
  transform: scaleX(0);
  transform-origin: left;
  transition: transform 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  z-index: 1;
}

.trigger-progress.progress-active {
  transform: scaleX(1);
}

/* 弹窗和遮罩层样式保持不变 */
.chat-modal {
  position: fixed;
  bottom: 100px;
  left: 50%;
  transform: translateX(-50%);
  width: 90%;
  max-width: 800px;
  height: 70vh;
  max-height: 600px;
  background: white;
  border-radius: 20px;
  box-shadow:
    0 20px 60px rgba(0, 0, 0, 0.2),
    0 0 0 1px rgba(255, 255, 255, 0.1) inset;
  display: flex;
  flex-direction: column;
  z-index: 1002;
  overflow: hidden;
  animation: modalSlideUp 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

@keyframes modalSlideUp {
  from {
    transform: translateX(-50%) translateY(100%);
    opacity: 0;
  }
  to {
    transform: translateX(-50%) translateY(0);
    opacity: 1;
  }
}

.chat-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  z-index: 1001;
  animation: overlayFadeIn 0.3s ease;
}

@keyframes overlayFadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .chat-trigger {
    bottom: 16px;
    width: calc(100% - 32px);
    max-width: none;
  }

  .trigger-main {
    padding: 14px 16px;
  }

  .trigger-icon-wrapper {
    width: 36px;
    height: 36px;
  }

  .trigger-icon {
    font-size: 16px;
  }

  .trigger-title {
    font-size: 15px;
  }

  .trigger-status {
    font-size: 12px;
  }

  .message-indicator {
    padding: 5px 8px;
  }

  .message-count, .message-text {
    font-size: 11px;
  }

  .chat-modal {
    bottom: 90px;
    width: calc(100% - 32px);
    height: 75vh;
    border-radius: 16px;
  }
}

@media (max-width: 480px) {
  .trigger-right {
    gap: 8px;
  }

  .message-text {
    display: none;
  }

  .message-indicator {
    padding: 6px 8px;
    border-radius: 50%;
    min-width: 32px;
    justify-content: center;
  }
}

/* 暗色主题支持 */
@media (prefers-color-scheme: dark) {
  .chat-trigger {
    background: rgba(31, 41, 55, 0.95);
    border-color: rgba(255, 255, 255, 0.1);
    box-shadow:
      0 8px 32px rgba(0, 0, 0, 0.3),
      0 2px 8px rgba(0, 0, 0, 0.2);
  }

  .chat-trigger:hover {
    background: rgba(31, 41, 55, 0.98);
    box-shadow:
      0 12px 40px rgba(0, 0, 0, 0.4),
      0 4px 12px rgba(0, 0, 0, 0.3);
  }

  .trigger-title {
    color: #f9fafb;
  }

  .trigger-status {
    color: #d1d5db;
  }

  .status-online {
    color: #34d399;
  }

  .status-offline {
    color: #9ca3af;
  }

  .trigger-arrow {
    color: #9ca3af;
    background: rgba(156, 163, 175, 0.1);
  }

  .trigger-arrow:hover {
    background: rgba(156, 163, 175, 0.2);
    color: #e5e7eb;
  }
}

/* 重新设计的底部触发条 - 加长版本 */
.chat-trigger {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  width: 90%;
  max-width: 600px; /* 增加最大宽度 */
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  padding: 0;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  z-index: 1000;
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.1),
    0 2px 8px rgba(0, 0, 0, 0.05),
    inset 0 1px 0 rgba(255, 255, 255, 0.6);
}

.chat-trigger:hover {
  transform: translateX(-50%) translateY(-2px);
  box-shadow:
    0 12px 40px rgba(0, 0, 0, 0.15),
    0 4px 12px rgba(0, 0, 0, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.8);
  background: rgba(255, 255, 255, 0.98);
}

.chat-trigger.trigger-active {
  background: rgba(255, 255, 255, 0.98);
  border-color: rgba(9, 105, 218, 0.2);
  box-shadow:
    0 8px 32px rgba(9, 105, 218, 0.15),
    0 2px 8px rgba(9, 105, 218, 0.1);
}

.trigger-container {
  position: relative;
  overflow: hidden;
  border-radius: 16px;
}

.trigger-main {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 24px; /* 增加内边距让条更长 */
  position: relative;
  z-index: 2;
}

/* 左侧内容 - 扩展布局 */
.trigger-left {
  display: flex;
  align-items: center;
  gap: 16px; /* 增加间距 */
  flex: 1;
}

.trigger-icon-wrapper {
  position: relative;
  width: 44px; /* 稍大一些的图标 */
  height: 44px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
  flex-shrink: 0;
}

.trigger-icon {
  font-size: 20px; /* 更大的图标 */
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.1));
}

.online-indicator {
  position: absolute;
  top: -2px;
  right: -2px;
  width: 12px;
  height: 12px;
  background: #10b981;
  border: 2px solid white;
  border-radius: 50%;
  box-shadow: 0 2px 4px rgba(16, 185, 129, 0.3);
}

.trigger-info {
  display: flex;
  flex-direction: column;
  gap: 4px; /* 增加间距 */
  min-width: 0;
  flex: 1;
}

.trigger-title {
  font-weight: 700;
  font-size: 17px; /* 稍大的字体 */
  color: #1f2937;
  letter-spacing: -0.01em;
}

.trigger-status {
  font-size: 14px; /* 稍大的状态文字 */
  font-weight: 610;
  transition: color 0.3s ease;
}

.status-online {
  color: #10b981;
}

.status-offline {
  color: #6b7280;
}

/* 右侧内容 - 扩展布局 */
.trigger-right {
  display: flex;
  align-items: center;
  gap: 16px; /* 增加间距 */
  flex-shrink: 0;
}

.message-indicator {
  display: flex;
  align-items: center;
  gap: 8px; /* 增加间距 */
  background: rgba(9, 105, 218, 0.08);
  padding: 8px 12px; /* 更大的内边距 */
  border-radius: 20px;
  transition: all 0.3s ease;
  min-width: 80px; /* 确保有足够宽度 */
  justify-content: center;
}

.message-count {
  font-weight: 700;
  font-size: 14px; /* 稍大的字体 */
  color: #0969da;
  min-width: 18px;
  text-align: center;
}

.message-text {
  font-size: 13px; /* 稍大的字体 */
  color: #0969da;
  font-weight: 610;
  white-space: nowrap;
}

.trigger-arrow {
  color: #6b7280;
  transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px; /* 更大的箭头区域 */
  height: 36px;
  border-radius: 10px; /* 更大的圆角 */
  background: rgba(107, 114, 128, 0.05);
  flex-shrink: 0;
}

.trigger-arrow:hover {
  background: rgba(107, 114, 128, 0.1);
  color: #374151;
}

.trigger-arrow.arrow-up {
  transform: rotate(180deg);
  color: #0969da;
  background: rgba(9, 105, 218, 0.1);
}

/* 进度条效果 */
.trigger-progress {
  position: absolute;
  bottom: 0;
  left: 0;
  height: 3px; /* 更粗的进度条 */
  background: linear-gradient(90deg, #667eea, #764ba2);
  border-radius: 0 0 16px 16px;
  transform: scaleX(0);
  transform-origin: left;
  transition: transform 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  z-index: 1;
}

.trigger-progress.progress-active {
  transform: scaleX(1);
}

/* 弹窗位置调整以适应更长的触发条 */
.chat-modal {
  position: fixed;
  bottom: 110px; /* 调整位置避免重叠 */
  left: 50%;
  transform: translateX(-50%);
  width: 90%;
  max-width: 900px;
  height: 85vh;
  max-height: 1000px;
  background: white;
  border-radius: 20px;
  box-shadow:
    0 20px 60px rgba(0, 0, 0, 0.2),
    0 0 0 1px rgba(255, 255, 255, 0.1) inset;
  display: flex;
  flex-direction: column;
  z-index: 1002;
  overflow: hidden;
  animation: modalSlideUp 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .chat-trigger {
    bottom: 16px;
    width: calc(100% - 32px);
    max-width: none;
  }

  .trigger-main {
    padding: 16px 20px; /* 移动端保持合适的内边距 */
  }

  .trigger-icon-wrapper {
    width: 40px;
    height: 40px;
  }

  .trigger-icon {
    font-size: 18px;
  }

  .trigger-title {
    font-size: 16px;
  }

  .trigger-status {
    font-size: 13px;
  }

  .message-indicator {
    padding: 7px 10px;
    min-width: 70px;
  }

  .message-count, .message-text {
    font-size: 12px;
  }

  .chat-modal {
    bottom: 100px; /* 移动端调整位置 */
    width: calc(100% - 32px);
    height: 75vh;
    border-radius: 16px;
  }
}

@media (max-width: 480px) {
  .trigger-main {
    padding: 14px 16px;
  }

  .trigger-left {
    gap: 12px;
  }

  .trigger-icon-wrapper {
    width: 36px;
    height: 36px;
  }

  .trigger-right {
    gap: 12px;
  }

  .message-text {
    display: block; /* 小屏幕也显示文字 */
  }

  .message-indicator {
    min-width: auto;
    padding: 6px 10px;
  }
}

/* 超宽屏幕支持 */
@media (min-width: 1200px) {
  .chat-trigger {
    max-width: 550px; /* 在宽屏上更宽 */
  }
}

/* 暗色主题支持 */
@media (prefers-color-scheme: dark) {
  .chat-trigger {
    background: rgba(31, 41, 55, 0.95);
    border-color: rgba(255, 255, 255, 0.1);
    box-shadow:
      0 8px 32px rgba(0, 0, 0, 0.3),
      0 2px 8px rgba(0, 0, 0, 0.2);
  }

  .chat-trigger:hover {
    background: rgba(31, 41, 55, 0.98);
    box-shadow:
      0 12px 40px rgba(0, 0, 0, 0.4),
      0 4px 12px rgba(0, 0, 0, 0.3);
  }

  .trigger-title {
    color: #f9fafb;
  }

  .trigger-status {
    color: #d1d5db;
  }

  .status-online {
    color: #34d399;
  }

  .status-offline {
    color: #9ca3af;
  }

  .trigger-arrow {
    color: #9ca3af;
    background: rgba(156, 163, 175, 0.1);
  }

  .trigger-arrow:hover {
    background: rgba(156, 163, 175, 0.2);
    color: #e5e7eb;
  }
}


</style>
