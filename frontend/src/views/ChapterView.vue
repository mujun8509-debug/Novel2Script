<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { apiService, ChapterInfo, StoryBible } from '@/api'

const router = useRouter()
const route = useRoute()
const projectId = route.params.id as string

const loading = ref(true)
const analyzing = ref(false)
const projectInfo = ref<any>(null)
const chapters = ref<ChapterInfo[]>([])
const storyBible = ref<StoryBible | null>(null)
const currentStep = ref('识别章节中...')
const selectedChapters = ref<Set<string>>(new Set())
const selectedStorageKey = `novel2script:selectedChapters:${projectId}`

// 计算选中的章节数量
const selectedCount = computed(() => selectedChapters.value.size)

// 检查是否满足批量生成要求（至少3章）
const canBatchGenerate = computed(() => selectedChapters.value.size >= 3)

// 检查是否至少3章（不管是否选中）
const hasMinimumChapters = computed(() => chapters.value.length >= 3)

// 全选/取消全选
const toggleSelectAll = () => {
  const selectableCount = Math.min(10, chapters.value.length)
  if (selectedChapters.value.size === selectableCount) {
    selectedChapters.value.clear()
  } else {
    selectedChapters.value.clear()
    chapters.value.forEach(ch => {
      if (chapters.value.indexOf(ch) < 10) { // 默认最多选10章
        selectedChapters.value.add(ch.chapter_id)
      }
    })
  }
  selectedChapters.value = new Set(selectedChapters.value)
}

// 切换单个章节选中状态
const toggleChapter = (chapterId: string) => {
  if (selectedChapters.value.has(chapterId)) {
    selectedChapters.value.delete(chapterId)
  } else {
    selectedChapters.value.add(chapterId)
  }
  // 强制更新响应式
  selectedChapters.value = new Set(selectedChapters.value)
}

const handleAnalyze = async () => {
  analyzing.value = true
  currentStep.value = '正在分析小说...'
  try {
    const result = await apiService.analyzeProject(projectId)
    chapters.value = result.chapters || []
    storyBible.value = result.story_bible
    // 默认选中前3章
    selectedChapters.value.clear()
    chapters.value.slice(0, Math.min(3, chapters.value.length)).forEach(ch => {
      selectedChapters.value.add(ch.chapter_id)
    })
    currentStep.value = '提取人物设定...'
    await fetchProjectDetails()
    ElMessage.success('分析完成，已默认选中前3章')
  } catch (error: any) {
    ElMessage.error(error.detail || '分析失败')
  } finally {
    analyzing.value = false
  }
}

const fetchProjectDetails = async () => {
  try {
    const info = await apiService.getProject(projectId)
    projectInfo.value = info
  } catch (error) {
    console.error('获取项目信息失败', error)
  }
}

const handleConvert = () => {
  sessionStorage.setItem(selectedStorageKey, JSON.stringify([...selectedChapters.value]))
  router.push(`/progress/${projectId}`)
}

onMounted(async () => {
  await fetchProjectDetails()
  loading.value = false

  if (projectInfo.value?.has_story_bible) {
    // 已经分析过，获取完整的章节和story_bible数据
    try {
      const result = await apiService.getAnalysis(projectId)
      chapters.value = result.chapters || []
      storyBible.value = result.story_bible
      // 默认选中前3章
      selectedChapters.value.clear()
      chapters.value.slice(0, Math.min(3, chapters.value.length)).forEach(ch => {
        selectedChapters.value.add(ch.chapter_id)
      })
    } catch (e) {
      console.error('获取分析结果失败', e)
    }
  } else {
    // 自动开始分析
    setTimeout(() => {
      handleAnalyze()
    }, 500)
  }
})
</script>

