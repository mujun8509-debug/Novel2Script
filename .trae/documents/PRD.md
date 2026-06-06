# Novel2Script 产品需求文档

## 1. 产品概述

Novel2Script 是一款 AI 小说转结构化剧本工具，通过智能识别小说章节、提取人物设定和剧情要素，将小说自动转化为符合自定义 YAML Schema 的结构化剧本初稿。

**目标用户**：小说作者、编剧、影视制作团队、内容创作者

**核心价值**：将非结构化的文本小说转化为可编辑、可校验、可复用的结构化剧本数据，解决传统剧本创作效率低、格式不统一的问题。

---

## 2. 功能模块

### 2.1 核心功能列表

| 功能 | 描述 |
|------|------|
| 小说输入 | 支持粘贴文本和上传 TXT 文件两种方式 |
| 章节识别 | 自动识别小说章节，支持多种章节格式 |
| 全局信息提取 | 提取故事标题、类型、主题、世界观、人物、地点 |
| 分章剧本生成 | 按章节逐章生成结构化剧本 |
| YAML Schema 校验 | 后端 Pydantic 模型校验，自动修复格式错误 |
| 结果预览 | YAML 编辑器 + 剧本可视化预览双视图 |
| 导出功能 | 导出 YAML 文件和 Markdown 剧本 |

### 2.2 页面结构

1. **首页/输入页** - 小说输入、项目命名、开始解析
2. **章节预览页** - 展示识别结果、章节列表、字数统计
3. **生成进度页** - 实时展示转换进度和状态
4. **结果页** - YAML 编辑器 + 剧本预览 + 导出按钮

---

## 3. 核心流程

```
上传小说/粘贴小说
       ↓
  系统识别章节
       ↓
  AI 提取人物、地点、剧情线索
       ↓
  按章节生成结构化剧本 YAML
       ↓
  YAML 校验与自动修复
       ↓
  在线预览/编辑/导出
```

---

## 4. 技术架构

### 4.1 技术栈

- **前端**：Vue 3 + Vite + Element Plus
- **后端**：Python FastAPI
- **数据存储**：本地 JSON 文件
- **AI 模型**：统一 LLMProvider 接口，支持 OpenAI/Qwen/vLLM

### 4.2 后端 API 设计

| 接口 | 方法 | 功能 |
|------|------|------|
| `/api/projects` | POST | 创建项目，上传小说 |
| `/api/projects/{id}` | GET | 获取项目状态 |
| `/api/projects/{id}/analyze` | POST | 识别章节，提取全局信息 |
| `/api/projects/{id}/convert` | POST | 转换为 YAML 剧本 |
| `/api/projects/{id}/validate` | POST | 校验 YAML Schema |
| `/api/projects/{id}/export` | GET | 导出 YAML 文件 |

### 4.3 数据模型

```
ScriptYaml
├── schema_version: str
├── story_bible: StoryBible
│   ├── title: str
│   ├── genre: str
│   ├── theme: str
│   ├── world_setting: str
│   ├── main_conflict: str
│   ├── characters: List[Character]
│   └── locations: List[Location]
└── chapters: List[Chapter]
    ├── chapter_id: str
    ├── title: str
    └── scenes: List[Scene]
        ├── scene_id: str
        ├── scene_title: str
        ├── location: str
        ├── time: str
        ├── characters: List[str]
        ├── summary: str
        └── beats: List[Beat]
            ├── type: Literal["dialogue", "action", "narration", "transition"]
            ├── speaker: Optional[str]
            └── content: str
```

---

## 5. YAML Schema 设计亮点

1. **分层结构**：全局设定 (story_bible) + 章节 (chapters) + 场景 (scenes) + 剧本单元 (beats)
2. **类型明确**：dialogue/action/narration/transition 四种 beat 类型
3. **可扩展性**：支持后续生成分镜脚本、对白表、拍摄脚本
4. **校验保证**：Pydantic 模型确保数据完整性

---

## 6. 项目亮点

| 亮点 | 说明 |
|------|------|
| 结构化转换 | 不是简单文本生成，而是可编辑的 YAML 结构 |
| 自定义 Schema | 专为剧本设计，支持多场景、多角色 |
| 自动校验修复 | 后端 Schema 校验 + 自动修复流程 |
| 可视化预览 | YAML 编辑器 + 剧本预览双视图 |
| 长文本处理 | 章节切分 + 分段生成 + 最终合并 |
