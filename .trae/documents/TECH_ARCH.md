# Novel2Script 技术架构文档

## 1. 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      前端 (Vue 3 + Vite)                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ 输入页   │→ │ 章节预览  │→ │ 生成进度  │→ │  结果页  │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────────┘
                              ↓ HTTP API
┌─────────────────────────────────────────────────────────────┐
│                    后端 (FastAPI + Python)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  路由层       │  │  服务层      │  │   数据层      │      │
│  │  - /api/*    │  │  - NovelService│ │ - Pydantic   │      │
│  │              │  │  - LLMProvider │ │ - JSON File  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              ↓
                    ┌──────────────────┐
                    │    LLM API       │
                    │ OpenAI/Qwen/vLLM │
                    └──────────────────┘
```

## 2. 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 前端框架 | Vue 3 + Vite | 快速构建单页应用 |
| UI 组件 | Element Plus | 提供表单、按钮、进度条等组件 |
| 后端框架 | FastAPI | 高性能 Python Web 框架 |
| 数据校验 | Pydantic | Schema 定义与校验 |
| AI 接口 | OpenAI Compatible | 统一 LLM 调用接口 |
| 存储 | 本地 JSON 文件 | 轻量级数据持久化 |

## 3. 目录结构

```
project1/
├── backend/
│   ├── main.py              # FastAPI 入口
│   ├── models.py            # Pydantic 数据模型
│   ├── services/
│   │   ├── novel_service.py # 小说处理服务
│   │   └── llm_provider.py  # LLM 统一接口
│   ├── routers/
│   │   └── api.py           # API 路由
│   └── schemas/
│       └── script_schema.py # YAML Schema 定义
├── frontend/
│   ├── src/
│   │   ├── App.vue
│   │   ├── main.js
│   │   ├── views/
│   │   │   ├── InputView.vue      # 输入页
│   │   │   ├── ChapterView.vue   # 章节预览页
│   │   │   ├── ProgressView.vue  # 生成进度页
│   │   │   └── ResultView.vue     # 结果页
│   │   └── api/
│   │       └── index.js          # API 调用
│   ├── index.html
│   └── package.json
└── documents/
    └── YAML_SCHEMA.md        # Schema 设计文档
```

## 4. API 详细设计

### 4.1 创建项目
```
POST /api/projects
Request: { "name": string, "novel_text": string }
Response: { "project_id": string, "status": string }
```

### 4.2 获取项目
```
GET /api/projects/{project_id}
Response: {
  "project_id": string,
  "name": string,
  "status": "pending" | "analyzing" | "converting" | "completed" | "error",
  "chapters": [...],
  "result": {...}
}
```

### 4.3 分析小说
```
POST /api/projects/{project_id}/analyze
Response: {
  "status": string,
  "chapters_count": number,
  "story_bible": {...}
}
```

### 4.4 转换剧本
```
POST /api/projects/{project_id}/convert
Response: {
  "status": string,
  "progress": number,
  "current_step": string
}
```

### 4.5 校验 Schema
```
POST /api/projects/{project_id}/validate
Response: {
  "valid": boolean,
  "errors": [...],
  "stats": { "chapters": number, "scenes": number, "dialogues": number }
}
```

### 4.6 导出结果
```
GET /api/projects/{project_id}/export?format=yaml|md
Response: 文件下载
```

## 5. 数据模型 (Pydantic)

```python
class Character(BaseModel):
    id: str
    name: str
    role: str
    personality: Optional[str] = None
    goal: Optional[str] = None
    relationship: Optional[str] = None

class Location(BaseModel):
    id: str
    name: str
    description: Optional[str] = None

class Beat(BaseModel):
    type: Literal["dialogue", "action", "narration", "transition"]
    speaker: Optional[str] = None
    content: str

class Scene(BaseModel):
    scene_id: str
    scene_title: str
    location: str
    time: str
    characters: List[str]
    summary: str
    beats: List[Beat]

class Chapter(BaseModel):
    chapter_id: str
    title: str
    scenes: List[Scene]

class StoryBible(BaseModel):
    title: str
    genre: str
    theme: str
    world_setting: str
    main_conflict: str
    characters: List[Character]
    locations: List[Location]

class ScriptYaml(BaseModel):
    schema_version: str
    story_bible: StoryBible
    chapters: List[Chapter]
```

## 6. LLM Provider 设计

```python
class LLMProvider:
    def __init__(self, provider_type: str, api_key: str, base_url: str):
        ...

    async def generate(self, prompt: str, system: str = None) -> str:
        """统一生成接口"""
        ...

# 支持的 provider
- "openai": OpenAI API
- "qwen": Qwen API
- "vllm": 本地 vLLM OpenAI-Compatible API
```

## 7. 核心流程时序

```
用户上传小说
    ↓
POST /api/projects → 创建项目
    ↓
POST /api/projects/{id}/analyze
    ↓
1. normalize_text() 文本规范化
    ↓
2. split_chapters() 章节识别
    ↓
3. extract_story_bible() 提取全局设定
    ↓
POST /api/projects/{id}/convert
    ↓
for each chapter:
    convert_chapter_to_script()
    ↓
validate_and_repair()
    ↓
GET /api/projects/{id}/result
```
