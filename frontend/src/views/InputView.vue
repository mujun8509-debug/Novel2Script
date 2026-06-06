<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { UploadFilled, Document, ArrowRight } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { apiService } from '@/api'

const router = useRouter()
const projectName = ref('')
const novelText = ref('')
const loading = ref(false)

const handleFileUpload = (file: any) => {
  const reader = new FileReader()
  reader.onload = (e) => {
    novelText.value = e.target?.result as string
    ElMessage.success('文件上传成功')
  }
  reader.readAsText(file.raw)
  return false
}

const handleSubmit = async () => {
  if (!projectName.value.trim()) {
    ElMessage.warning('请输入项目名称')
    return
  }
  if (!novelText.value.trim()) {
    ElMessage.warning('请输入小说文本或上传文件')
    return
  }

  loading.value = true
  try {
    const result = await apiService.createProject({
      name: projectName.value,
      novel_text: novelText.value
    })
    router.push(`/chapters/${result.project_id}`)
  } catch (error: any) {
    ElMessage.error(error.message || '创建项目失败')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="input-page">
    <div class="header">
      <h1 class="page-title">Novel2Script</h1>
      <p class="page-subtitle">AI 小说转结构化剧本工具</p>
    </div>

    <div class="card form-card">
      <div class="form-group">
        <label class="form-label">项目名称</label>
        <el-input
          v-model="projectName"
          placeholder="给项目起个名字"
          size="large"
          class="project-input"
        />
      </div>

      <div class="form-group">
        <label class="form-label">上传小说文件</label>
        <el-upload
          class="upload-area"
          drag
          action="#"
          :auto-upload="false"
          :show-file-list="false"
          :on-change="handleFileUpload"
          accept=".txt"
        >
          <el-icon class="upload-icon"><UploadFilled /></el-icon>
          <div class="upload-text">
            <span>拖拽 TXT 文件到此处</span>
            <span class="upload-hint">或点击选择文件</span>
          </div>
        </el-upload>
      </div>

      <div class="form-group">
        <label class="form-label">或直接粘贴小说文本</label>
        <el-input
          v-model="novelText"
          type="textarea"
          :rows="10"
          placeholder="将小说内容粘贴在此处..."
          class="input-area"
        />
        <div class="text-hint">支持至少 3 个章节的小说文本</div>
      </div>

      <div class="form-actions">
        <button
          class="btn-primary"
          :disabled="loading"
          @click="handleSubmit"
        >
          <span v-if="loading">创建中...</span>
          <span v-else>
            开始解析
            <el-icon class="btn-icon"><ArrowRight /></el-icon>
          </span>
        </button>
      </div>
    </div>

    <div class="features">
      <div class="feature-item">
        <el-icon class="feature-icon"><Document /></el-icon>
        <span>智能章节识别</span>
      </div>
      <div class="feature-item">
        <el-icon class="feature-icon"><Document /></el-icon>
        <span>人物场景提取</span>
      </div>
      <div class="feature-item">
        <el-icon class="feature-icon"><Document /></el-icon>
        <span>结构化 YAML 输出</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.input-page {
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

.form-card {
  width: 100%;
  max-width: 700px;
  animation: fadeIn 0.6s ease;
}

.form-group {
  margin-bottom: 24px;
}

.form-label {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 12px;
}

.project-input {
  font-size: 16px;
}

.upload-area {
  width: 100%;
}

:deep(.el-upload-dragger) {
  background: rgba(15, 15, 26, 0.6);
  border: 2px dashed var(--border-color);
  border-radius: 12px;
  padding: 40px;
  transition: all 0.3s ease;
}

:deep(.el-upload-dragger:hover) {
  border-color: var(--primary-color);
  background: rgba(99, 102, 241, 0.1);
}

.upload-icon {
  font-size: 48px;
  color: var(--primary-color);
  margin-bottom: 16px;
}

.upload-text {
  display: flex;
  flex-direction: column;
  gap: 8px;
  color: var(--text-primary);
}

.upload-hint {
  font-size: 12px;
  color: var(--text-secondary);
}

.input-area {
  font-family: inherit;
}

.text-hint {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 8px;
  text-align: right;
}

.form-actions {
  display: flex;
  justify-content: center;
  margin-top: 32px;
}

.btn-primary {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  padding: 14px 48px;
}

.btn-icon {
  margin-left: 4px;
}

.features {
  display: flex;
  gap: 40px;
  margin-top: 48px;
  animation: fadeIn 0.8s ease;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-secondary);
  font-size: 14px;
}

.feature-icon {
  color: var(--primary-color);
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
