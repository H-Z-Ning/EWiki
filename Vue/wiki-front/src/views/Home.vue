<template>
  <div class="home">
    <!-- 顶部 Hero -->
    <section class="hero">
      <div class="hero-header">
        <h1 class="title">{{ $t('home.title') }}</h1>
        <LanguageSwitcher />
      </div>
      <p class="subtitle">{{ $t('home.subtitle') }}</p>
    </section>

    <!-- 导入区域 -->
    <section class="glass import-card">
      <h3>{{ $t('home.importProject') }}</h3>

      <!-- 选项卡 -->
      <div class="tab-buttons">
        <button
          class="tab-button"
          :class="{ active: activeTab === 'upload' }"
          @click="activeTab = 'upload'"
        >
          {{ $t('home.fileUpload') }}
        </button>
        <button
          class="tab-button"
          :class="{ active: activeTab === 'local' }"
          @click="activeTab = 'local'"
        >
          {{ $t('home.localPath') }}
        </button>
      </div>

      <!-- Wiki 语言选择 -->
      <div class="language-selection compact">
        <div class="language-header">
          <span class="language-icon">🌐</span>
          <span class="language-title">{{ $t('home.wikiLanguage') }}</span>
          <span class="language-hint">{{ $t('home.languageHint') }}</span>
        </div>
        <div class="language-options">
          <div
            class="lang-card"
            :class="{ active: wikiLanguage === 'en' }"
            @click="wikiLanguage = 'en'"
          >
            <div class="lang-flag">🇺🇸</div>
            <div class="lang-info">
              <div class="lang-name">{{ $t('home.english') }}</div>
              <div class="lang-desc">{{ $t('home.endoclang') }}</div>
            </div>
            <div class="lang-check">
              <div class="check-icon" v-if="wikiLanguage === 'en'">✓</div>
            </div>
          </div>
          <div
            class="lang-card"
            :class="{ active: wikiLanguage === 'zh' }"
            @click="wikiLanguage = 'zh'"
          >
            <div class="lang-flag">🇨🇳</div>
            <div class="lang-info">
              <div class="lang-name">{{ $t('home.chinese') }}</div>
              <div class="lang-desc">{{ $t('home.zhdoclang') }}</div>
            </div>
            <div class="lang-check">
              <div class="check-icon" v-if="wikiLanguage === 'zh'">✓</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 文件上传 -->
      <div v-if="activeTab === 'upload'" class="upload-box">
        <div class="upload-area" @click="triggerFileInput" @drop="handleDrop" @dragover.prevent>
          <input
            type="file"
            ref="fileInput"
            @change="handleFileSelect"
            style="display: none"
            accept=".zip,.rar,.7z"
          />
          <div class="upload-content">
            <span class="upload-icon">📦</span>
            <p class="upload-text">{{ $t('home.dragDrop') }}</p>
            <p class="upload-hint">{{ $t('home.supportedFormats') }}</p>
          </div>
        </div>

        <!-- 文件信息显示 -->
        <div v-if="selectedFile" class="file-info">
          <div class="file-details">
            <span class="file-name">{{ selectedFile.name }}</span>
            <span class="file-size">({{ formatFileSize(selectedFile.size) }})</span>
          </div>
          <button class="remove-btn" @click="clearFile">×</button>
        </div>

        <button
          class="primary upload-btn"
          @click="doUpload"
          :disabled="running || !selectedFile"
        >
          <span v-if="!running">{{ $t('home.uploadGenerate') }}</span>
          <span v-else>{{ $t('common.generating') }}</span>
        </button>
      </div>

      <!-- 本地路径输入 -->
      <div v-if="activeTab === 'local'" class="input-box">
        <input
          v-model="path"
          :placeholder="$t('home.pathPlaceholder')"
          @keyup.enter="doImport"
        />
        <button class="primary" @click="doImport" :disabled="running">
          <span v-if="!running">{{ $t('home.generateWiki') }}</span>
          <span v-else>{{ $t('common.generating') }}</span>
        </button>
      </div>
    </section>

    <!-- 已有项目 -->
    <section class="glass projects-card">
      <div class="projects-header">
        <h3>{{ $t('home.existingProjects') }}</h3>
        <div class="projects-count" v-if="projects.length > 0">
          {{ projects.length }} {{ $t('common.projects') }}
        </div>
      </div>
      <div v-if="projects.length === 0" class="empty">
        {{ $t('home.noProjects') }}
      </div>
      <div class="cards">
        <div
          class="project-card"
          v-for="project in projects"
          :key="project.name"
        >
          <div class="card-inner" @click="goWiki(project.name)">
            <span class="icon">📁</span>
            <span class="name">{{ project.name }}</span>
            <div class="card-actions">
              <span class="arrow"></span>
              <button
                class="delete-btn"
                @click.stop="confirmDelete(project.name)"
                :title="$t('common.delete')"
              >
                🗑️
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 进度条模态框 -->
    <div v-if="showProgress" class="progress-modal-overlay">
      <div class="progress-modal-content">
        <div class="progress-modal-header">
          <h3>{{ $t('home.generatingWiki') }}</h3>
        </div>
        <div class="progress-modal-body">
          <!-- 进度条 -->
          <div class="progress-container">
            <div class="progress-bar">
              <div 
                class="progress-fill" 
                :style="{ width: progress + '%' }"
              ></div>
            </div>
            <div class="progress-info">
              <span class="progress-percentage">{{ progress }}%</span>
              <span class="progress-message">{{ progressMessage }}</span>
            </div>
          </div>

          <!-- 详细进度信息 -->
          <div v-if="progressDetails" class="progress-details">
            <div v-if="progressDetails.current_page && progressDetails.total_pages">
              <p>正在生成页面: {{ progressDetails.current_page }}/{{ progressDetails.total_pages }}</p>
            </div>
          </div>

          <!-- 完成信息 -->
          <div v-if="progressStage === 'completed'" class="success-message">
            <p>✅ {{ progressMessage }}</p>
            <p class="redirect-hint">即将跳转到项目页面...</p>
          </div>

          <!-- 错误信息 -->
          <div v-if="progressStage === 'error'" class="error-message">
            <p>❌ {{ progressMessage }}</p>
          </div>
        </div>
        <div class="progress-modal-actions">
          <button 
            v-if="progressStage === 'error' || progressStage === 'completed'" 
            class="btn-primary" 
            @click="closeProgress"
          >
            {{ progressStage === 'completed' ? '立即查看' : $t('common.close') }}
          </button>
          <button 
            v-else 
            class="btn-secondary" 
            @click="cancelGeneration"
            :disabled="cancelling"
          >
            {{ cancelling ? $t('common.cancelling') : $t('common.cancel') }}
          </button>
        </div>
      </div>
    </div>

    <!-- 删除确认对话框 -->
    <div v-if="showDeleteConfirm" class="modal-overlay" @click="cancelDelete">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>{{ $t('home.deleteConfirm') }}</h3>
        </div>
        <div class="modal-body">
          <p>{{ $t('home.deleteProjectConfirm') }} <strong>"{{ projectToDelete }}"</strong>？</p>
          <p class="warning-text">{{ $t('home.deleteWarning') }}</p>
        </div>
        <div class="modal-actions">
          <button class="btn-secondary" @click="cancelDelete">{{ $t('common.cancel') }}</button>
          <button class="btn-danger" @click="doDelete" :disabled="deleting">
            {{ deleting ? $t('common.deleting') : $t('home.confirmDelete') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
  import { ref, onMounted, onUnmounted } from 'vue'
  import { useRouter } from 'vue-router'
  import { useI18n } from 'vue-i18n'
  import axios from 'axios'
  import LanguageSwitcher from '@/components/LanguageSwitcher.vue'
  
  const { t } = useI18n()
  
  interface Project {
    name: string;
  }
  
  interface ProgressData {
    stage: string;
    progress: number;
    message: string;
    current_page?: number;
    total_pages?: number;
  }
  
  /* 数据 */
  const router = useRouter()
  const path = ref('')
  const running = ref(false)
  const projects = ref<Project[]>([])
  const activeTab = ref('upload')
  const selectedFile = ref<File | null>(null)
  const fileInput = ref<HTMLInputElement | null>(null)
  const wikiLanguage = ref('en')
  
  // 进度相关状态
  const showProgress = ref(false)
  const progress = ref(0)
  const progressMessage = ref('')
  const progressStage = ref('')
  const progressDetails = ref<any>(null)
  const currentProject = ref('')
  const websocket = ref<WebSocket | null>(null)
  const cancelling = ref(false)
  const completedProject = ref('') // 新增：存储完成的项目名
  
  // 删除相关状态
  const showDeleteConfirm = ref(false)
  const projectToDelete = ref('')
  const deleting = ref(false)
  
  /* 方法 */
  const loadList = async () => {
    try {
      const response = await axios.get('/api/projects')
      projects.value = Array.isArray(response.data)
        ? response.data.map((name: string) => ({ name }))
        : response.data
    } catch (error) {
      console.error(t('errors.loadFailed'), error)
      projects.value = []
    }
  }
  
  const setupWebSocket = (project: string) => {
    return new Promise((resolve, reject) => {
      // 获取WebSocket URL
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const host = window.location.host
      const wsUrl = `${protocol}//${host}/ws/progress/${project}`
      
      console.log('Connecting to WebSocket:', wsUrl)
      
      websocket.value = new WebSocket(wsUrl)
      
      websocket.value.onopen = () => {
        console.log('WebSocket connected for progress updates')
        resolve(true)
      }
      
      websocket.value.onmessage = (event) => {
        try {
          const data: ProgressData = JSON.parse(event.data)
          console.log('Received progress:', data)
          handleProgressUpdate(data)
        } catch (error) {
          console.error('Failed to parse progress data:', error)
        }
      }
      
      websocket.value.onerror = (error) => {
        console.error('WebSocket error:', error)
        reject(error)
      }
      
      websocket.value.onclose = () => {
        console.log('WebSocket disconnected')
      }
    })
  }
  
  const handleProgressUpdate = (data: ProgressData) => {
    progress.value = data.progress
    progressMessage.value = data.message
    progressStage.value = data.stage
    
    // 更新详细进度信息
    if (data.current_page && data.total_pages) {
      progressDetails.value = {
        current_page: data.current_page,
        total_pages: data.total_pages
      }
    }
    
    // 处理完成状态
    if (data.stage === 'completed') {
      running.value = false
      completedProject.value = currentProject.value
      
      // 完成后延迟跳转，让用户看到完成消息
      setTimeout(() => {
        if (showProgress.value) {
          closeProgress()
          // 确保项目名正确后再跳转
          const projectToNavigate = completedProject.value || currentProject.value
          if (projectToNavigate) {
            console.log('跳转到项目:', projectToNavigate)
            router.push(`/wiki/${projectToNavigate}`)
          }
        }
      }, 1000) // 1秒后跳转，让用户看到完成状态
    }
    
    // 处理错误状态
    if (data.stage === 'error') {
      running.value = false
      // 错误时不自动关闭，让用户看到错误信息
    }
  }
  
  const closeProgress = () => {
    showProgress.value = false
    progress.value = 0
    progressMessage.value = ''
    progressStage.value = ''
    progressDetails.value = null
    currentProject.value = ''
    completedProject.value = ''
    
    if (websocket.value) {
      websocket.value.close()
      websocket.value = null
    }
  }
  
  const cancelGeneration = async () => {
    cancelling.value = true
    try {
      // 这里可以添加取消生成的API调用
      // await axios.post(`/api/projects/${currentProject.value}/cancel`)
      
      // 直接关闭进度显示
      closeProgress()
      running.value = false
    } catch (error) {
      console.error('取消生成失败:', error)
    } finally {
      cancelling.value = false
    }
  }
  
  const doImport = async () => {
    if (!path.value.trim()) return
    running.value = true
    
    try {
      // 从路径中提取项目名
      const pathParts = path.value.trim().split(/[\\/]/)
      const projectName = pathParts[pathParts.length - 1] || 'untitled'
      currentProject.value = projectName
      
      // 显示进度条
      showProgress.value = true
      progress.value = 0
      progressMessage.value = '准备开始...'
      
      // 设置WebSocket连接
      await setupWebSocket(projectName)
      
      const { data } = await axios.post('/api/import', {
        path: path.value.trim(),
        language: wikiLanguage.value
      })
      
      console.log('导入API返回:', data)
      
      // 更新项目名为API返回的项目名（可能和路径提取的不同）
      if (data.project && data.project !== currentProject.value) {
        currentProject.value = data.project
        console.log('更新项目名为:', data.project)
      }
      
      await loadList()
      
      // 如果WebSocket没有收到完成消息，设置超时处理
      const timeout = setTimeout(() => {
        if (showProgress.value && progressStage.value !== 'completed' && progressStage.value !== 'error') {
          console.log('WebSocket超时，强制完成')
          closeProgress()
          const finalProject = data.project || currentProject.value
          if (finalProject) {
            router.push(`/wiki/${finalProject}`)
          }
        }
      }, 120000) // 2分钟超时
      
      // 监听完成状态来清除超时
      const checkComplete = setInterval(() => {
        if (!showProgress.value || progressStage.value === 'completed' || progressStage.value === 'error') {
          clearTimeout(timeout)
          clearInterval(checkComplete)
        }
      }, 1000)
      
    } catch (error: any) {
      console.error(t('errors.importFailed'), error)
      alert(t('errors.importFailed'))
      closeProgress()
      running.value = false
    }
  }
  
  const doUpload = async () => {
    if (!selectedFile.value) return
  
    running.value = true
    
    try {
      const projectName = selectedFile.value.name.replace(/\.[^/.]+$/, "") // 移除扩展名
      currentProject.value = projectName
      
      // 显示进度条
      showProgress.value = true
      progress.value = 0
      progressMessage.value = '准备开始...'
      
      // 设置WebSocket连接
      await setupWebSocket(projectName)
      
      const formData = new FormData()
      formData.append('file', selectedFile.value)
      formData.append('language', wikiLanguage.value)
  
      const { data } = await axios.post('/api/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
  
      console.log('上传API返回:', data)
      
      // 更新项目名为API返回的项目名
      if (data.project && data.project !== currentProject.value) {
        currentProject.value = data.project
        console.log('更新项目名为:', data.project)
      }
      
      await loadList()
      
      // 如果WebSocket没有收到完成消息，设置超时处理
      const timeout = setTimeout(() => {
        if (showProgress.value && progressStage.value !== 'completed' && progressStage.value !== 'error') {
          console.log('WebSocket超时，强制完成')
          closeProgress()
          const finalProject = data.project || currentProject.value
          if (finalProject) {
            router.push(`/wiki/${finalProject}`)
          }
        }
      }, 120000) // 2分钟超时
      
      // 监听完成状态来清除超时
      const checkComplete = setInterval(() => {
        if (!showProgress.value || progressStage.value === 'completed' || progressStage.value === 'error') {
          clearTimeout(timeout)
          clearInterval(checkComplete)
        }
      }, 1000)
      
    } catch (error: any) {
      console.error(t('errors.uploadFailed'), error)
      alert(`${t('errors.uploadFailed')}: ${error.response?.data?.detail || t('errors.requestFailed')}`)
      closeProgress()
      running.value = false
    }
  }
  
  // 其他方法保持不变...
  const triggerFileInput = () => {
    fileInput.value?.click()
  }
  
  const handleFileSelect = (event: Event) => {
    const target = event.target as HTMLInputElement
    if (target.files && target.files[0]) {
      const file = target.files[0]
      if (isValidArchiveFile(file)) {
        selectedFile.value = file
      } else {
        alert(t('errors.fileTypeError'))
        clearFile()
      }
    }
  }
  
  const handleDrop = (event: DragEvent) => {
    event.preventDefault()
    if (event.dataTransfer?.files && event.dataTransfer.files[0]) {
      const file = event.dataTransfer.files[0]
      if (isValidArchiveFile(file)) {
        selectedFile.value = file
      } else {
        alert(t('errors.fileTypeError'))
        clearFile()
      }
    }
  }
  
  const isValidArchiveFile = (file: File): boolean => {
    const allowedTypes = [
      'application/zip',
      'application/x-zip-compressed',
      'application/x-rar-compressed',
      'application/x-7z-compressed'
    ]
    const allowedExtensions = ['.zip', '.rar', '.7z']
  
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase()
  
    return allowedTypes.includes(file.type) ||
           (fileExtension && allowedExtensions.includes(fileExtension))
  }
  
  const clearFile = () => {
    selectedFile.value = null
    if (fileInput.value) {
      fileInput.value.value = ''
    }
  }
  
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }
  
  const goWiki = (p: string) => {
    console.log('跳转到项目:', p)
    router.push(`/wiki/${p}`)
  }
  
  // 删除项目相关方法
  const confirmDelete = (projectName: string) => {
    projectToDelete.value = projectName
    showDeleteConfirm.value = true
  }
  
  const cancelDelete = () => {
    showDeleteConfirm.value = false
    projectToDelete.value = ''
    deleting.value = false
  }
  
  const doDelete = async () => {
    if (!projectToDelete.value) return
  
    deleting.value = true
    try {
      await axios.delete(`/api/projects/${projectToDelete.value}`)
      await loadList()
      cancelDelete()
    } catch (error: any) {
      console.error(t('errors.deleteFailed'), error)
      alert(`${t('errors.deleteFailed')}: ${error.response?.data?.detail || t('errors.requestFailed')}`)
      cancelDelete()
    }
  }
  
  /* 生命周期 */
  onMounted(() => {
    loadList()
  })
  
  onUnmounted(() => {
    if (websocket.value) {
      websocket.value.close()
    }
  })
  </script>

<style scoped>
/* 基础重置 */
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

.home {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 64px 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 40px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  line-height: 1.5;
}

/* Hero 区域 */
.hero {
  text-align: center;
  color: #fff;
  margin-bottom: 20px;
}

.title {
  font-size: 48px;
  font-weight: 700;
  letter-spacing: 2px;
  margin: 0 0 16px 0;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.subtitle {
  font-size: 18px;
  opacity: 0.9;
  margin: 0;
  font-weight: 400;
}

/* Glass 卡片 */
.glass {
  width: 100%;
  max-width: 680px;
  background: rgba(255, 255, 255, 0.18);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  padding: 32px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  color: #fff;
}

.glass h3 {
  margin: 0 0 20px 0;
  font-size: 20px;
  font-weight: 600;
}

/* 项目头部 */
.projects-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.projects-count {
  font-size: 14px;
  opacity: 0.7;
  background: rgba(255, 255, 255, 0.1);
  padding: 4px 12px;
  border-radius: 12px;
}

/* 输入框区域 */
.input-box {
  display: flex;
  gap: 12px;
  width: 100%;
  margin-top: 12px;
}

.input-box input {
  flex: 1;
  padding: 12px 16px;
  border: none;
  border-radius: 8px;
  font-size: 15px;
  background: rgba(255, 255, 255, 0.9);
  color: #333;
  font-family: inherit;
  outline: none;
  transition: background 0.2s;
}

.input-box input:focus {
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.3);
}

.input-box input::placeholder {
  color: #666;
}

/* 按钮样式 */
.primary {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  background: #6366f1;
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  font-family: inherit;
  white-space: nowrap;
}

.primary:hover:not(:disabled) {
  background: #4f46e5;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(79, 70, 229, 0.4);
}

.primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

/* 项目卡片区域 */
.cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
  margin-top: 16px;
}

.project-card {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  overflow: hidden;
}

.project-card:hover {
  background: rgba(255, 255, 255, 0.25);
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
}

.card-inner {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
}

.icon {
  font-size: 24px;
  flex-shrink: 0;
}

.name {
  flex: 1;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.arrow {
  opacity: 0.6;
  flex-shrink: 0;
}

.delete-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: all 0.2s;
  opacity: 0.7;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
}

.delete-btn:hover {
  opacity: 1;
  background: rgba(255, 255, 255, 0.1);
  transform: scale(1.1);
}

/* 空状态 */
.empty {
  text-align: center;
  opacity: 0.7;
  font-size: 15px;
  padding: 40px 20px;
}

/* 选项卡样式 */
.tab-buttons {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 4px;
}

.tab-button {
  flex: 1;
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: rgba(255, 255, 255, 0.7);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  font-family: inherit;
}

.tab-button.active {
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
}

.tab-button:hover:not(.active) {
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.9);
}

