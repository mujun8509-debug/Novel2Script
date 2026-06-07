# Novel2Script YAML Schema 设计说明

## 1. 设计目标

Novel2Script 的 YAML Schema 面向小说剧本化改编，核心目标是把小说文本转换成可编辑、可校验、可继续二创的结构化剧本。

设计重点：

1. **满足题目字段**：输出包含 `script`、`chapters`、`characters`、`scenes`、`elements`。
2. **层次清晰**：从全局剧本信息到章节、场景、剧本元素逐层展开。
3. **便于编辑**：YAML 可直接复制、导出和人工修改。
4. **便于校验**：后端检查必填字段、章节数量、元素类型和对白说话人。
5. **便于扩展**：后续可在 `elements` 或 `scenes` 下增加镜头、音效、分镜等字段。

## 2. 顶层结构

```yaml
schema_version: "1.0"
script:
  title: "剧本标题"
  genre: "悬疑"
  theme: "真相与救赎"
  world_setting: "现代都市"
  main_conflict: "主角寻找真相时遭遇阻挠"
  characters: []
  locations: []
  chapters: []
```

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `schema_version` | string | 是 | Schema 版本，当前为 `1.0` |
| `script` | object | 是 | 剧本主体 |

## 3. script 字段

`script` 保存全局设定和章节正文。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `title` | string | 是 | 剧本标题 |
| `genre` | string | 是 | 类型，如悬疑、爱情、科幻 |
| `theme` | string | 是 | 主题 |
| `world_setting` | string | 是 | 世界观/时代背景 |
| `main_conflict` | string | 是 | 核心冲突 |
| `characters` | array | 是 | 全局人物表 |
| `locations` | array | 是 | 全局地点表 |
| `chapters` | array | 是 | 章节列表，至少 3 个元素 |

## 4. characters 字段

```yaml
characters:
  - id: "char_001"
    name: "林澈"
    role: "protagonist"
    personality: "冷静、敏感"
    goal: "找到父亲死亡真相"
    relationship: "与沈眠是旧识"
```

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | string | 是 | 角色唯一标识 |
| `name` | string | 是 | 角色名称 |
| `role` | string | 是 | 角色定位 |
| `personality` | string | 否 | 性格描述 |
| `goal` | string | 否 | 角色目标 |
| `relationship` | string | 否 | 人物关系 |

## 5. chapters 字段

```yaml
chapters:
  - chapter_id: "chapter_001"
    title: "第一章 雨夜来客"
    scenes: []
```

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `chapter_id` | string | 是 | 章节唯一标识 |
| `title` | string | 是 | 章节标题 |
| `scenes` | array | 是 | 场景列表 |

规则：`script.chapters` 至少包含 3 个章节。

## 6. scenes 字段

```yaml
scenes:
  - scene_id: "scene_001"
    scene_title: "雨夜中的旧书店"
    location: "南城旧街旧书店"
    time: "夜晚"
    characters:
      - "林澈"
      - "沈眠"
    summary: "林澈进入旧书店，遇见多年未见的沈眠。"
    elements: []
```

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `scene_id` | string | 是 | 场景唯一标识 |
| `scene_title` | string | 是 | 场景标题 |
| `location` | string | 是 | 场景地点 |
| `time` | string | 是 | 时间 |
| `characters` | array | 是 | 出场人物名称 |
| `summary` | string | 是 | 场景摘要 |
| `elements` | array | 是 | 剧本元素列表 |

## 7. elements 字段

`elements` 是剧本中的最小叙事单元，用于表达动作、对白、旁白和转场。

```yaml
elements:
  - type: "action"
    content: "林澈推开旧书店的门，雨水顺着外套滴落。"
  - type: "dialogue"
    speaker: "沈眠"
    content: "你终于来了。"
  - type: "narration"
    content: "林澈没有立刻回答。"
  - type: "transition"
    content: "画面切换至：次日清晨。"
```

| `type` | 说明 | 必填字段 |
| --- | --- | --- |
| `dialogue` | 对白 | `type`、`speaker`、`content` |
| `action` | 动作描写 | `type`、`content` |
| `narration` | 旁白/叙述 | `type`、`content` |
| `transition` | 转场 | `type`、`content` |

## 8. 完整示例

完整三章示例见：`../examples/sample_output.yaml`。

该示例展示：

- `schema_version` 与 `script` 顶层结构
- `script.characters` 人物表
- 3 个以上 `script.chapters`
- 每章包含 `scenes`
- 每个场景包含 `elements`
- `dialogue`、`action`、`narration`、`transition` 四类元素

## 9. 与题目要求对应

| 题目要求 | Schema 实现 |
| --- | --- |
| 3 个章节以上小说 | `script.chapters` 至少包含 3 个章节 |
| 结构化剧本 | `script -> chapters -> scenes -> elements` |
| 包含人物 | `script.characters` |
| YAML 格式 | 输出纯 YAML，可复制、导出、人工编辑 |
| 可校验 | 后端按字段、类型和章节数量校验 |
