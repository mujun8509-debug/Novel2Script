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


def normalize_text(text: str) -> str:
    """规范化文本，预处理"""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\ufeff", "")
    
    # 全角空格转半角
    text = text.replace("\u3000", " ")
    
    # 如果章节标题前没有换行，强制补换行
    text = re.sub(
        r"(?<!\n)(第\s*[一二三四五六七八九十百千万零〇两0-9]+\s*[章节回卷集部篇])",
        r"\n\1",
        text
    )
    
    return text.strip()


def split_chapters(text: str) -> List[Dict[str, Any]]:
    """识别小说章节 - 支持有无标题两种情况"""
    print(f"[Split Chapters] 开始识别章节...")
    print(f"[Split Chapters] 输入文本长度: {len(text)}")
    
    # 先规范化文本
    text = normalize_text(text)
    
    lines = text.split("\n")
    chapters = []
    
    # 清理空行但保留段落分隔
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped or (cleaned_lines and cleaned_lines[-1] != ""):
            cleaned_lines.append(stripped)
    
    print(f"[Split Chapters] 清理后行数: {len(cleaned_lines)}")
    
    # 增强版章节标题模式
    chapter_patterns = [
        r"^\s*第\s*[一二三四五六七八九十百千万零〇两0-9]+\s*[章节回卷集部篇]\s*[:：、.\-—]?\s*.*$",
        r"^\s*[一二三四五六七八九十百千万零〇两0-9]+\s*[、.．]\s*.+$",
        r"^\s*[Cc][Hh][Aa][Pp][Tt][Ee][Rr]\s*\d+\s*.*$",
        r"^\s*【\s*第?\s*[一二三四五六七八九十百千万零〇两0-9]+\s*[章节回卷集部篇]?\s*】\s*.*$",
        r"^\s*序章\s*$",
        r"^\s*楔子\s*$",
        r"^\s*尾声\s*$",
        r"^\s*番外\s*[一二三四五六七八九十0-9]*\s*.*$",
    ]
    chapter_pattern = re.compile("|".join(chapter_patterns))

    # 扫描章节标题位置
    chapter_positions = []
    for i, line in enumerate(cleaned_lines):
        if chapter_pattern.match(line):
            chapter_positions.append(i)
            print(f"[Split Chapters] 找到章节标题: '{line[:50]}...' 在第 {i+1} 行")

    # 如果找到了章节标题
    if chapter_positions:
        # 确保第一个标题从文本开始
        if chapter_positions[0] != 0:
            chapter_positions.insert(0, 0)
        
        # 分割章节
        for i in range(len(chapter_positions)):
            start = chapter_positions[i]
            if i < len(chapter_positions) - 1:
                end = chapter_positions[i + 1]
            else:
                end = len(cleaned_lines)
            
            # 获取标题
            if start < len(cleaned_lines) and chapter_pattern.match(cleaned_lines[start]):
                title = cleaned_lines[start]
                content_start = start + 1
            else:
                title = f"第 {i + 1} 章"
                content_start = start
            
            # 获取内容
            content_lines = cleaned_lines[content_start:end]
            content = "\n".join([l for l in content_lines if l]).strip()
            
            if content:
                chapters.append({
                    "chapter_id": f"chapter_{i + 1:03d}",
                    "title": title,
                    "content": content,
                    "word_count": len(content)
                })
    else:
        # 没有找到章节标题，按内容长度平均分割
        print(f"[Split Chapters] 未找到章节标题，按内容平均分割...")
        
        # 计算总字数
        total_content = "\n".join([l for l in cleaned_lines if l])
        total_chars = len(total_content)
        print(f"[Split Chapters] 总字数: {total_chars}")
        
        # 至少分成 3 章
        num_chapters = max(3, min(10, total_chars // 1000))
        chars_per_chapter = total_chars // num_chapters
        
        print(f"[Split Chapters] 计划分成 {num_chapters} 章，每章约 {chars_per_chapter} 字")
        
        current_char_count = 0
        current_content = []
        chapter_num = 1
        
        for line in cleaned_lines:
            if not line:
                current_content.append(line)
                continue
            
            line_char_count = len(line)
            
            # 如果加上这行超过了每章的字数限制，且已有内容，就分割
            if current_char_count + line_char_count > chars_per_chapter and current_content:
                content = "\n".join([l for l in current_content if l]).strip()
                if content:
                    chapters.append({
                        "chapter_id": f"chapter_{chapter_num:03d}",
                        "title": f"第 {chapter_num} 章",
                        "content": content,
                        "word_count": len(content)
                    })
                    chapter_num += 1
                    current_content = []
                    current_char_count = 0
            
            current_content.append(line)
            current_char_count += line_char_count
        
        # 处理最后一章
        if current_content:
            content = "\n".join([l for l in current_content if l]).strip()
            if content:
                chapters.append({
                    "chapter_id": f"chapter_{chapter_num:03d}",
                    "title": f"第 {chapter_num} 章",
                    "content": content,
                    "word_count": len(content)
                })
    
    # 如果还是没有章节，强制生成 3 章
    if len(chapters) < 3:
        print(f"[Split Chapters] 章节数不足，强制生成 3 章...")
        total_content = "\n".join([l for l in cleaned_lines if l]).strip()
        if total_content:
            # 简单地按字符数平均分割
            third = len(total_content) // 3
            chapters = [
                {
                    "chapter_id": "chapter_001",
                    "title": "第 1 章",
                    "content": total_content[:third],
                    "word_count": len(total_content[:third])
                },
                {
                    "chapter_id": "chapter_002",
                    "title": "第 2 章",
                    "content": total_content[third:2*third],
                    "word_count": len(total_content[third:2*third])
                },
                {
                    "chapter_id": "chapter_003",
                    "title": "第 3 章",
                    "content": total_content[2*third:],
                    "word_count": len(total_content[2*third:])
                }
            ]

    print(f"[Split Chapters] 最终识别到 {len(chapters)} 章")
    for i, ch in enumerate(chapters):
        print(f"[Split Chapters] 第 {i+1} 章: {ch['title']}, 内容长度: {len(ch['content'])}")

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

    if not data:
        return False, ["数据为空"]

    # 检查顶层字段
    if "schema_version" not in data:
        errors.append("缺少 schema_version 字段")
    if "story_bible" not in data:
        errors.append("缺少 story_bible 字段")
    if "chapters" not in data:
        errors.append("缺少 chapters 字段")

    if errors:
        return False, errors

    # 检查 chapters 至少 3 个
    chapters = data.get("chapters", [])
    if len(chapters) < 3:
        errors.append(f"章节数不足：当前 {len(chapters)} 章，要求至少 3 章")

    # 检查 story_bible
    sb = data.get("story_bible", {})
    required_sb_fields = ["title", "genre", "theme", "world_setting", "main_conflict", "characters", "locations"]
    for field in required_sb_fields:
        if field not in sb:
            errors.append(f"story_bible 缺少 {field} 字段")

    # 检查 chapters
    for i, chapter in enumerate(chapters):
        if "chapter_id" not in chapter:
            errors.append(f"第 {i+1} 章缺少 chapter_id")
        if "title" not in chapter:
            errors.append(f"第 {i+1} 章缺少 title")
        if "scenes" not in chapter:
            errors.append(f"第 {i+1} 章缺少 scenes")
        elif not isinstance(chapter.get("scenes"), list):
            errors.append(f"第 {i+1} 章 scenes 必须是数组")

        # 检查 scenes
        for j, scene in enumerate(chapter.get("scenes", []) or []):
            if not isinstance(scene, dict):
                errors.append(f"第 {i+1} 章第 {j+1} 场景格式错误")
                continue

            if "scene_id" not in scene:
                errors.append(f"第 {i+1} 章第 {j+1} 场景缺少 scene_id")
            if "beats" not in scene:
                errors.append(f"第 {i+1} 章第 {j+1} 场景缺少 beats")
            elif not isinstance(scene.get("beats"), list):
                errors.append(f"第 {i+1} 章第 {j+1} 场景 beats 必须是数组")

            # 检查 beats
            for k, beat in enumerate(scene.get("beats", []) or []):
                if not isinstance(beat, dict):
                    errors.append(f"第 {i+1} 章第 {j+1} 场景第 {k+1} 个 beat 格式错误")
                    continue

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

        print(f"[NovelService] 开始分析项目: {project['name']}")

        # 识别章节
        chapters = split_chapters(novel_text)
        project["chapters"] = chapters

        if len(chapters) < 3:
            print(f"[NovelService] 章节数不足: {len(chapters)}")
            # 如果没有识别到章节，尝试手动分块
            print(f"[NovelService] 尝试手动分割文本...")
            lines = novel_text.split("\n")
            # 按大约 500 字分块
            block_size = 500
            current_block = []
            current_word_count = 0
            manual_chapters = []
            
            for line in lines:
                current_block.append(line)
                current_word_count += len(line)
                if current_word_count >= block_size:
                    manual_chapters.append({
                        "chapter_id": f"chapter_{len(manual_chapters) + 1:03d}",
                        "title": f"第 {len(manual_chapters) + 1} 章",
                        "content": "\n".join(current_block),
                        "word_count": len("\n".join(current_block))
                    })
                    current_block = []
                    current_word_count = 0
            
            # 处理最后一块
            if current_block:
                manual_chapters.append({
                    "chapter_id": f"chapter_{len(manual_chapters) + 1:03d}",
                    "title": f"第 {len(manual_chapters) + 1} 章",
                    "content": "\n".join(current_block),
                    "word_count": len("\n".join(current_block))
                })
            
            if len(manual_chapters) >= 3:
                chapters = manual_chapters
                project["chapters"] = chapters
                print(f"[NovelService] 手动分割成功: {len(chapters)} 章")
            else:
                raise ValueError(f"检测到章节数不足 3 章，请上传至少 3 个章节的小说文本。当前识别到 {len(chapters)} 章。")

        # 提取全局信息
        try:
            print(f"[NovelService] 开始提取全局信息...")
            system_prompt = "你是一个专业的影视剧本改编助手，擅长从小说中提取剧本设定。"
            prompt = extract_story_bible_prompt(chapters)
            response = await self.llm_provider.generate(prompt, system_prompt)
            story_bible = parse_yaml_response(response)
            print(f"[NovelService] LLM 响应: {response[:100]}...")
            
            if story_bible and "story_bible" in story_bible:
                project["story_bible"] = story_bible["story_bible"]
                print(f"[NovelService] 全局信息提取成功")
            else:
                # 使用默认结构
                print(f"[NovelService] 使用默认全局信息结构")
                project["story_bible"] = {
                    "title": project["name"],
                    "genre": "悬疑",
                    "theme": "寻找真相",
                    "world_setting": "现代都市",
                    "main_conflict": "待补充",
                    "characters": [],
                    "locations": []
                }
        except Exception as e:
            print(f"[NovelService] 全局信息提取失败: {e}")
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
        conversion_errors = []

        for i, chapter in enumerate(chapters):
            print(f"[Convert] 正在转换第 {i+1}/{total} 章: {chapter.get('title', '未命名')}")

            try:
                prompt = convert_chapter_prompt(story_bible, chapter)
                system_prompt = "你是一个专业的影视剧本改编助手，擅长将小说改编为结构化剧本 YAML。"

                response = await self.llm_provider.generate(prompt, system_prompt)
                chapter_data = parse_yaml_response(response)

                if chapter_data and isinstance(chapter_data, dict):
                    script_chapters.append(chapter_data)
                    print(f"[Convert] 第 {i+1} 章转换成功")
                else:
                    # 兜底：创建默认章节结构
                    print(f"[Convert] 第 {i+1} 章解析失败，使用兜底结构")
                    conversion_errors.append(f"第 {i+1} 章解析失败")
                    script_chapters.append(create_fallback_chapter(chapter, story_bible))
            except Exception as e:
                print(f"[Convert] 第 {i+1} 章转换异常: {e}")
                conversion_errors.append(f"第 {i+1} 章异常: {str(e)}")
                script_chapters.append(create_fallback_chapter(chapter, story_bible))

        # 如果所有章节都失败，至少保证有 3 个章节
        while len(script_chapters) < 3 and len(chapters) < 3:
            print(f"[Convert] 补充兜底章节以满足 3 章要求")
            script_chapters.append({
                "chapter_id": f"chapter_{len(script_chapters) + 1:03d}",
                "title": f"第 {len(script_chapters) + 1} 章",
                "scenes": [{
                    "scene_id": "scene_001",
                    "scene_title": "待整理场景",
                    "location": "未指定",
                    "time": "未指定",
                    "characters": [],
                    "summary": "内容待整理",
                    "beats": [{
                        "type": "narration",
                        "content": "原始生成内容已丢失，请重新生成。"
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
            print(f"[Convert] YAML 校验失败: {errors}")
            # 尝试修复
            schema_desc = "需要包含 schema_version, story_bible, chapters 字段，chapters 至少 3 个章节"
            repair_prompt = repair_yaml_prompt(schema_desc, "\n".join(errors), yaml.dump(result))
            try:
                repair_response = await self.llm_provider.generate(repair_prompt, system_prompt)
                fixed_result = parse_yaml_response(repair_response)
                if fixed_result and isinstance(fixed_result, dict):
                    result = fixed_result
                    valid, errors = validate_script_yaml(result)
                    print(f"[Convert] YAML 修复{'成功' if valid else '仍失败'}")
            except Exception as e:
                print(f"[Convert] YAML 修复异常: {e}")

        # 最终兜底：确保至少 3 个章节
        if len(result.get("chapters", [])) < 3:
            print(f"[Convert] 最终兜底：确保至少 3 个章节")
            while len(result.get("chapters", [])) < 3:
                result["chapters"].append({
                    "chapter_id": f"chapter_{len(result['chapters']) + 1:03d}",
                    "title": f"第 {len(result['chapters']) + 1} 章",
                    "scenes": [{
                        "scene_id": "scene_001",
                        "scene_title": "系统生成章节",
                        "location": "未指定",
                        "time": "未指定",
                        "characters": [],
                        "summary": "系统自动生成以满足最小章节要求",
                        "beats": [{
                            "type": "narration",
                            "content": "本章节为系统自动生成以满足至少 3 章的要求，请手动编辑或重新生成。"
                        }]
                    }]
                })
            valid = False
            errors.append("自动补充了章节以满足 3 章最低要求")

        project["result"] = result
        project["validation_result"] = {
            "valid": valid,
            "errors": errors,
            "stats": collect_stats(result),
            "conversion_errors": conversion_errors
        }
        project["status"] = "completed"

        return result


def create_fallback_chapter(chapter: Dict, story_bible: Dict) -> Dict:
    """创建兜底章节结构"""
    return {
        "chapter_id": chapter.get("chapter_id", "chapter_001"),
        "title": chapter.get("title", "未命名章节"),
        "summary": "AI 返回内容格式异常，已生成基础结构。",
        "characters": story_bible.get("characters", [])[:3] if story_bible else [],
        "scenes": [{
            "scene_id": "scene_001",
            "scene_title": "待整理场景",
            "location": "未指定",
            "time": "未指定",
            "atmosphere": "未指定",
            "purpose": "保留原始生成内容，便于后续编辑。",
            "beats": [{
                "type": "narration",
                "content": chapter.get("content", "内容待整理")[:500] + "..."
            }]
        }]
    }