/* 上传区域样式 */
.upload-box {
  display: flex;
  flex-direction: column;
  margin-top: 20px;
  gap: 16px;
}

.upload-area {
  border: 2px dashed rgba(255, 255, 255, 0.3);
  border-radius: 12px;
  padding: 40px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  background: rgba(255, 255, 255, 0.05);
}

.upload-area:hover {
  border-color: rgba(255, 255, 255, 0.5);
  background: rgba(255, 255, 255, 0.08);
}

.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.upload-icon {
  font-size: 32px;
  opacity: 0.7;
}

.upload-text {
  margin: 0;
  font-size: 16px;
  font-weight: 500;
  color: #fff;
}

.upload-hint {
  margin: 0;
  font-size: 14px;
  opacity: 0.7;
  color: #fff;
}

/* 文件信息样式 */
.file-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 12px 16px;
  margin-top: 8px;
}

.file-details {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.file-name {
  font-weight: 500;
  color: #fff;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-size {
  opacity: 0.7;
  font-size: 14px;
  flex-shrink: 0;
}

.remove-btn {
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.7);
  font-size: 20px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: all 0.2s;
  font-family: inherit;
  line-height: 1;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.remove-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.upload-btn {
  align-self: flex-end;
  margin-top: 8px;
}

/* 模态框样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal-content {
  background: white;
  border-radius: 16px;
  padding: 0;
  max-width: 400px;
  width: 100%;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  color: #333;
  overflow: hidden;
}

.modal-header {
  padding: 24px 24px 0;
}

.modal-header h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #1f2937;
}

.modal-body {
  padding: 20px 24px;
}

.modal-body p {
  margin: 0 0 12px 0;
  line-height: 1.5;
}

.warning-text {
  color: #dc2626;
  font-weight: 500;
  font-size: 14px;
}

.modal-actions {
  padding: 16px 24px 24px;
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.btn-secondary {
  padding: 10px 20px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  background: white;
  color: #374151;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  font-family: inherit;
}

.btn-secondary:hover {
  background: #f9fafb;
  border-color: #9ca3af;
}

.btn-danger {
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  background: #dc2626;
  color: white;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  font-family: inherit;
}

.btn-danger:hover:not(:disabled) {
  background: #b91c1c;
  transform: translateY(-1px);
}

.btn-danger:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

/* 响应式调整 */
@media (max-width: 600px) {
  .home {
    padding: 40px 16px;
    gap: 30px;
  }

  .title {
    font-size: 36px;
  }

  .subtitle {
    font-size: 16px;
  }

  .glass {
    padding: 24px;
  }

  .input-box {
    flex-direction: column;
  }

  .tab-buttons {
    flex-direction: column;
  }

  .upload-area {
    padding: 30px 15px;
  }

  .upload-text {
    font-size: 14px;
  }

  .upload-hint {
    font-size: 12px;
  }

  .cards {
    grid-template-columns: 1fr;
  }

  .file-details {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }

  .file-name {
    font-size: 14px;
  }

  .file-size {
    font-size: 12px;
  }

  .projects-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .modal-content {
    margin: 20px;
  }

  .modal-actions {
    flex-direction: column;
  }
}

/* 大屏幕优化 */
@media (min-width: 1200px) {
  .home {
    padding: 80px 24px;
  }

  .glass {
    max-width: 800px;
  }
}

/* 加载状态动画 */
@keyframes pulse {
  0% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
  100% {
    opacity: 1;
  }
}

.primary:disabled span {
  animation: pulse 1.5s ease-in-out infinite;
}
.hero-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
  margin-bottom: 16px;
}

