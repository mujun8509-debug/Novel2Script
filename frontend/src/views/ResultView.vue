<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Download, Refresh, Check, Warning } from '@element-plus/icons-vue'
import { apiService, ScriptResult } from '@/api'
import yaml from 'js-yaml'

const route = useRoute()
const projectId = route.params.id as string

const loading = ref(true)
const result = ref<ScriptResult | null>(null)
const validationResult = ref<any>(null)
const yamlText = ref('')
const activeTab = ref('preview')

const stats = computed(() => validationResult.value?.stats || {})

const handleExport = async (format: 'yaml' | 'md') => {
  try {
    const blob = await apiService.exportResult(projectId, format)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `script.${format}`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success(`导出 ${format.toUpperCase()} 成功`)
  } catch (error) {
    ElMessage.error('导出失败')
  }
}

const handleValidate = async () => {
  try {
    validationResult.value = await apiService.validateResult(projectId)
    if (validationResult.value.valid) {
      ElMessage.success('Schema 校验通过')
    } else {
      ElMessage.warning('Schema 校验发现问题')
    }
  } catch (error) {
    ElMessage.error('校验失败')
  }
}

const formatYaml = () => {
  try {
    const obj = yaml.load(yamlText.value)
    yamlText.value = yaml.dump(obj, { allowUnicode: true, sortKeys: false })
  } catch (e) {
    ElMessage.error('YAML 格式错误')
  }
}

onMounted(async () => {
  try {
    result.value = await apiService.getResult(projectId)
    yamlText.value = yaml.dump(result.value, { allowUnicode: true, sortKeys: false })
    await handleValidate()
  } catch (error) {
    ElMessage.error('获取结果失败')
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="result-page">
    <div class="header">
      <h1 class="page-title">生成结果</h1>
      <p class="page-subtitle">剧本已生成完毕，可预览、编辑或导出</p>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-bar">
      <div class="stat-item">
        <span class="stat-value">{{ stats.chapters || 0 }}</span>
        <span class="stat-label">章节</span>
      </div>
      <div class="stat-item">
        <span class="stat-value">{{ stats.scenes || 0 }}</span>
        <span class="stat-label">场景</span>
      </div>
      <div class="stat-item">
        <span class="stat-value">{{ stats.dialogues || 0 }}</span>
        <span class="stat-label">对白</span>
      </div>
      <div class="stat-item">
        <span class="stat-value">{{ stats.actions || 0 }}</span>
        <span class="stat-label">动作</span>
      </div>
      <div class="stat-item">
        <span class="stat-value">{{ stats.narrations || 0 }}</span>
        <span class="stat-label">旁白</span>
      </div>
      <div class="validation-badge" :class="{ valid: validationResult?.valid }">
        <el-icon v-if="validationResult?.valid"><Check /></el-icon>
        <el-icon v-else><Warning /></el-icon>
        <span>{{ validationResult?.valid ? '校验通过' : '校验警告' }}</span>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="result-content">
      <!-- 左侧：YAML 编辑器 -->
      <div class="card yaml-panel">
        <div class="panel-header">
          <span class="panel-title">YAML 源码</span>
          <div class="panel-actions">
            <el-button size="small" @click="formatYaml">
              格式化
            </el-button>
          </div>
        </div>
        <el-input
          v-model="yamlText"
          type="textarea"
          :rows="30"
          class="yaml-editor"
          placeholder="YAML 内容..."
        />
      </div>

      <!-- 右侧：剧本预览 -->
      <div class="card preview-panel">
        <div class="panel-header">
          <span class="panel-title">剧本预览</span>
        </div>

        <div class="script-content">
          <template v-if="result">
            <!-- 故事设定 -->
            <div class="story-header">
              <h2 class="script-title">{{ result.story_bible?.title }}</h2>
              <div class="script-meta">
                <span>类型: {{ result.story_bible?.genre }}</span>
                <span>主题: {{ result.story_bible?.theme }}</span>
              </div>
            </div>

            <!-- 章节内容 -->
            <div
              v-for="chapter in result.chapters"
              :key="chapter.chapter_id"
              class="chapter-section"
            >
              <h3 class="chapter-title">{{ chapter.title }}</h3>

              <div
                v-for="scene in chapter.scenes"
                :key="scene.scene_id"
                class="scene-block"
              >
                <div class="scene-header">
                  <span class="scene-title">{{ scene.scene_title }}</span>
                  <span class="scene-info">{{ scene.location }} | {{ scene.time }}</span>
                </div>

                <div class="scene-summary">{{ scene.summary }}</div>

                <div class="beats-list">
                  <div
                    v-for="(beat, index) in scene.beats"
                    :key="index"
                    class="beat-item"
                    :class="beat.type"
                  >
                    <template v-if="beat.type === 'dialogue'">
                      <span class="speaker">{{ beat.speaker }}:</span>
                      <span class="content">{{ beat.content }}</span>
                    </template>
                    <template v-else-if="beat.type === 'action'">
                      <span class="beat-tag">【动作】</span>
                      <span class="content">{{ beat.content }}</span>
                    </template>
                    <template v-else-if="beat.type === 'narration'">
                      <span class="beat-tag">【旁白】</span>
                      <span class="content">{{ beat.content }}</span>
                    </template>
                    <template v-else-if="beat.type === 'transition'">
                      <span class="beat-tag">【转场】</span>
                      <span class="content">{{ beat.content }}</span>
                    </template>
                  </div>
                </div>
              </div>
            </div>
          </template>
        </div>
      </div>
    </div>

    <!-- 底部操作栏 -->
    <div class="bottom-actions">
      <el-button type="primary" @click="handleExport('yaml')">
        <el-icon><Download /></el-icon>
        导出 YAML
      </el-button>
      <el-button type="success" @click="handleExport('md')">
        <el-icon><Download /></el-icon>
        导出 Markdown
      </el-button>
      <el-button @click="handleValidate">
        <el-icon><Check /></el-icon>
        重新校验
      </el-button>
    </div>

    <!-- 校验错误列表 -->
    <div v-if="validationResult?.errors?.length > 0" class="errors-panel card">
      <h3 class="errors-title">
        <el-icon><Warning /></el-icon>
        校验问题
      </h3>
      <ul class="errors-list">
        <li v-for="(error, index) in validationResult.errors" :key="index">
          {{ error }}
        </li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
.result-page {
  min-height: 100vh;
  padding: 40px 20px;
  max-width: 1600px;
  margin: 0 auto;
}

.header {
  text-align: center;
  margin-bottom: 24px;
}

.stats-bar {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 32px;
  padding: 20px 32px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--primary-color);
}

.stat-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.validation-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: rgba(245, 158, 11, 0.1);
  border: 1px solid rgba(245, 158, 11, 0.3);
  border-radius: 20px;
  color: #fbbf24;
  font-size: 14px;
}

.validation-badge.valid {
  background: rgba(16, 185, 129, 0.1);
  border-color: rgba(16, 185, 129, 0.3);
  color: #10b981;
}

.result-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-bottom: 24px;
}

