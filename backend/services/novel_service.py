"""
小说处理服务
包含文本预处理、章节识别、全局信息提取、剧本转换等核心逻辑
"""
import re
import json
import uuid
import yaml
from typing import List, Dict, Any, Optional
from datetime import datetime


# 章节识别正则表达式
CHAPTER_PATTERNS = [
    r"第[一二三四五六七八九十百千万零0-9]+章[^\n]*",
    r"第[一二三四五六七八九十百千万零0-9]+回[^\n]*",
    r"Chapter\s+\d+[^\n]*",
    r"CHAPTER\s+\d+[^\n]*",
    r"^\d+\.\s+.+",  # 1. 章节名
]


def normalize_text(text: str) -> str:
    """文本规范化"""
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")
    text = text.strip()
    return text


def split_chapters(text: str) -> List[Dict[str, Any]]:
    """识别小说章节"""
    lines = text.split("\n")
    chapters = []
    current_chapter = None
    current_content = []

    chapter_pattern = re.compile("|".join(CHAPTER_PATTERNS))

    for line in lines:
        if chapter_pattern.match(line.strip()):
            if current_chapter:
                content = "\n".join(current_content).strip()
                if content:
                    chapters.append({
                        "chapter_id": f"chapter_{len(chapters) + 1:03d}",
                        "title": current_chapter,
                        "content": content,
                        "word_count": len(content)
                    })
            current_chapter = line.strip()
            current_content = []
        else:
            if current_chapter is not None:
                current_content.append(line)

    # 处理最后一章
    if current_chapter:
        content = "\n".join(current_content).strip()
        if content:
            chapters.append({
                "chapter_id": f"chapter_{len(chapters) + 1:03d}",
                "title": current_chapter,
                "content": content,
                "word_count": len(content)
            })

    return chapters


def extract_story_bible_prompt(chapters: List[Dict]) -> str:
    """生成提取全局信息的 prompt"""
    # 取前两章内容用于提取全局信息
    excerpt = "\n\n".join([
        f"=== {ch['title']} ===\n{ch['content'][:2000]}"
        for ch in chapters[:2]
    ])

    prompt = f"""你是一名专业影视编剧助理。请从以下小说章节中提取全局剧本设定。

要求：
1. 提取故事标题、类型、主题、世界观、核心冲突。
2. 提取主要人物，包括姓名、角色定位、性格、目标、人物关系。
3. 提取重要地点。
4. 只输出 YAML，不要输出解释文字。

输出格式必须符合：

story_bible:
  title: ""
  genre: ""
  theme: ""
  world_setting: ""
  main_conflict: ""
  characters:
    - id: "char_001"
      name: ""
      role: ""
      personality: ""
      goal: ""
      relationship: ""
  locations:
    - id: "loc_001"
      name: ""
      description: ""

小说内容：
{excerpt}"""

    return prompt


def convert_chapter_prompt(story_bible: Dict, chapter: Dict) -> str:
    """生成单章转换的 prompt"""
    prompt = f"""你是一名专业影视剧本改编助手。请将下面小说章节改编为结构化剧本 YAML。

要求：
1. 保留原章节的主要剧情。
2. 将小说叙述拆分为若干场景 scenes。
3. 每个场景包含地点、时间、出场人物、剧情摘要和 beats。
4. beats 的 type 只能是 dialogue、action、narration、transition。
5. dialogue 必须包含 speaker。
6. action 和 narration 不需要 speaker。
7. 不要输出 Markdown，不要解释，只输出 YAML。

全局人物和设定：
{yaml.dump(story_bible, allow_unicode=True, sort_keys=False)}

当前章节：
=== {chapter['title']} ===
{chapter['content']}

输出格式：

chapter_id: "{chapter['chapter_id']}"
title: "{chapter['title']}"
scenes:
  - scene_id: ""
    scene_title: ""
    location: ""
    time: ""
    characters:
      - ""
    summary: ""
    beats:
      - type: "action"
        content: ""
      - type: "dialogue"
        speaker: ""
        content: ""
      - type: "narration"
        content: """""

    return prompt