.title {
  margin: 0;
}

/* ==================== 优化的语言选择样式 - 降低高度 ==================== */
.language-selection {
  margin-top: 20px;
  padding: 10px 14px; /* 进一步减少内边距 */
  background: rgba(255, 255, 255, 0.08);
  border-radius: 10px; /* 稍微减小圆角 */
  border: 1px solid rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(10px);
}

/* 紧凑版本 */
.language-selection.compact {
  padding: 12px 16px;
}

.language-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.language-icon {
  font-size: 18px;
  opacity: 0.9;
}

.language-title {
  font-weight: 600;
  font-size: 15px;
  color: #fff;
}

.language-hint {
  font-size: 11px;
  opacity: 0.7;
  color: rgba(255, 255, 255, 0.8);
  margin-left: auto;
}

.language-options {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.lang-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.05);
  border: 2px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.lang-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
  transition: left 0.5s;
}

.lang-card:hover::before {
  left: 100%;
}

.lang-card:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.3);
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.lang-card.active {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(139, 92, 246, 0.2));
  border-color: #6366f1;
  box-shadow: 0 8px 25px rgba(99, 102, 241, 0.3);
}

.lang-flag {
  font-size: 20px;
  flex-shrink: 0;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
}

.lang-info {
  flex: 1;
  min-width: 0;
}

