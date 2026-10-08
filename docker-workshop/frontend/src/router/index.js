import { createRouter, createWebHistory } from 'vue-router'
import { getBasePath } from '../utils/basePath'

import Welcome from '../views/Welcome.vue'
import Build from '../views/Build.vue'

const routes = [
  {
    path: '/',
    name: 'Welcome',
    component: Welcome
  },
  {
    path: '/review',
    name: 'Review',
    redirect: '/build'
  },
  {
    path: '/demo',
    name: 'Demo',
    redirect: '/build'
  },
  {
    path: '/build',
    name: 'Build',
    component: Build
  }
]

const router = createRouter({
  history: createWebHistory(getBasePath()),
  routes
})

export default router