def repair_yaml_prompt(schema_description: str, validation_error: str, broken_yaml: str) -> str:
    """生成修复 YAML 的 prompt"""
    prompt = f"""下面是一段不符合 Schema 的 YAML，请修复它。

要求：
1. 不要改变剧情含义。
2. 补全缺失字段。
3. 修正 YAML 缩进和字段名。
4. 只输出修复后的 YAML。

Schema 要求：
{schema_description}

错误信息：
{validation_error}

原始 YAML：
{broken_yaml}"""

    return prompt


def parse_yaml_response(response: str) -> Optional[Dict]:
    """解析 LLM 返回的 YAML 响应"""
    # 尝试提取 YAML 代码块
    yaml_match = re.search(r"```yaml\s*\n(.*?)\n```", response, re.DOTALL)
    if yaml_match:
        yaml_str = yaml_match.group(1)
    else:
        # 直接使用响应文本
        yaml_str = response

    try:
        data = yaml.safe_load(yaml_str)
        return data
    except yaml.YAMLError as e:
        print(f"YAML 解析错误: {e}")
        return None


def validate_script_yaml(data: Dict) -> tuple:
    """校验 YAML 数据结构"""
    errors = []

    # 检查顶层字段
    if "schema_version" not in data:
        errors.append("缺少 schema_version 字段")
    if "story_bible" not in data:
        errors.append("缺少 story_bible 字段")
    if "chapters" not in data:
        errors.append("缺少 chapters 字段")

    if errors:
        return False, errors

    # 检查 story_bible
    sb = data.get("story_bible", {})
    required_sb_fields = ["title", "genre", "theme", "world_setting", "main_conflict", "characters", "locations"]
    for field in required_sb_fields:
        if field not in sb:
            errors.append(f"story_bible 缺少 {field} 字段")

    # 检查 chapters
    chapters = data.get("chapters", [])
    for i, chapter in enumerate(chapters):
        if "chapter_id" not in chapter:
            errors.append(f"第 {i+1} 章缺少 chapter_id")
        if "title" not in chapter:
            errors.append(f"第 {i+1} 章缺少 title")
        if "scenes" not in chapter:
            errors.append(f"第 {i+1} 章缺少 scenes")

        # 检查 scenes
        for j, scene in enumerate(chapter.get("scenes", [])):
            if "scene_id" not in scene:
                errors.append(f"第 {i+1} 章第 {j+1} 场景缺少 scene_id")
            if "beats" not in scene:
                errors.append(f"第 {i+1} 章第 {j+1} 场景缺少 beats")

            # 检查 beats
            for k, beat in enumerate(scene.get("beats", [])):
                if "type" not in beat:
                    errors.append(f"第 {i+1} 章第 {j+1} 场景第 {k+1} 个 beat 缺少 type")
                if "content" not in beat:
                    errors.append(f"第 {i+1} 章第 {j+1} 场景第 {k+1} 个 beat 缺少 content")
                if beat.get("type") == "dialogue" and "speaker" not in beat:
                    errors.append(f"第 {i+1} 章第 {j+1} 场景第 {k+1} 个 dialogue 缺少 speaker")

    return len(errors) == 0, errors


def collect_stats(data: Dict) -> Dict:
    """收集统计数据"""
    stats = {
        "chapters": 0,
        "scenes": 0,
        "dialogues": 0,
        "actions": 0,
        "narrations": 0,
        "transitions": 0
    }

    for chapter in data.get("chapters", []):
        stats["chapters"] += 1
        for scene in chapter.get("scenes", []):
            stats["scenes"] += 1
            for beat in scene.get("beats", []):
                beat_type = beat.get("type", "")
                if beat_type == "dialogue":
                    stats["dialogues"] += 1
                elif beat_type == "action":
                    stats["actions"] += 1
                elif beat_type == "narration":
                    stats["narrations"] += 1
                elif beat_type == "transition":
                    stats["transitions"] += 1

    return stats


