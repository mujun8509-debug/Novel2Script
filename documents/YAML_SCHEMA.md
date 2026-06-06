# Novel2Script YAML Schema 设计说明

## 1. 设计目标

本项目的 YAML Schema 专为**小说转剧本**场景设计，目标是：

1. **结构化表达**：将非结构化的小说文本转化为可编辑、可校验的结构化数据
2. **层次分明**：从全局设定到章节、场景、剧本单元，层层递进
3. **可扩展性**：支持后续生成分镜脚本、对白表、拍摄脚本或有声剧脚本
4. **工程化**：通过 Pydantic 模型进行数据校验，确保数据完整性

## 2. 顶层结构

```yaml
schema_version: "1.0"        # Schema 版本号，便于后续升级
story_bible: {...}           # 全局设定
chapters: [...]              # 章节列表
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| schema_version | string | 是 | Schema 版本号，当前为 "1.0" |
| story_bible | object | 是 | 全局故事设定 |
| chapters | array | 是 | 章节列表 |

## 3. story_bible 字段说明

story_bible 用于保存全局人物、地点、主题和核心冲突，解决长篇小说改编中**人物关系不一致、设定遗失**的问题。

```yaml
story_bible:
  title: "小说标题"
  genre: "类型"
  theme: "主题"
  world_setting: "世界观"
  main_conflict: "核心冲突"
  characters:
    - id: "char_001"
      name: "角色名"
      role: "protagonist|antagonist|supporting"
      personality: "性格描述"
      goal: "角色目标"
      relationship: "人物关系"
  locations:
    - id: "loc_001"
      name: "地点名称"
      description: "地点描述"
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| title | string | 是 | 故事标题 |
| genre | string | 是 | 故事类型（悬疑/爱情/科幻等） |
| theme | string | 是 | 故事主题 |
| world_setting | string | 是 | 世界观设定 |
| main_conflict | string | 是 | 核心冲突 |
| characters | array | 是 | 人物列表 |
| locations | array | 是 | 地点列表 |

### characters 子字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | string | 是 | 角色唯一标识 |
| name | string | 是 | 角色名称 |
| role | string | 是 | 角色定位（protagonist/antagonist/supporting） |
| personality | string | 否 | 性格描述 |
| goal | string | 否 | 角色目标 |
| relationship | string | 否 | 与其他角色的关系 |

## 4. chapters 字段说明

chapters 保留原小说章节结构，方便作者对照原文进行修改。

```yaml
chapters:
  - chapter_id: "chapter_001"
    title: "第一章 雨夜来客"
    scenes: [...]
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| chapter_id | string | 是 | 章节唯一标识 |
| title | string | 是 | 章节标题 |
| scenes | array | 是 | 场景列表 |

## 5. scenes 字段说明

scenes 将小说内容拆分为影视剧本常用的场景单位。

```yaml
scenes:
  - scene_id: "scene_001"
    scene_title: "雨夜中的旧书店"
    location: "南城旧街旧书店"
    time: "夜晚"
    characters:
      - "林澈"
      - "沈眠"
    summary: "林澈在雨夜进入旧书店，遇见多年未见的沈眠。"
    beats: [...]
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| scene_id | string | 是 | 场景唯一标识 |
| scene_title | string | 是 | 场景标题 |
| location | string | 是 | 地点 |
| time | string | 是 | 时间（白天/夜晚/清晨等） |
| characters | array | 是 | 出场人物列表 |
| summary | string | 是 | 场景剧情摘要 |
| beats | array | 是 | 剧本单元列表 |

## 6. beats 字段说明

beats 是剧本中最小的叙事单元，分为四种类型，方便后续扩展。

```yaml
beats:
  - type: "dialogue"          # 对白
    speaker: "沈眠"            # 说话者
    content: "你终于来了。"
  - type: "action"            # 动作描写
    content: "林澈推开旧书店的门，雨水顺着他的外套滴落。"
  - type: "narration"         # 旁白
    content: "林澈没有立刻回答，他的目光停在柜台后的黑色信封上。"
  - type: "transition"         # 转场
    content: "画面切换至：次日清晨，沈眠的公寓。"
```

| type 值 | 说明 | speaker 必填 |
|---------|------|--------------|
| dialogue | 对白 | 是 |
| action | 动作描写 | 否 |
| narration | 旁白 | 否 |
| transition | 转场 | 否 |

### type 设计原因

- **dialogue**：剧本核心，用于角色对白，必须标注说话者
- **action**：描述角色动作和表情，丰富视觉表现
- **narration**：叙述性文字，用于交代背景或心理
- **transition**：场景转换标记，便于剪辑和分镜

## 7. 设计原因

### 7.1 分层结构的优势

```
story_bible (全局) → chapters (章) → scenes (场) → beats (节)
```

这种分层设计的好处：

1. **全局一致性**：story_bible 统一管理人物和地点，避免各章节出现矛盾
2. **结构清晰**：便于人工复查和修改
3. **便于扩展**：可在现有结构上添加新字段（如镜头、音效等）

### 7.2 为什么要校验 Schema

传统 AI 生成剧本的问题：
- 输出格式不统一
- 字段缺失（如对话缺少 speaker）
- 类型错误（如 beats 是对象而非数组）

通过 Pydantic 模型校验：
- 确保必填字段存在
- 确保类型正确
- 自动修复常见错误

### 7.3 可扩展方向

当前 Schema 可扩展支持：

1. **分镜脚本**：在 scene 中添加 `shots` 字段
2. **对白表**：单独导出 beats 中 type=dialogue 的内容
3. **角色表**：从 story_bible.characters 导出
4. **有声剧脚本**：保留 beats 结构，移除 action

## 8. 示例 YAML

```yaml
schema_version: "1.0"
story_bible:
  title: "雨夜迷踪"
  genre: "悬疑"
  theme: "真相与救赎"
  world_setting: "现代都市"
  main_conflict: "林澈寻找失踪妹妹的过程中发现惊天秘密"
  characters:
    - id: "char_001"
      name: "林澈"
      role: "protagonist"
      personality: "冷静、敏感"
      goal: "找到妹妹失踪真相"
      relationship: "与沈眠是旧识"
    - id: "char_002"
      name: "沈眠"
      role: "supporting"
      personality: "神秘、睿智"
      goal: "保护旧书店的秘密"
      relationship: "林澈的旧友"
  locations:
    - id: "loc_001"
      name: "南城旧街"
      description: "潮湿、昏暗、充满旧时代气息"
    - id: "loc_002"
      name: "旧书店"
      description: "林澈与沈眠相遇的地方"
chapters:
  - chapter_id: "chapter_001"
    title: "第一章 雨夜来客"
    scenes:
      - scene_id: "scene_001"
        scene_title: "雨夜中的旧书店"
        location: "南城旧街旧书店"
        time: "夜晚"
        characters:
          - "林澈"
          - "沈眠"
        summary: "林澈在雨夜进入旧书店，遇见多年未见的沈眠。"
        beats:
          - type: "action"
            content: "林澈推开旧书店的门，雨水顺着他的外套滴落。"
          - type: "dialogue"
            speaker: "沈眠"
            content: "你终于来了。"
          - type: "narration"
            content: "林澈没有立刻回答，他的目光停在柜台后的黑色信封上。"
```
