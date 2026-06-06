import { createRouter, createWebHistory } from 'vue-router'
import InputView from '@/views/InputView.vue'
import ChapterView from '@/views/ChapterView.vue'
import ProgressView from '@/views/ProgressView.vue'
import ResultView from '@/views/ResultView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'input',
      component: InputView
    },
    {
      path: '/chapters/:id',
      name: 'chapters',
      component: ChapterView
    },
    {
      path: '/progress/:id',
      name: 'progress',
      component: ProgressView
    },
    {
      path: '/result/:id',
      name: 'result',
      component: ResultView
    }
  ]
})

export default router
