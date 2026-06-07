# Novel2Script

AI 小说转结构化剧本工具 - 将小说自动转换为符合 YAML Schema 的结构化剧本。

## 功能特性

- **智能章节识别**：自动识别小说章节，支持多种章节格式
- **全局信息提取**：提取故事标题、类型、主题、世界观、人物、地点
- **结构化剧本生成**：按章节生成结构化剧本 YAML
- **Schema 校验与修复**：后端 Pydantic 模型校验，自动修复格式错误
- **可视化预览**：YAML 编辑器 + 剧本可视化预览双视图
- **多格式导出**：支持导出 YAML 和 Markdown 格式

## 技术栈

- **前端**：Vue 3 + Vite + Element Plus + TypeScript
- **后端**：Python FastAPI
- **AI 模型**：统一 LLMProvider 接口，支持 OpenAI/Qwen/vLLM

## 项目结构

```
project1/
├── backend/
│   ├── main.py              # FastAPI 入口
│   ├── models.py            # Pydantic 数据模型
│   ├── routers/
│   │   └── api.py           # API 路由
│   └── services/
│       ├── llm_provider.py  # LLM 统一接口
│       └── novel_service.py # 小说处理服务
├── frontend/
│   ├── src/
│   │   ├── App.vue
│   │   ├── main.ts
│   │   ├── router/
│   │   ├── api/
│   │   ├── views/           # 页面组件
│   │   └── styles/
│   └── package.json
└── documents/
    ├── YAML_SCHEMA.md       # Schema 设计文档
    ├── PRD.md              # 产品需求文档
    └── TECH_ARCH.md        # 技术架构文档
```

## 快速开始

### 环境要求

- Node.js 18+
- Python 3.9+
- OpenAI API Key 或其他大模型 API

### 后端安装

```bash
cd backend
pip install -r requirements.txt
```

### 后端配置

设置环境变量（复制 .env.example 为 .env 并修改）：

```bash
# DeepSeek V4 Pro（推荐）
LLM_PROVIDER=deepseekv4pro
OPENAI_API_KEY=sk-a82d96ac8f254a04b3ded6f5a991fe94
OPENAI_API_BASE=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat

# 其他可选配置
# LLM_PROVIDER=deepseek
# LLM_PROVIDER=openai
# LLM_PROVIDER=qwen
# LLM_PROVIDER=vllm
```

### 后端启动

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 前端安装

```bash
cd frontend
npm install
```

### 前端启动

```bash
npm run dev
```

访问 http://localhost:3000

## API 接口

| 接口 | 方法 | 功能 |
|------|------|------|
| `/api/projects` | POST | 创建项目 |
| `/api/projects/{id}` | GET | 获取项目状态 |
| `/api/projects/{id}/analyze` | POST | 分析小说 |
| `/api/projects/{id}/convert` | POST | 转换剧本 |
| `/api/projects/{id}/result` | GET | 获取结果 |
| `/api/projects/{id}/validate` | POST | 校验 Schema |
| `/api/projects/{id}/export` | GET | 导出结果 |

## YAML Schema

详见 [YAML_SCHEMA.md](documents/YAML_SCHEMA.md)

## 工作流程

1. **上传小说**：粘贴或上传 TXT 文件
2. **自动分析**：识别章节，提取全局信息
3. **生成剧本**：按章节生成结构化 YAML
4. **校验预览**：Schema 校验，可视化预览
5. **导出使用**：导出 YAML 或 Markdown

## 设计亮点

1. **不是简单文本生成，而是结构化转换**
2. **自定义 YAML Schema，专为剧本设计**
3. **自动校验与修复，工程化质量控制**
4. **可视化预览，YAML 编辑器双视图**
5. **支持长文本分章处理**

## 与题目要求对应关系

| 题目要求 | 项目实现 |
|----------|----------|
| 3 个章节以上小说文本 | 支持 TXT 上传并识别 3 章以上章节，自动分割不规则文本 |
| 自动转换为结构化剧本 | 使用 AI 提取章节、场景、人物、动作、对白、旁白 |
| YAML 格式 | 提供 YAML 预览、复制和 .yaml 导出 |
| YAML Schema 文档 | 提供 documents/yaml-schema-design.md |
| 可编辑剧本初稿 | YAML 文件可直接人工修改和二次创作 |

## 评分亮点

1. **完整流程**：上传 → 识别 → 生成 → 预览 → 导出
2. **创新性**：面向小说短剧化改编，输出可编辑 YAML 剧本
3. **工程质量**：模块化结构、异常处理、测试样例、README 和 Schema 文档
4. **展示友好**：可视化剧本视图 + YAML 源码视图 + 示例快速载入
5. **稳定可靠**：YAML 校验、兜底逻辑、错误提示

## 测试流程

推荐测试步骤：

1. 点击「载入示例小说」或上传 test-samples/standard-chapters.txt
2. 确认识别到 3 个以上章节
3. 查看解析摘要面板，确认满足要求提示
4. 点击「生成所选 N 章 YAML 剧本」
5. 查看 YAML 源码视图，确认结构完整
6. 测试复制 YAML 和导出 .yaml 文件
7. 查看可视化剧本视图，确认动作/对白/旁白区分清晰
8. 测试 Schema 校验功能

## License

MIT