class NovelService:
    """小说处理服务类"""

    def __init__(self, llm_provider):
        self.llm_provider = llm_provider

    async def create_project(self, name: str, novel_text: str) -> Dict:
        """创建项目"""
        project_id = str(uuid.uuid4())[:8]
        project = {
            "project_id": project_id,
            "name": name,
            "novel_text": normalize_text(novel_text),
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "chapters": [],
            "story_bible": None,
            "result": None,
            "validation_result": None
        }
        return project

    async def analyze(self, project: Dict) -> Dict:
        """分析小说：识别章节，提取全局信息"""
        project["status"] = "analyzing"
        novel_text = project["novel_text"]

        # 识别章节
        chapters = split_chapters(novel_text)
        project["chapters"] = chapters

        if len(chapters) < 3:
            raise ValueError(f"检测到章节数不足 3 章，请上传至少 3 个章节的小说文本。当前识别到 {len(chapters)} 章。")

        # 提取全局信息
        system_prompt = "你是一个专业的影视剧本改编助手，擅长从小说中提取剧本设定。"
        prompt = extract_story_bible_prompt(chapters)

        response = await self.llm_provider.generate(prompt, system_prompt)
        story_bible = parse_yaml_response(response)

        if story_bible and "story_bible" in story_bible:
            project["story_bible"] = story_bible["story_bible"]
        else:
            # 使用默认结构
            project["story_bible"] = {
                "title": project["name"],
                "genre": "悬疑",
                "theme": "寻找真相",
                "world_setting": "现代都市",
                "main_conflict": "待补充",
                "characters": [],
                "locations": []
            }

        project["status"] = "analyzed"
        return project

    async def convert(self, project: Dict) -> Dict:
        """转换小说为剧本"""
        project["status"] = "converting"
        chapters = project["chapters"]
        story_bible = project.get("story_bible", {})

        script_chapters = []
        total = len(chapters)

        for i, chapter in enumerate(chapters):
            prompt = convert_chapter_prompt(story_bible, chapter)
            system_prompt = "你是一个专业的影视剧本改编助手，擅长将小说改编为结构化剧本 YAML。"

            response = await self.llm_provider.generate(prompt, system_prompt)
            chapter_data = parse_yaml_response(response)

            if chapter_data:
                script_chapters.append(chapter_data)
            else:
                # 创建默认章节结构
                script_chapters.append({
                    "chapter_id": chapter["chapter_id"],
                    "title": chapter["title"],
                    "scenes": [{
                        "scene_id": "scene_001",
                        "scene_title": "场景一",
                        "location": "待补充",
                        "time": "待补充",
                        "characters": [],
                        "summary": "内容待补充",
                        "beats": [{
                            "type": "narration",
                            "content": chapter["content"][:500] + "..."
                        }]
                    }]
                })

        # 构建最终结果
        result = {
            "schema_version": "1.0",
            "story_bible": story_bible,
            "chapters": script_chapters
        }

        # 校验
        valid, errors = validate_script_yaml(result)
        if not valid:
            # 尝试修复
            schema_desc = "需要包含 schema_version, story_bible, chapters 字段"
            repair_prompt = repair_yaml_prompt(schema_desc, "\n".join(errors), yaml.dump(result))
            repair_response = await self.llm_provider.generate(repair_prompt, system_prompt)
            fixed_result = parse_yaml_response(repair_response)
            if fixed_result:
                result = fixed_result
                valid, errors = validate_script_yaml(result)

        project["result"] = result
        project["validation_result"] = {
            "valid": valid,
            "errors": errors,
            "stats": collect_stats(result)
        }
        project["status"] = "completed"

        return project
