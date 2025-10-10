<template>
  <div class="language-switcher">
    <button
      class="lang-btn"
      :class="{ active: currentLang === 'zh' }"
      @click="switchLanguage('zh')"
    >
      中文
    </button>
    <span class="separator">|</span>
    <button
      class="lang-btn"
      :class="{ active: currentLang === 'en' }"
      @click="switchLanguage('en')"
    >
      English
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'

const { locale } = useI18n()
const currentLang = ref(locale.value)

const switchLanguage = (lang: 'zh' | 'en') => {
  locale.value = lang
  currentLang.value = lang
  localStorage.setItem('preferred-language', lang)
}

onMounted(() => {
  const savedLang = localStorage.getItem('preferred-language') as 'zh' | 'en'
  if (savedLang) {
    switchLanguage(savedLang)
  }
})
</script>

<style scoped>
.language-switcher {
  display: flex;
  align-items: center;
  gap: 4px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 4px;
  backdrop-filter: blur(10px);
}

.lang-btn {
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.7);
  font-size: 12px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.lang-btn:hover {
  color: rgba(255, 255, 255, 0.9);
  background: rgba(255, 255, 255, 0.1);
}

.lang-btn.active {
  color: #fff;
  background: rgba(255, 255, 255, 0.2);
  font-weight: 600;
}

.separator {
  color: rgba(255, 255, 255, 0.4);
  font-size: 12px;
}
</style>
