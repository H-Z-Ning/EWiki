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
          :class="{ active: activeTab === 'local' }"
          @click="activeTab = 'local'"
        >
          {{ $t('home.localPath') }}
        </button>
        <button
          class="tab-button"
          :class="{ active: activeTab === 'upload' }"
          @click="activeTab = 'upload'"
        >
          {{ $t('home.fileUpload') }}
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
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import axios from 'axios'
import LanguageSwitcher from '@/components/LanguageSwitcher.vue'

const { t } = useI18n()

interface Project {
  name: string;
}

/* 数据 */
const router = useRouter()
const path = ref('')
const running = ref(false)
const projects = ref<Project[]>([])
const activeTab = ref('local')
const selectedFile = ref<File | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)

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

const doImport = async () => {
  if (!path.value.trim()) return
  running.value = true
  try {
    const { data } = await axios.post('/api/import', { path: path.value.trim() })
    await loadList()
    router.push(`/wiki/${data.project}`)
  } catch (error) {
    console.error(t('errors.importFailed'), error)
    alert(t('errors.importFailed'))
  } finally {
    running.value = false
  }
}

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

const doUpload = async () => {
  if (!selectedFile.value) return

  running.value = true
  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)

    const { data } = await axios.post('/api/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    await loadList()
    router.push(`/wiki/${data.project}`)
  } catch (error: any) {
    console.error(t('errors.uploadFailed'), error)
    alert(`${t('errors.uploadFailed')}: ${error.response?.data?.detail || t('errors.requestFailed')}`)
  } finally {
    running.value = false
  }
}

const goWiki = (p: string) => router.push(`/wiki/${p}`)

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
</style>
