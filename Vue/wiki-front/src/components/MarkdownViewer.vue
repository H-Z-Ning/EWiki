<template>
  <article class="markdown-body" v-html="html"></article>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import MarkdownIt from 'markdown-it'
import 'github-markdown-css/github-markdown.css'

const props = defineProps<{ source: string }>()

const md = new MarkdownIt({ html: true })
const html = computed(() => md.render(props.source))
</script>

<style scoped>
.markdown-body {
  padding: 32px;
  max-width: 100%;
  box-sizing: border-box;
}
</style>