<template>
  <div class="chapter-page">
    <div class="header">
      <h1 class="page-title">章节预览</h1>
      <p class="page-subtitle">{{ projectInfo?.name || '项目' }}</p>
    </div>

    <div v-if="loading" class="loading-state">
      <el-icon class="is-loading"><Loading /></el-icon>
      <span>加载中...</span>
    </div>

    <template v-else>
      <!-- 分析状态 -->
      <div v-if="analyzing" class="analyzing-card card">
        <el-icon class="analyzing-icon"><Loading /></el-icon>
        <p class="analyzing-text">{{ currentStep }}</p>
      </div>

      <!-- 章节列表 -->
      <div v-else class="chapters-section">
        <div class="card chapters-card">
          <h2 class="section-title">
            <el-icon><Document /></el-icon>
            已识别到 {{ chapters.length }} 个章节
            <span class="chapter-requirement" :class="{ met: hasMinimumChapters }">
              {{ hasMinimumChapters ? '✅ 满足要求' : '⚠️ 不足3章' }}
            </span>
          </h2>

          <!-- 选择提示 -->
          <div class="selection-info">
            <span class="selection-count">
              已选择 <strong>{{ selectedCount }}</strong> 个章节
              <template v-if="selectedCount < 3">（至少需要3章）</template>
            </span>
            <button class="btn-select-all" @click="toggleSelectAll">
              {{ selectedCount === Math.min(10, chapters.length) ? '取消全选' : '全选前10章' }}
            </button>
          </div>

          <div class="chapter-list">
            <div
              v-for="(chapter, index) in chapters"
              :key="chapter.chapter_id"
              :class="['chapter-item', { selected: selectedChapters.has(chapter.chapter_id) }]"
              @click="toggleChapter(chapter.chapter_id)"
            >
              <el-checkbox
                :model-value="selectedChapters.has(chapter.chapter_id)"
                @click.stop
                @change="toggleChapter(chapter.chapter_id)"
              />
              <span class="chapter-index">{{ index + 1 }}</span>
              <span class="chapter-title">{{ chapter.title }}</span>
              <span class="chapter-words">{{ chapter.word_count }} 字</span>
            </div>
          </div>

          <div v-if="!hasMinimumChapters" class="warning-text">
            <el-icon><Warning /></el-icon>
            检测到章节数不足 3 章，请上传至少 3 个章节的小说文本
          </div>
        </div>

        <!-- 全局信息预览 -->
        <div v-if="storyBible" class="card story-bible-card">
          <h2 class="section-title">
            <el-icon><InfoFilled /></el-icon>
            全局设定
          </h2>

          <div class="story-bible-content">
            <div class="sb-item">
              <label>标题</label>
              <span>{{ storyBible.title }}</span>
            </div>
            <div class="sb-item">
              <label>类型</label>
              <span>{{ storyBible.genre }}</span>
            </div>
            <div class="sb-item">
              <label>主题</label>
              <span>{{ storyBible.theme }}</span>
            </div>
            <div class="sb-item">
              <label>世界观</label>
              <span>{{ storyBible.world_setting }}</span>
            </div>
            <div class="sb-item">
              <label>核心冲突</label>
              <span>{{ storyBible.main_conflict }}</span>
            </div>

            <div class="sb-section">
              <h3>人物 ({{ storyBible.characters?.length || 0 }})</h3>
              <div class="character-list">
                <div
                  v-for="char in storyBible.characters"
                  :key="char.id"
                  class="character-item"
                >
                  <span class="char-name">{{ char.name }}</span>
                  <span class="char-role">{{ char.role }}</span>
                </div>
              </div>
            </div>

            <div class="sb-section">
              <h3>地点 ({{ storyBible.locations?.length || 0 }})</h3>
              <div class="location-list">
                <div
                  v-for="loc in storyBible.locations"
                  :key="loc.id"
                  class="location-item"
                >
                  <span class="loc-name">{{ loc.name }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="actions">
          <div class="action-info">
            <span v-if="selectedCount > 0 && selectedCount < 3" class="action-warning">
              ⚠️ 请至少选择 3 个章节
            </span>
            <span v-else-if="selectedCount >= 3" class="action-success">
              ✅ 已选择 {{ selectedCount }} 个章节，满足批量生成要求
            </span>
          </div>
          <button
            class="btn-primary"
            :disabled="!canBatchGenerate || analyzing"
            @click="handleConvert"
          >
            生成所选 {{ selectedCount }} 章 YAML 剧本
            <el-icon><ArrowRight /></el-icon>
          </button>
          <p class="action-hint">
            题目要求：至少 3 个章节以上小说文本转换为结构化剧本
          </p>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.chapter-page {
  min-height: 100vh;
  padding: 40px 20px;
  max-width: 900px;
  margin: 0 auto;
}

.header {
  text-align: center;
  margin-bottom: 40px;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 80px;
  color: var(--text-secondary);
}

.analyzing-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px;
  gap: 20px;
}