.lang-name {
  font-weight: 600;
  font-size: 13px;
  color: #fff;
  margin-bottom: 2px;
}

.lang-desc {
  font-size: 11px;
  opacity: 0.8;
  color: rgba(255, 255, 255, 0.9);
}

.lang-check {
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.check-icon {
  width: 14px;
  height: 14px;
  background: #10b981;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 9px;
  font-weight: bold;
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.4);
  animation: checkPop 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes checkPop {
  0% {
    transform: scale(0);
    opacity: 0;
  }
  50% {
    transform: scale(1.2);
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

/* 响应式调整 */
@media (max-width: 600px) {
  .language-options {
    grid-template-columns: 1fr;
  }

  .language-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 6px;
  }

  .language-hint {
    margin-left: 0;
    font-size: 10px;
  }

  .lang-card {
    padding: 10px;
  }
}

@media (min-width: 768px) {
  .language-options {
    gap: 12px;
  }

  .lang-card {
    padding: 14px;
  }
}
/* ==================== 进一步降低高度的语言选择样式 ==================== */
.language-selection {
  margin-top: 20px;
  padding: 10px 14px; /* 进一步减少内边距 */
  background: rgba(255, 255, 255, 0.08);
  border-radius: 10px; /* 稍微减小圆角 */
  border: 1px solid rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(10px);
}

.language-header {
  display: flex;
  align-items: center;
  gap: 6px; /* 减少间距 */
  margin-bottom: 10px; /* 减少底部间距 */
}

.language-icon {
  font-size: 16px; /* 进一步缩小图标 */
  opacity: 0.9;
}

.language-title {
  font-weight: 600;
  font-size: 14px; /* 进一步缩小字体 */
  color: #fff;
}

.language-hint {
  font-size: 10px; /* 进一步缩小提示文字 */
  opacity: 0.7;
  color: rgba(255, 255, 255, 0.8);
  margin-left: auto;
}

.language-options {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px; /* 减少选项间距 */
}

.lang-card {
  display: flex;
  align-items: center;
  gap: 8px; /* 减少内部元素间距 */
  padding: 10px; /* 进一步减少内边距 */
  background: rgba(255, 255, 255, 0.05);
  border: 2px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px; /* 减小圆角 */
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.lang-flag {
  font-size: 18px; /* 进一步缩小国旗图标 */
  flex-shrink: 0;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
}

.lang-info {
  flex: 1;
  min-width: 0;
}

.lang-name {
  font-weight: 600;
  font-size: 12px; /* 进一步缩小字体 */
  color: #fff;
  margin-bottom: 1px; /* 减少底部间距 */
}

.lang-desc {
  font-size: 10px; /* 进一步缩小描述文字 */
  opacity: 0.8;
  color: rgba(255, 255, 255, 0.9);
}

.lang-check {
  width: 16px; /* 进一步缩小勾选框 */
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.check-icon {
  width: 12px; /* 进一步缩小勾选图标 */
  height: 12px;
  background: #10b981;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 8px; /* 进一步缩小勾号 */
  font-weight: bold;
  box-shadow: 0 2px 6px rgba(16, 185, 129, 0.4);
  animation: checkPop 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* 移动端响应式调整 */
@media (max-width: 600px) {
  .language-selection {
    padding: 8px 12px; /* 移动端进一步减少内边距 */
  }
  
  .language-header {
    gap: 4px;
    margin-bottom: 8px;
  }
  
  .lang-card {
    padding: 8px; /* 移动端进一步减少内边距 */
    gap: 6px;
  }
}

@media (min-width: 768px) {
  .language-options {
    gap: 10px; /* 桌面端保持适当间距 */
  }
  
  .lang-card {
    padding: 12px; /* 桌面端保持适当内边距 */
  }
}
/* 上传区域样式 - 降低高度版本 */
.upload-box {
  display: flex;
  flex-direction: column;
  gap: 12px; /* 减少整体间距 */
}

.upload-area {
  border: 2px dashed rgba(255, 255, 255, 0.3);
  border-radius: 10px; /* 稍微减小圆角 */
  padding: 24px 16px; /* 大幅减少内边距，特别是上下内边距 */
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  background: rgba(255, 255, 255, 0.05);
  min-height: auto; /* 确保没有最小高度限制 */
}

.upload-area:hover {
  border-color: rgba(255, 255, 255, 0.5);
  background: rgba(255, 255, 255, 0.08);
}

.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px; /* 减少内容间距 */
}

.upload-icon {
  font-size: 24px; /* 缩小上传图标 */
  opacity: 0.7;
  margin-bottom: 2px; /* 可选：添加一点底部间距 */
}

.upload-text {
  margin: 0;
  font-size: 14px; /* 缩小文字 */
  font-weight: 500;
  color: #fff;
  line-height: 1.3; /* 减少行高 */
}

.upload-hint {
  margin: 0;
  font-size: 12px; /* 缩小提示文字 */
  opacity: 0.7;
  color: #fff;
  line-height: 1.2; /* 减少行高 */
}

/* 文件信息样式 - 如果需要也可以降低高度 */
.file-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 6px; /* 减小圆角 */
  padding: 10px 12px; /* 减少内边距 */
  margin-top: 4px; /* 减少顶部间距 */
}

.file-details {
  display: flex;
  align-items: center;
  gap: 6px; /* 减少元素间距 */
  flex: 1;
  min-width: 0;
}

.file-name {
  font-weight: 500;
  font-size: 13px; /* 稍微缩小文件名 */
  color: #fff;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-size {
  opacity: 0.7;
  font-size: 12px; /* 缩小文件大小文字 */
  flex-shrink: 0;
}

.remove-btn {
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.7);
  font-size: 18px; /* 稍微缩小删除按钮 */
  cursor: pointer;
  padding: 3px 6px; /* 减少内边距 */
  border-radius: 4px;
  transition: all 0.2s;
  font-family: inherit;
  line-height: 1;
  width: 28px; /* 缩小按钮尺寸 */
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.upload-btn {
  align-self: flex-end;
  margin-top: 4px; /* 减少顶部间距 */
  padding: 10px 20px; /* 如果需要也可以缩小按钮 */
  font-size: 14px; /* 缩小按钮文字 */
}

/* 移动端响应式调整 */
@media (max-width: 600px) {
  .upload-area {
    padding: 20px 12px; /* 移动端进一步减少内边距 */
  }
  
  .upload-icon {
    font-size: 20px; /* 移动端进一步缩小图标 */
  }
  
  .upload-text {
    font-size: 13px; /* 移动端进一步缩小文字 */
  }
  
  .upload-hint {
    font-size: 11px; /* 移动端进一步缩小提示 */
  }
  
  .file-info {
    padding: 8px 10px; /* 移动端进一步减少内边距 */
  }
  
  .upload-btn {
    padding: 8px 16px; /* 移动端缩小按钮 */
    font-size: 13px;
  }
}
/* Hero 区域 - 降低高度版本 */
.hero {
  text-align: center;
  color: #fff;
  margin-bottom: 16px; /* 减少底部外边距 */
  padding: 0; /* 移除内边距 */
}

.hero-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px; /* 减少元素间距 */
  margin-bottom: 12px; /* 减少底部间距 */
}

.title {
  font-size: 36px; /* 大幅缩小标题字体 */
  font-weight: 700;
  letter-spacing: 1px; /* 减少字间距 */
  margin: 0;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  line-height: 1.2; /* 减少行高 */
}

.subtitle {
  font-size: 15px; /* 缩小副标题字体 */
  opacity: 0.9;
  margin: 0;
  font-weight: 400;
  line-height: 1.3; /* 减少行高 */
}

/* 移动端响应式调整 */
@media (max-width: 600px) {
  .hero {
    margin-bottom: 12px; /* 移动端进一步减少底部间距 */
  }
  
  .hero-header {
    gap: 12px; /* 移动端进一步减少间距 */
    margin-bottom: 8px; /* 移动端进一步减少底部间距 */
    flex-direction: column; /* 可选：改为垂直布局节省空间 */
  }
  
  .title {
    font-size: 28px; /* 移动端进一步缩小标题 */
    letter-spacing: 0.5px;
    line-height: 1.1;
  }
  
  .subtitle {
    font-size: 13px; /* 移动端进一步缩小副标题 */
    line-height: 1.2;
  }
}

/* 如果需要更紧凑，可以使用这个版本 */
/*
.hero {
  text-align: center;
  color: #fff;
  margin-bottom: 12px;
}

.hero-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 8px;
}

.title {
  font-size: 32px;
  font-weight: 700;
  letter-spacing: 0.5px;
  margin: 0;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  line-height: 1.1;
}

.subtitle {
  font-size: 14px;
  opacity: 0.9;
  margin: 0;
  font-weight: 400;
  line-height: 1.2;
}
*/
/* 进度条样式 */
.progress-modal {
  max-width: 500px;
}

.progress-container {
  margin: 20px 0;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background-color: #e9ecef;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #4f46e5, #7c3aed);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
  font-size: 14px;
}

.progress-percentage {
  font-weight: 600;
  color: #4f46e5;
}

.progress-message {
  color: #6b7280;
  text-align: right;
}

.progress-details {
  margin-top: 12px;
  padding: 12px;
  background-color: #f8fafc;
  border-radius: 6px;
  font-size: 14px;
  color: #475569;
}

/* 模态框样式调整 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
}

.modal-header h3 {
  margin: 0 0 16px 0;
  font-size: 20px;
  font-weight: 600;
}

.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 20px;
}

.btn-primary {
  background-color: #4f46e5;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
}

.btn-secondary {
  background-color: #f3f4f6;
  color: #374151;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
}

.btn-secondary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
/* 进度条模态框样式 */
.progress-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(5px);
}

.progress-modal-content {
  background: white;
  border-radius: 16px;
  padding: 32px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  max-width: 500px;
  width: 90%;
  animation: modal-appear 0.3s ease-out;
}

@keyframes modal-appear {
  from {
    opacity: 0;
    transform: scale(0.9) translateY(-10px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.progress-modal-header h3 {
  margin: 0 0 20px 0;
  font-size: 24px;
  font-weight: 600;
  text-align: center;
  color: #1f2937;
}

.progress-modal-body {
  margin: 20px 0;
}

.progress-container {
  margin: 20px 0;
}

.progress-bar {
  width: 100%;
  height: 12px;
  background-color: #e5e7eb;
  border-radius: 6px;
  overflow: hidden;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.1);
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #4f46e5, #7c3aed);
  border-radius: 6px;
  transition: width 0.5s ease-in-out;
  box-shadow: 0 2px 4px rgba(79, 70, 229, 0.3);
}

.progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
  font-size: 14px;
}

.progress-percentage {
  font-weight: 700;
  color: #4f46e5;
  font-size: 16px;
}

.progress-message {
  color: #6b7280;
  text-align: right;
  flex: 1;
  margin-left: 16px;
}

.progress-details {
  margin-top: 16px;
  padding: 16px;
  background-color: #f8fafc;
  border-radius: 8px;
  font-size: 14px;
  color: #475569;
  border-left: 4px solid #4f46e5;
}

.error-message {
  margin-top: 16px;
  padding: 16px;
  background-color: #fef2f2;
  border-radius: 8px;
  font-size: 14px;
  color: #dc2626;
  border-left: 4px solid #dc2626;
}

.progress-modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 24px;
}

.btn-primary {
  background-color: #4f46e5;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.2s;
}

.btn-primary:hover {
  background-color: #4338ca;
}

.btn-secondary {
  background-color: #f3f4f6;
  color: #374151;
  border: none;
  padding: 10px 20px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.2s;
}

.btn-secondary:hover:not(:disabled) {
  background-color: #e5e7eb;
}

.btn-secondary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 确保其他模态框样式不冲突 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
  max-width: 400px;
  width: 90%;
}
/* 进度条模态框样式 */
.progress-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(5px);
}

