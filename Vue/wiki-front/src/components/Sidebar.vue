<template>
  <aside class="sidebar">
    <!-- 仓库概览 -->
    <section class="group">
      <h4 class="title">📚 仓库概览</h4>
      <button
        :class="['btn', { active: current === 'project' }]"
        @click="select('project')"
      >
        📖 项目总览
      </button>
    </section>

    <!-- 代码模块 -->
    <section class="group">
      <h4 class="title">🧩 代码模块</h4>
      <button
        v-for="m in modules"
        :key="m"
        :class="['btn', { active: current === m }]"
        @click="select(m)"
      >
        📄 {{ m }}
      </button>
    </section>
  </aside>
</template>

<script setup lang="ts">
/* 你的原脚本完全保留，无需改动 */
import { ref } from 'vue'
import { listModules } from '@/api'

const emit = defineEmits<{ select: [key: string] }>()
const props = defineProps<{ project: string }>()

const modules = ref<string[]>([])
const current = ref('project')

listModules(props.project).then(data => (modules.value = data))

function select(key: string) {
  current.value = key
  emit('select', key)
}
</script>

<style scoped>
/* 整体侧边栏 */
.sidebar {
  width: 240px;
  height: 100vh;
  background: #ffffff;
  border-right: 1px solid #e5e7eb;
  padding: 24px 16px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* 分组 */
.group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* 小标题 */
.title {
  margin: 0;
  font-size: 13px;
  font-weight: 600;
  color: #4b5563;
  letter-spacing: 0.5px;
  padding-left: 4px;
}

/* 按钮统一样式 */
.btn {
  width: 100%;
  text-align: left;
  border: none;
  background: #f3f4f6;
  padding: 8px 12px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  color: #111827;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 6px;
}

/* 悬停态 */
.btn:hover {
  background: #e5e7eb;
}

/* 激活态 */
.btn.active {
  background: #0969da;
  color: #fff;
  box-shadow: 0 2px 8px rgba(9, 105, 218, 0.25);
}

/* 圆角激活条 */
.btn.active::before {
  content: "";
  width: 4px;
  height: 16px;
  background: #ffffff;
  border-radius: 2px;
  margin-right: 6px;
}
</style>