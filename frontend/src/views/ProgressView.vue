<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { apiService } from '@/api'

const router = useRouter()
const route = useRoute()
const projectId = route.params.id as string
const selectedStorageKey = `novel2script:selectedChapters:${projectId}`

const currentStep = ref('准备中...')
const selectedChapterIds = ref<string[]>([])

const buildSteps = (chapterCount: number) => [
  { name: '准备转换', key: 'prepare', status: 'pending' },
  { name: `生成所选 ${chapterCount} 章剧本`, key: 'chapters', status: 'pending' },
  { name: '校验 YAML Schema', key: 'validate', status: 'pending' },
  { name: '生成完成', key: 'completed', status: 'pending' }
]

const steps = ref(buildSteps(3))

const progress = ref(0)
const isConverting = ref(true)
let pollInterval: number | null = null

const updateSteps = (status: string) => {
  const currentIndex = status === 'completed' ? steps.value.length : status === 'converting' ? 1 : 0
  steps.value.forEach((step, index) => {
    if (index < currentIndex) {
      step.status = 'completed'
    } else if (index === currentIndex) {
      step.status = 'active'
      currentStep.value = steps.value[index].name
    } else {
      step.status = 'pending'
    }
  })

  if (status === 'completed') {
    currentStep.value = '生成完成'
  }
  progress.value = Math.min((currentIndex / steps.value.length) * 100, 100)
}

const checkStatus = async () => {
  try {
    const info = await apiService.getProject(projectId)
    updateSteps(info.status)

    if (info.status === 'completed') {
      isConverting.value = false
      ElMessage.success('剧本生成完成！')
      setTimeout(() => {
        router.push(`/result/${projectId}`)
      }, 1000)
    } else if (info.status === 'error') {
      isConverting.value = false
      ElMessage.error('生成失败，请重试')
    }
  } catch (error) {
    console.error('检查状态失败', error)
  }
}

const startConvert = async () => {
  try {
    await apiService.convertProject(projectId, selectedChapterIds.value)
    await checkStatus()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || error.detail || '转换失败')
    isConverting.value = false
  }
}

onMounted(() => {
  try {
    const raw = sessionStorage.getItem(selectedStorageKey)
    selectedChapterIds.value = raw ? JSON.parse(raw) : []
  } catch {
    selectedChapterIds.value = []
  }
  steps.value = buildSteps(selectedChapterIds.value.length || 3)
  updateSteps('converting')
  startConvert()

  pollInterval = window.setInterval(() => {
    if (isConverting.value) {
      checkStatus()
    }
  }, 2000)
})

onUnmounted(() => {
  if (pollInterval) {
    clearInterval(pollInterval)
  }
})
</script>

<template>
  <div class="progress-page">
    <div class="header">
      <h1 class="page-title">正在生成剧本</h1>
      <p class="page-subtitle">请耐心等待，AI 正在分析并转换...</p>
    </div>

    <div class="card progress-card">
      <div class="progress-info">
        <span class="current-step">{{ currentStep }}</span>
        <span class="progress-percent">{{ Math.round(progress) }}%</span>
      </div>

      <el-progress
        :percentage="progress"
        :stroke-width="10"
        :show-text="false"
        class="progress-bar"
      />

      <div class="steps-list">
        <div
          v-for="(step, index) in steps"
          :key="step.key"
          class="step-item"
          :class="step.status"
        >
          <div class="step-indicator">
            <el-icon v-if="step.status === 'completed'" class="check-icon"><Check /></el-icon>
            <el-icon v-else-if="step.status === 'active'" class="loading-icon"><Loading /></el-icon>
            <span v-else class="step-number">{{ index + 1 }}</span>
          </div>
          <span class="step-name">{{ step.name }}</span>
        </div>
      </div>
    </div>

    <div class="tips">
      <el-icon><InfoFilled /></el-icon>
      <span>提示：生成过程可能需要几分钟，取决于小说长度和网络状况</span>
    </div>
  </div>
</template>

<style scoped>
.progress-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
}

.header {
  text-align: center;
  margin-bottom: 40px;
}

.progress-card {
  width: 100%;
  max-width: 600px;
  padding: 40px;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.current-step {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.progress-percent {
  font-size: 24px;
  font-weight: 700;
  color: var(--primary-color);
}

.progress-bar {
  margin-bottom: 40px;
}

:deep(.el-progress-bar__outer) {
  background: rgba(99, 102, 241, 0.15);
  border-radius: 10px;
}

:deep(.el-progress-bar__inner) {
  background: linear-gradient(90deg, var(--primary-color), #8b5cf6);
  border-radius: 10px;
  transition: width 0.5s ease;
}

.steps-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.step-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
  background: rgba(15, 15, 26, 0.5);
  border-radius: 10px;
  border: 1px solid rgba(99, 102, 241, 0.1);
  transition: all 0.3s ease;
}

.step-item.active {
  background: rgba(99, 102, 241, 0.15);
  border-color: var(--primary-color);
}

.step-item.completed {
  background: rgba(16, 185, 129, 0.1);
  border-color: rgba(16, 185, 129, 0.3);
}

.step-indicator {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: rgba(99, 102, 241, 0.2);
  color: var(--primary-color);
}

.step-item.completed .step-indicator {
  background: rgba(16, 185, 129, 0.2);
  color: #10b981;
}

.step-item.pending .step-indicator {
  background: rgba(148, 163, 184, 0.2);
  color: var(--text-secondary);
}

.step-number {
  font-size: 14px;
  font-weight: 600;
}

.check-icon,
.loading-icon {
  font-size: 18px;
}

.loading-icon {
  animation: spin 1s linear infinite;
}

.step-name {
  font-size: 15px;
  color: var(--text-secondary);
}

.step-item.active .step-name {
  color: var(--text-primary);
  font-weight: 500;
}

.step-item.completed .step-name {
  color: #10b981;
}

.tips {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 32px;
  padding: 16px 24px;
  background: rgba(99, 102, 241, 0.1);
  border: 1px solid rgba(99, 102, 241, 0.2);
  border-radius: 10px;
  color: var(--text-secondary);
  font-size: 14px;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