.progress-modal-content {
  background: white;
  border-radius: 16px;
  padding: 32px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  max-width: 500px;
  width: 90%;
  animation: modal-appear 0.3s ease-out;
}

@keyframes modal-appear {
  from {
    opacity: 0;
    transform: scale(0.9) translateY(-10px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.progress-modal-header h3 {
  margin: 0 0 20px 0;
  font-size: 24px;
  font-weight: 600;
  text-align: center;
  color: #1f2937;
}

.progress-modal-body {
  margin: 20px 0;
}

.progress-container {
  margin: 20px 0;
}

.progress-bar {
  width: 100%;
  height: 12px;
  background-color: #e5e7eb;
  border-radius: 6px;
  overflow: hidden;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.1);
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #4f46e5, #7c3aed);
  border-radius: 6px;
  transition: width 0.5s ease-in-out;
  box-shadow: 0 2px 4px rgba(79, 70, 229, 0.3);
}

.progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
  font-size: 14px;
}

.progress-percentage {
  font-weight: 700;
  color: #4f46e5;
  font-size: 16px;
}

.progress-message {
  color: #6b7280;
  text-align: right;
  flex: 1;
  margin-left: 16px;
}

.progress-details {
  margin-top: 16px;
  padding: 16px;
  background-color: #f8fafc;
  border-radius: 8px;
  font-size: 14px;
  color: #475569;
  border-left: 4px solid #4f46e5;
}

.success-message {
  margin-top: 16px;
  padding: 16px;
  background-color: #f0fdf4;
  border-radius: 8px;
  font-size: 14px;
  color: #166534;
  border-left: 4px solid #22c55e;
}

.success-message .redirect-hint {
  margin-top: 8px;
  font-size: 12px;
  opacity: 0.8;
}

.error-message {
  margin-top: 16px;
  padding: 16px;
  background-color: #fef2f2;
  border-radius: 8px;
  font-size: 14px;
  color: #dc2626;
  border-left: 4px solid #dc2626;
}

.progress-modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 24px;
}

.btn-primary {
  background-color: #4f46e5;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.2s;
}

.btn-primary:hover {
  background-color: #4338ca;
}

.btn-secondary {
  background-color: #f3f4f6;
  color: #374151;
  border: none;
  padding: 10px 20px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.2s;
}

.btn-secondary:hover:not(:disabled) {
  background-color: #e5e7eb;
}

.btn-secondary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 确保其他模态框样式不冲突 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
  max-width: 400px;
  width: 90%;
}
</style>
