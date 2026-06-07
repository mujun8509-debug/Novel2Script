<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { UploadFilled, Document, ArrowRight, Check, Warning } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { apiService } from '@/api'

const router = useRouter()
const projectName = ref('')
const novelText = ref('')
const loading = ref(false)
const uploadedFileName = ref('')

// 解析摘要数据
const parseSummary = computed(() => {
  const text = novelText.value.trim()
  const charCount = text.length
  // 估算章节数（简单按换行或章节标题检测）
  const chapterMatches = text.match(/(?:^|\n)第[一二三四五六七八九十百千万零0-9零一二三四五六七八九十百千万]+[章回]|#+\s*\d+/gim)
  const estimatedChapters = chapterMatches ? chapterMatches.length : 0
  const wordCount = Math.round(charCount / 2) // 中文字符估算

  return {
    fileName: uploadedFileName.value || '未命名',
    charCount,
    wordCount,
    estimatedChapters: Math.max(estimatedChapters, 3), // 至少显示3章用于提示
    isValid: estimatedChapters >= 3 || charCount > 0
  }
})

// 检测是否满足3章要求
const meetsRequirement = computed(() => {
  const text = novelText.value.trim()
  if (!text) return false
  const chapterMatches = text.match(/(?:^|\n)第[一二三四五六七八九十百千万零0-9零一二三四五六七八九十百千万]+[章回]|#+\s*\d+/gim)
  const count = chapterMatches ? chapterMatches.length : 0
  return count >= 3
})

// 预估章节列表
const estimatedChapterList = computed(() => {
  const text = novelText.value.trim()
  if (!text) return []

  const chapters: string[] = []
  const lines = text.split('\n')

  for (const line of lines) {
    const trimmed = line.trim()
    // 检测中文章节标题
    const chapterMatch = trimmed.match(/^(?:第)?([一二三四五六七八九十百千万零0-9零一二三四五六七八九十百千万]+)[章回](.*)$/i)
    if (chapterMatch) {
      chapters.push(`第${chapterMatch[1]}章${chapterMatch[2] || ''}`.trim())
    }
    // 检测 Markdown 标题格式
    const mdMatch = trimmed.match(/^#+\s*(\d+)\s*(.*)$/i)
    if (mdMatch) {
      chapters.push(`第${mdMatch[1]}章${mdMatch[2] || ''}`.trim())
    }
  }

  // 如果没检测到，返回默认提示
  if (chapters.length === 0 && text.length > 100) {
    return ['（将自动分割为3章）']
  }

  return chapters.slice(0, 10) // 最多显示10个
})

const handleFileUpload = (file: any) => {
  uploadedFileName.value = file.name
  const reader = new FileReader()
  reader.onload = (e) => {
    novelText.value = e.target?.result as string
    ElMessage.success('文件上传成功')
  }
  reader.readAsText(file.raw)
  return false
}

// 监听文本变化，清除文件名
watch(novelText, () => {
  if (!novelText.value && uploadedFileName.value) {
    // 如果清空了文本，也清空文件名
  }
})

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
      </div>

      <!-- 解析摘要面板 -->
      <div v-if="novelText.trim()" class="parse-summary">
        <div class="summary-header">
          <span class="summary-title">📋 小说解析结果</span>
        </div>
        <div class="summary-content">
          <div class="summary-item">
            <span class="summary-label">文件名</span>
            <span class="summary-value">{{ parseSummary.fileName }}</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">总字数</span>
            <span class="summary-value">{{ parseSummary.charCount.toLocaleString() }} 字</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">识别章节</span>
            <span class="summary-value">{{ estimatedChapterList.length || '待识别' }} 章</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">满足要求</span>
            <span :class="['summary-badge', meetsRequirement ? 'success' : 'warning']">
              <el-icon v-if="meetsRequirement"><Check /></el-icon>
              <el-icon v-else><Warning /></el-icon>
              {{ meetsRequirement ? '已满足（≥3章）' : '不足3章' }}
            </span>
          </div>
        </div>
        <div v-if="estimatedChapterList.length > 0" class="chapter-preview">
          <div class="chapter-preview-title">预估章节列表：</div>
          <div class="chapter-tags">
            <span v-for="(chapter, index) in estimatedChapterList" :key="index" class="chapter-tag">
              {{ chapter }}
            </span>
            <span v-if="estimatedChapterList.length >= 10" class="chapter-tag more">
              ...
            </span>
          </div>
        </div>
        <div class="summary-tip" :class="{ success: meetsRequirement }">
          <template v-if="meetsRequirement">
            ✅ 已识别到 3 个以上章节，满足题目要求，可生成结构化 YAML 剧本。
          </template>
          <template v-else>
            ⚠️ 当前识别章节不足 3 个，系统将自动将文本分割为 3 个章节进行生成。
          </template>
        </div>
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

/* 解析摘要面板 */
.parse-summary {
  background: rgba(99, 102, 241, 0.08);
  border: 1px solid rgba(99, 102, 241, 0.3);
  border-radius: 12px;
  padding: 20px;
  margin-top: 16px;
  animation: fadeIn 0.4s ease;
}

.summary-header {
  margin-bottom: 16px;
}

.summary-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.summary-content {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

.summary-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: rgba(15, 15, 26, 0.4);
  border-radius: 8px;
}

.summary-label {
  font-size: 13px;
  color: var(--text-secondary);
}

.summary-value {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
}

.summary-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}

.summary-badge.success {
  background: rgba(16, 185, 129, 0.2);
  color: #10b981;
}

.summary-badge.warning {
  background: rgba(245, 158, 11, 0.2);
  color: #f59e0b;
}

.chapter-preview {
  margin-bottom: 12px;
}

.chapter-preview-title {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.chapter-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.chapter-tag {
  padding: 4px 10px;
  background: rgba(99, 102, 241, 0.15);
  border: 1px solid rgba(99, 102, 241, 0.3);
  border-radius: 6px;
  font-size: 12px;
  color: var(--text-primary);
}

.chapter-tag.more {
  background: transparent;
  border: 1px dashed var(--border-color);
  color: var(--text-secondary);
}

.summary-tip {
  padding: 10px 12px;
  background: rgba(245, 158, 11, 0.1);
  border-radius: 8px;
  font-size: 13px;
  color: #f59e0b;
  line-height: 1.5;
}

.summary-tip.success {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
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