@media (max-width: 1200px) {
  .result-content {
    grid-template-columns: 1fr;
  }
}

.yaml-panel,
.preview-panel {
  display: flex;
  flex-direction: column;
  min-height: 600px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.panel-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.panel-actions {
  display: flex;
  gap: 8px;
}

.yaml-editor {
  flex: 1;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
}

:deep(.yaml-editor textarea) {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace !important;
  background: rgba(15, 15, 26, 0.6) !important;
  border: 1px solid var(--border-color) !important;
  color: #e2e8f0 !important;
  resize: none;
}

.preview-panel {
  overflow: hidden;
}

.script-content {
  flex: 1;
  overflow-y: auto;
  padding-right: 8px;
}

.story-header {
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-color);
}

.script-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.script-meta {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: var(--text-secondary);
}

.chapter-section {
  margin-bottom: 32px;
}

.chapter-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--primary-color);
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 2px solid var(--primary-color);
}

.scene-block {
  margin-bottom: 20px;
  padding: 16px;
  background: rgba(15, 15, 26, 0.4);
  border-radius: 12px;
  border: 1px solid rgba(99, 102, 241, 0.1);
}

.scene-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.scene-title {
  font-size: 15px;
  font-weight: 600;
  color: #c4b5fd;
}

.scene-info {
  font-size: 12px;
  color: var(--text-secondary);
}

.scene-summary {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 12px;
  font-style: italic;
}

.beats-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.beat-item {
  font-size: 14px;
  line-height: 1.6;
  padding: 8px 12px;
  border-radius: 6px;
}

.beat-item.dialogue {
  background: rgba(99, 102, 241, 0.1);
}

.beat-item.action {
  background: rgba(236, 72, 153, 0.1);
}

.beat-item.narration {
  background: rgba(16, 185, 129, 0.1);
}

.beat-item.transition {
  background: rgba(245, 158, 11, 0.1);
}

.speaker {
  font-weight: 600;
  color: #c4b5fd;
  margin-right: 8px;
}

.beat-tag {
  font-size: 12px;
  font-weight: 600;
  margin-right: 8px;
  opacity: 0.7;
}

.beat-item.action .beat-tag {
  color: #f472b6;
}

.beat-item.narration .beat-tag {
  color: #10b981;
}

.beat-item.transition .beat-tag {
  color: #fbbf24;
}

.content {
  color: var(--text-primary);
}

.bottom-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-bottom: 24px;
}

.errors-panel {
  background: rgba(245, 158, 11, 0.05);
  border-color: rgba(245, 158, 11, 0.2);
}

.errors-title {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #fbbf24;
  font-size: 14px;
  margin-bottom: 12px;
}

.errors-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.errors-list li {
  font-size: 13px;
  color: var(--text-secondary);
  padding: 4px 0;
  padding-left: 20px;
  position: relative;
}

.errors-list li::before {
  content: '•';
  position: absolute;
  left: 8px;
  color: #fbbf24;
}
</style>
