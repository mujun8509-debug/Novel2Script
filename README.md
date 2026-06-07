# Novel2Script

AI 小说转结构化剧本工具。项目将 3 个章节以上的小说文本转换为可编辑、可校验、可导出的 YAML 剧本。

## 演示视频

**在线演示**：https://b23.tv/vJuR8wL

## 功能特性

- **智能章节识别**：识别 `第一章`、`第1章`、`Chapter 1`、序章、番外等常见格式。
- **内容感知分章**：未检测到章节标题时，结合时间跳转、地点变化、突发事件和段落节奏自动划分至少 3 章。
- **结构化剧本生成**：输出 `script -> chapters -> scenes -> elements` 结构。
- **人物与地点提取**：在 `script.characters` 和 `script.locations` 中保留全局设定。
- **Schema 校验与统计**：后端检查章节数、场景字段和动作/对白/旁白/转场元素。
- **可视化预览与导出**：前端支持 YAML 源码、剧本预览、复制、YAML 导出和 Markdown 导出。

## 技术栈与第三方依赖

后端：

- Python 3.9+
- FastAPI
- Uvicorn
- Pydantic
- httpx
- PyYAML
- python-multipart

前端：

- Node.js 18+
- Vue 3
- Vite
- TypeScript
- Vue Router
- Element Plus
- axios
- js-yaml

AI 调用：

- 统一 `LLMProvider` 接口，兼容 OpenAI 协议。
- 支持 `openai`、`qwen`、`deepseek`、`deepseekv4pro`、`vllm` 等配置。

## 项目结构

```text
project1/
├── backend/
│   ├── main.py
│   ├── models.py
│   ├── routers/api.py
│   ├── services/llm_provider.py
│   ├── services/novel_service.py
│   ├── requirements.txt
│   └── test_chapters.py
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── router/
│   │   ├── styles/
│   │   └── views/
│   ├── package.json
│   └── vite.config.ts
├── documents/
│   ├── YAML_SCHEMA.md
│   └── sample_novel.txt
└── examples/
    └── sample_output.yaml
```

## 快速开始

### 1. 配置后端环境

```bash
cd backend
pip install -r requirements.txt
```

复制 `.env.example` 为 `.env`，并填入自己的 API Key：

```bash
LLM_PROVIDER=deepseekv4pro
OPENAI_API_KEY=your_api_key_here
OPENAI_API_BASE=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat
```

### 2. 启动后端

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

后端健康检查：`http://localhost:8000/health`

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
```

访问：`http://localhost:3000`

## 使用流程

1. 在首页粘贴小说文本，或上传 TXT 文件。
2. 点击「载入示例小说」可直接使用内置三章样例；完整样例文本见 `documents/sample_novel.txt`。
3. 点击「开始解析」，系统识别章节并提取人物、地点和故事设定。
4. 在章节页选择至少 3 章，点击「生成所选 N 章 YAML 剧本」。
5. 在结果页查看可视化剧本或 YAML 源码。
6. 复制 YAML，或导出 `.yaml` / `.md` 文件。

## YAML Schema

详见 [documents/YAML_SCHEMA.md](documents/YAML_SCHEMA.md)。

核心结构：

```yaml
schema_version: "1.0"
script:
  title: "剧本标题"
  characters: []
  chapters:
    - chapter_id: "chapter_001"
      scenes:
        - scene_id: "scene_001"
          elements:
            - type: "dialogue"
              speaker: "角色"
              content: "对白"
```

完整示例见 [examples/sample_output.yaml](examples/sample_output.yaml)。

## 与题目要求对应关系

| 题目要求 | 项目实现 |
| --- | --- |
| 3 个章节以上小说文本 | 后端章节识别和内容感知分章均保证至少 3 章；前端生成按钮要求至少选择 3 章 |
| 自动转换为结构化剧本 | LLM 按章节生成场景、动作、对白、旁白和转场 |
| YAML 格式 | 结果页提供 YAML 源码、复制和 `.yaml` 导出 |
| 包含 script/chapters/characters/scenes/elements | YAML 顶层为 `script`，内部包含 `characters`、`chapters`，章节下包含 `scenes`，场景下包含 `elements` |
| YAML Schema 设计文档 | `documents/YAML_SCHEMA.md` |
| 可编辑剧本初稿 | YAML 文本可复制、格式化、导出并继续人工修改 |

## 原创功能与展示亮点

- 面向小说短剧化改编，不只是摘要生成。
- 自定义 `elements` 叙事单元，统一表达动作、对白、旁白和转场。
- 章节选择会真实参与后端转换，适合演示三章以上批量生成。
- 后端内置兜底结构，LLM 返回格式异常时仍能生成可编辑初稿。
- 结果页同时提供 YAML 源码和可视化剧本视图，便于答辩展示。

## 测试建议

```bash
# 后端章节识别测试
cd backend
python test_chapters.py

# 前端构建检查
cd frontend
npm run build
```

如当前机器没有全局 Python，请使用已安装的 Python 解释器运行后端测试。

## License

MIT
