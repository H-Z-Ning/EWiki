import { createRouter, createWebHistory } from 'vue-router'
import Home from './views/Home.vue'
import Wiki from './views/Wiki.vue'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: Home },
    { path: '/wiki/:project', name: 'wiki', component: Wiki }
  ]
})