<template>
  <div class="home">
    <!-- 顶部 Hero -->
    <section class="hero">
      <h1 class="title">EWiki</h1>
      <p class="subtitle">一键生成项目 Wiki，让文档不再难写</p>
    </section>

    <!-- 导入区域 -->
    <section class="glass import-card">
      <h3>📦 导入新项目</h3>
      <div class="input-box">
        <input
          v-model="path"
          placeholder="粘贴本地项目绝对路径，如 /home/me/myproj"
          @keyup.enter="doImport"
        />
        <button class="primary" @click="doImport" :disabled="running">
          <span v-if="!running">生成 Wiki</span>
          <span v-else>生成中...</span>
        </button>
      </div>
    </section>

    <!-- 已有项目 -->
    <section class="glass projects-card">
      <h3>📚 已有 Wiki 的项目</h3>
      <div v-if="projects.length === 0" class="empty">
        暂无项目，快去导入一个吧 ~
      </div>
      <div class="cards">
        <div
          class="project-card"
          v-for="p in projects"
          :key="p"
          @click="goWiki(p)"
        >
          <div class="card-inner">
            <span class="icon">📁</span>
            <span class="name">{{ p }}</span>
            <span class="arrow">→</span>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

/* 数据 */
const router = useRouter()
const path = ref('')
const running = ref(false)
const projects = ref<string[]>([])

/* 方法 */
const loadList = async () => {
  projects.value = await axios.get('/api/projects').then(r => r.data)
}
const doImport = async () => {
  if (!path.value.trim()) return
  running.value = true
  try {
    const { data } = await axios.post('/api/import', { path: path.value.trim() })
    router.push(`/wiki/${data.project}`)
  } finally {
    running.value = false
  }
}
const goWiki = (p: string) => router.push(`/wiki/${p}`)

/* 生命周期 */
onMounted(loadList)
</script>

<style scoped>
/* 全局变量 */
:root {
  --blur: 12px;
  --radius: 16px;
  --primary: #6366f1;
  --primary-hover: #4f46e5;
}

/* 布局 */
.home {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 64px 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 40px;
}

/* Hero */
.hero {
  text-align: center;
  color: #fff;
}
.title {
  font-size: 48px;
  font-weight: 700;
  letter-spacing: 2px;
}
.subtitle {
  margin-top: 8px;
  font-size: 18px;
  opacity: 0.9;
}

/* Glass 卡片 */
.glass {
  width: 100%;
  max-width: 680px;
  background: rgba(255, 255, 255, 0.18);
  backdrop-filter: blur(var(--blur));
  -webkit-backdrop-filter: blur(var(--blur));
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: var(--radius);
  padding: 32px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  color: #fff;
}
.glass h3 {
  margin: 0 0 20px;
  font-size: 20px;
  font-weight: 600;
}

/* 输入框 */
.input-box {
  display: flex;
  gap: 12px;
}
.input-box input {
  flex: 1;
  padding: 12px 16px;
  border: none;
  border-radius: 8px;
  font-size: 15px;
  background: rgba(255, 255, 255, 0.9);
  color: #333;
}
.primary {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  background: var(--primary);
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}
.primary:hover:not(:disabled) {
  background: var(--primary-hover);
}
.primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 项目卡片 */
.cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}
.project-card {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 12px;
  cursor: pointer;
  transition: transform 0.2s, background 0.2s;
}
.project-card:hover {
  background: rgba(255, 255, 255, 0.25);
  transform: translateY(-4px);
}
.card-inner {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
}
.icon {
  font-size: 24px;
}
.name {
  flex: 1;
  font-weight: 500;
}
.arrow {
  opacity: 0.6;
}

/* 空状态 */
.empty {
  text-align: center;
  opacity: 0.7;
  font-size: 15px;
}

/* 响应式 */
@media (max-width: 600px) {
  .title {
    font-size: 36px;
  }
  .input-box {
    flex-direction: column;
  }
}
</style>