.analyzing-icon {
  font-size: 48px;
  color: var(--primary-color);
  animation: spin 2s linear infinite;
}

.analyzing-text {
  font-size: 18px;
  color: var(--text-secondary);
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.chapters-section {
  animation: fadeIn 0.5s ease;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 24px;
}

.chapters-card {
  margin-bottom: 24px;
}

.chapter-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.chapter-item {
  display: flex;
  align-items: center;
  padding: 16px 20px;
  background: rgba(15, 15, 26, 0.5);
  border-radius: 10px;
  border: 1px solid rgba(99, 102, 241, 0.15);
  transition: all 0.2s ease;
}

.chapter-item:hover {
  border-color: var(--primary-color);
  background: rgba(99, 102, 241, 0.1);
}

.chapter-index {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--primary-color);
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  color: white;
  margin-right: 16px;
}

.chapter-title {
  flex: 1;
  font-size: 15px;
  color: var(--text-primary);
}

.chapter-words {
  font-size: 13px;
  color: var(--text-secondary);
}

.chapter-item.selected {
  border-color: var(--primary-color);
  background: rgba(99, 102, 241, 0.1);
}

.chapter-requirement {
  font-size: 13px;
  margin-left: 12px;
  padding: 4px 10px;
  border-radius: 12px;
}

.chapter-requirement:not(.met) {
  background: rgba(245, 158, 11, 0.15);
  color: #f59e0b;
}

.chapter-requirement.met {
  background: rgba(16, 185, 129, 0.15);
  color: #10b981;
}

.selection-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding: 12px 16px;
  background: rgba(15, 15, 26, 0.4);
  border-radius: 8px;
}

.selection-count {
  font-size: 14px;
  color: var(--text-secondary);
}

.selection-count strong {
  color: var(--primary-color);
  font-size: 16px;
}

.btn-select-all {
  padding: 6px 14px;
  background: rgba(99, 102, 241, 0.15);
  border: 1px solid rgba(99, 102, 241, 0.3);
  border-radius: 6px;
  color: var(--primary-color);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-select-all:hover {
  background: rgba(99, 102, 241, 0.25);
}

.warning-text {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 20px;
  padding: 12px 16px;
  background: rgba(245, 158, 11, 0.1);
  border: 1px solid rgba(245, 158, 11, 0.3);
  border-radius: 8px;
  color: #fbbf24;
  font-size: 14px;
}

.story-bible-card {
  margin-bottom: 24px;
}

.story-bible-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.sb-item {
  display: flex;
  gap: 12px;
}

.sb-item label {
  width: 80px;
  font-size: 13px;
  color: var(--text-secondary);
  flex-shrink: 0;
}

.sb-item span {
  font-size: 14px;
  color: var(--text-primary);
}

.sb-section {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid rgba(99, 102, 241, 0.15);
}

.sb-section h3 {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 12px;
}

.character-list,
.location-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.character-item,
.location-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: rgba(99, 102, 241, 0.1);
  border: 1px solid rgba(99, 102, 241, 0.2);
  border-radius: 6px;
}

.char-name {
  font-size: 13px;
  color: var(--text-primary);
  font-weight: 500;
}

.char-role {
  font-size: 11px;
  color: var(--text-secondary);
}

.loc-name {
  font-size: 13px;
  color: var(--text-primary);
}

.actions {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  margin-top: 32px;
}

.action-info {
  font-size: 14px;
}

.action-warning {
  color: #f59e0b;
}

.action-success {
  color: #10b981;
}

.btn-primary {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 48px;
  font-size: 16px;
}

.action-hint {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 8px;
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
