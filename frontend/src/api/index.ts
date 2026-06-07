import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 120000
})

export interface ProjectCreate {
  name: string
  novel_text: string
}

export interface ChapterInfo {
  chapter_id: string
  title: string
  content: string
  word_count: number
}

export interface StoryBible {
  title: string
  genre: string
  theme: string
  world_setting: string
  main_conflict: string
  characters: Array<{
    id: string
    name: string
    role: string
    personality?: string
    goal?: string
    relationship?: string
  }>
  locations: Array<{
    id: string
    name: string
    description?: string
  }>
}

export interface ScriptElement {
  type: 'dialogue' | 'action' | 'narration' | 'transition'
  speaker?: string
  content: string
}

export interface Scene {
  scene_id: string
  scene_title: string
  location: string
  time: string
  characters: string[]
  summary: string
  elements: ScriptElement[]
}

export interface Chapter {
  chapter_id: string
  title: string
  summary?: string
  scenes: Scene[]
}

export interface ScriptResult {
  schema_version: string
  script: StoryBible & {
    chapters: Chapter[]
  }
}

export interface ProjectInfo {
  project_id: string
  name: string
  status: string
  created_at: string
  chapters_count: number
  has_story_bible: boolean
  has_result: boolean
}

export const apiService = {
  // 创建项目
  async createProject(data: ProjectCreate): Promise<{ project_id: string; status: string }> {
    const response = await api.post('/projects', data)
    return response.data
  },

  // 获取项目详情
  async getProject(id: string): Promise<ProjectInfo> {
    const response = await api.get(`/projects/${id}`)
    return response.data
  },

  // 获取项目分析结果
  async getAnalysis(id: string): Promise<{
    chapters: ChapterInfo[]
    story_bible: StoryBible
    chapters_count: number
  }> {
    const response = await api.get(`/projects/${id}/analysis`)
    return response.data
  },

  // 分析项目（识别章节、提取全局信息）
  async analyzeProject(id: string): Promise<{
    status: string
    chapters_count: number
    chapters: ChapterInfo[]
    story_bible: StoryBible
  }> {
    const response = await api.post(`/projects/${id}/analyze`)
    return response.data
  },

  // 转换剧本
  async convertProject(id: string, chapterIds?: string[]): Promise<{ status: string; message: string }> {
    const response = await api.post(`/projects/${id}/convert`, chapterIds?.length ? {
      chapter_ids: chapterIds
    } : undefined)
    return response.data
  },

  // 获取结果
  async getResult(id: string): Promise<ScriptResult> {
    const response = await api.get(`/projects/${id}/result`)
    return response.data
  },

  // 校验结果
  async validateResult(id: string): Promise<{
    valid: boolean
    errors: string[]
    stats: Record<string, number>
  }> {
    const response = await api.post(`/projects/${id}/validate`)
    return response.data
  },

  // 导出结果
  async exportResult(id: string, format: 'yaml' | 'md'): Promise<Blob> {
    const response = await api.get(`/projects/${id}/export`, {
      params: { format },
      responseType: 'blob'
    })
    return response.data
  }
}

export default api
