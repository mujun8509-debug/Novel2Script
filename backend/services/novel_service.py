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


def clamp(value: int, min_value: int, max_value: int) -> int:
    """限制数值范围。"""
    return max(min_value, min(max_value, value))


def score_narrative_boundary(prev_para: str, next_para: str) -> int:
    """给无标题文本中的段落边界打分，分数越高越适合作为章节分界。"""
    score = 0
    prev_tail = prev_para[-80:]
    next_head = next_para[:120]

    strong_start_patterns = [
        r"^(第二天|次日|翌日|几天后|数日后|多年后|十年后|当天晚上|那天晚上|接下来的几天)",
        r"^(清晨|黎明|上午|中午|午后|傍晚|黄昏|夜里|深夜|雨停后)",
        r"^(与此同时|另一边|同一时间|后来|之后|随后)",
    ]
    location_shift_patterns = [
        r"(来到|走进|回到|离开|赶到|抵达).{0,12}(旧书店|公寓|档案馆|工厂|学校|医院|办公室|街|门口|房间|大厅|车站)",
        r"^(门外|店里|房间里|街上|雨幕中|档案馆|废弃工厂|南城旧街)",
    ]
    event_shift_patterns = [
        r"^(就在这时|这时|突然|忽然|门铃再次响起|电话响起|外面传来|门外站着)",
        r"(陷入了沉默|必须|决定|计划|真相|秘密|失踪|被杀|跟踪)",
    ]

    if any(re.search(pattern, next_head) for pattern in strong_start_patterns):
        score += 8
    if any(re.search(pattern, next_head) for pattern in location_shift_patterns):
        score += 5
    if any(re.search(pattern, next_head) for pattern in event_shift_patterns):
        score += 3
    if re.search(r"[？?!！。]$", prev_tail.strip()):
        score += 1
    if "。" in prev_tail and re.match(r'^[“"]', next_head):
        score += 1
    if re.search(r"(会是谁|怎么办|为什么|什么版本|必须去|今晚就去)[？?。！””\"]*$", prev_tail.strip()):
        score += 2

    return score


def estimate_auto_chapter_count(total_chars: int, paragraphs: List[str]) -> int:
    """根据文本长度和剧情转场密度估算无标题文本的章节数。"""
    length_based = round(total_chars / 1800)
    transition_count = 0
    for index in range(len(paragraphs) - 1):
        if score_narrative_boundary(paragraphs[index], paragraphs[index + 1]) >= 6:
            transition_count += 1

    # 短文本仍满足至少 3 章；长文本会随篇幅和强转场自然增加章节。
    count = max(3, length_based, transition_count + 1)
    max_by_length = max(3, (total_chars + 899) // 900)
    return clamp(count, 3, min(10, max_by_length))


def infer_auto_chapter_title(chapter_num: int, content: str) -> str:
    """为自动划分章节生成可读标题。"""
    first_line = next((line.strip() for line in content.split("\n") if line.strip()), "")
    title_seed = re.sub(r"^[“\"'「『]+|[。！？!?，,；;：“”\"'」』]+$", "", first_line)
    title_seed = title_seed[:18] or "剧情推进"
    return f"第 {chapter_num} 章（自动分章：{title_seed}）"


def build_auto_chapter(paragraphs: List[str], start: int, end: int, chapter_num: int) -> Dict[str, Any]:
    """按段落区间构建自动章节。end 为闭区间。"""
    content = "\n".join(paragraphs[start:end + 1]).strip()
    return {
        "chapter_id": f"chapter_{chapter_num:03d}",
        "title": infer_auto_chapter_title(chapter_num, content),
        "content": content,
        "word_count": len(content)
    }


def split_untitled_text_by_content(cleaned_lines: List[str]) -> List[Dict[str, Any]]:
    """无章节标题时，优先根据剧情转场和段落节奏划分章节。"""
    paragraphs = [line.strip() for line in cleaned_lines if line.strip()]
    if not paragraphs:
        return []
    if len(paragraphs) < 3:
        return [build_auto_chapter(paragraphs, 0, len(paragraphs) - 1, 1)]

    total_chars = sum(len(paragraph) for paragraph in paragraphs)
    target_count = estimate_auto_chapter_count(total_chars, paragraphs)
    target_size = max(1, total_chars // target_count)
    min_size = max(180, int(target_size * 0.45))
    max_size = max(min_size + 1, int(target_size * 1.75))

    print(f"[Split Chapters] 未找到章节标题，启用内容感知分章...")
    print(f"[Split Chapters] 总字数: {total_chars}")
    print(f"[Split Chapters] 计划分成 {target_count} 章，每章目标约 {target_size} 字")

    prefix_lengths = [0]
    for paragraph in paragraphs:
        prefix_lengths.append(prefix_lengths[-1] + len(paragraph))

    chapters = []
    start = 0
    chapter_num = 1

    while start < len(paragraphs) and chapter_num <= target_count:
        remaining_chapters = target_count - chapter_num + 1
        if remaining_chapters == 1:
            chapters.append(build_auto_chapter(paragraphs, start, len(paragraphs) - 1, chapter_num))
            break

        best_boundary = None
        best_score = None
        fallback_boundary = None
        fallback_distance = None

        for boundary in range(start, len(paragraphs) - 1):
            segment_len = prefix_lengths[boundary + 1] - prefix_lengths[start]
            remaining_len = prefix_lengths[-1] - prefix_lengths[boundary + 1]

            if segment_len < min_size:
                continue
            if remaining_len < min_size * (remaining_chapters - 1):
                break

            distance = abs(segment_len - target_size)
            if fallback_distance is None or distance < fallback_distance:
                fallback_boundary = boundary
                fallback_distance = distance

            boundary_score = score_narrative_boundary(paragraphs[boundary], paragraphs[boundary + 1])
            length_penalty = distance / max(target_size, 1)
            combined_score = boundary_score * 10 - length_penalty * 4

            if best_score is None or combined_score > best_score:
                best_boundary = boundary
                best_score = combined_score

            if segment_len >= max_size and boundary_score < 6:
                break

        boundary = best_boundary if best_boundary is not None and best_score is not None and best_score > -2 else fallback_boundary
        if boundary is None:
            boundary = min(len(paragraphs) - 2, start)

        chapters.append(build_auto_chapter(paragraphs, start, boundary, chapter_num))
        print(
            f"[Split Chapters] 自动分章 {chapter_num}: 段落 {start + 1}-{boundary + 1}, "
            f"长度 {chapters[-1]['word_count']}"
        )

        start = boundary + 1
        chapter_num += 1

    return chapters


def ensure_minimum_chapters(chapters: List[Dict[str, Any]], cleaned_lines: List[str]) -> List[Dict[str, Any]]:
    """确保至少 3 章；优先按段落重分，而不是切断句子。"""
    if len(chapters) >= 3:
        return chapters

    print(f"[Split Chapters] 章节数不足，按段落补足到 3 章...")
    paragraphs = [line.strip() for line in cleaned_lines if line.strip()]
    if not paragraphs:
        return chapters
    if len(paragraphs) < 3:
        total_content = "\n".join(paragraphs).strip()
        if not total_content:
            return chapters
        third = max(1, len(total_content) // 3)
        chunks = [total_content[:third], total_content[third:2 * third], total_content[2 * third:]]
        return [
            {
                "chapter_id": f"chapter_{index + 1:03d}",
                "title": infer_auto_chapter_title(index + 1, chunk),
                "content": chunk,
                "word_count": len(chunk)
            }
            for index, chunk in enumerate(chunks)
        ]

    total_chars = sum(len(paragraph) for paragraph in paragraphs)
    target_size = max(1, total_chars // 3)
    rebuilt = []
    start = 0

    for chapter_num in range(1, 4):
        if chapter_num == 3:
            end = len(paragraphs) - 1
        else:
            end = start
            while end < len(paragraphs) - 1:
                current_len = sum(len(paragraph) for paragraph in paragraphs[start:end + 1])
                remaining_paragraphs = len(paragraphs) - end - 1
                if current_len >= target_size and remaining_paragraphs >= (3 - chapter_num):
                    break
                end += 1
        rebuilt.append(build_auto_chapter(paragraphs, start, end, chapter_num))
        start = end + 1

    return rebuilt


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
        chapters = split_untitled_text_by_content(cleaned_lines)
    
    chapters = ensure_minimum_chapters(chapters, cleaned_lines)

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
3. 每个场景包含地点、时间、出场人物、剧情摘要和 elements。
4. elements 的 type 只能是 dialogue、action、narration、transition。
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
    elements:
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
    if "script" not in data:
        errors.append("缺少 script 字段")

    if errors:
        return False, errors

    script = data.get("script", {}) or {}
    if not isinstance(script, dict):
        return False, ["script 必须是对象"]

    # 检查 script
    required_script_fields = ["title", "genre", "theme", "world_setting", "main_conflict", "characters", "locations", "chapters"]
    for field in required_script_fields:
        if field not in script:
            errors.append(f"script 缺少 {field} 字段")

    # 检查 chapters 至少 3 个
    chapters = script.get("chapters", [])
    if not isinstance(chapters, list):
        errors.append("script.chapters 必须是数组")
        chapters = []
    if len(chapters) < 3:
        errors.append(f"章节数不足：当前 {len(chapters)} 章，要求至少 3 章")

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
            for field in ["scene_title", "location", "time", "characters", "summary"]:
                if field not in scene:
                    errors.append(f"第 {i+1} 章第 {j+1} 场景缺少 {field}")

            if "elements" not in scene:
                errors.append(f"第 {i+1} 章第 {j+1} 场景缺少 elements")
            elif not isinstance(scene.get("elements"), list):
                errors.append(f"第 {i+1} 章第 {j+1} 场景 elements 必须是数组")

            # 检查 elements
            for k, element in enumerate(scene.get("elements", []) or []):
                if not isinstance(element, dict):
                    errors.append(f"第 {i+1} 章第 {j+1} 场景第 {k+1} 个 element 格式错误")
                    continue

                if "type" not in element:
                    errors.append(f"第 {i+1} 章第 {j+1} 场景第 {k+1} 个 element 缺少 type")
                elif element.get("type") not in ["dialogue", "action", "narration", "transition"]:
                    errors.append(f"第 {i+1} 章第 {j+1} 场景第 {k+1} 个 element type 不合法")
                if "content" not in element:
                    errors.append(f"第 {i+1} 章第 {j+1} 场景第 {k+1} 个 element 缺少 content")
                if element.get("type") == "dialogue" and "speaker" not in element:
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

    script = data.get("script", {}) or {}
    for chapter in script.get("chapters", []):
        stats["chapters"] += 1
        for scene in chapter.get("scenes", []):
            stats["scenes"] += 1
            for element in scene.get("elements", []):
                element_type = element.get("type", "")
                if element_type == "dialogue":
                    stats["dialogues"] += 1
                elif element_type == "action":
                    stats["actions"] += 1
                elif element_type == "narration":
                    stats["narrations"] += 1
                elif element_type == "transition":
                    stats["transitions"] += 1

    return stats


def normalize_chapter_schema(chapter: Dict) -> Dict:
    """兼容旧字段并补齐前端预览所需字段。"""
    chapter.setdefault("chapter_id", "chapter_001")
    chapter.setdefault("title", "未命名章节")
    chapter.setdefault("scenes", [])

    for scene_index, scene in enumerate(chapter.get("scenes", []) or []):
        if not isinstance(scene, dict):
            continue
        scene.setdefault("scene_id", f"scene_{scene_index + 1:03d}")
        scene.setdefault("scene_title", "待整理场景")
        scene.setdefault("location", "未指定")
        scene.setdefault("time", "未指定")
        scene.setdefault("characters", [])
        scene.setdefault("summary", "内容待整理")

        if "elements" not in scene and "beats" in scene:
            scene["elements"] = scene.pop("beats")
        scene.setdefault("elements", [])

    return chapter


def build_script_result(story_bible: Dict, chapters: List[Dict]) -> Dict:
    """构建最终 YAML 顶层结构。"""
    story_bible = story_bible or {}
    return {
        "schema_version": "1.0",
        "script": {
            "title": story_bible.get("title") or "未命名剧本",
            "genre": story_bible.get("genre") or "未指定",
            "theme": story_bible.get("theme") or "未指定",
            "world_setting": story_bible.get("world_setting") or "未指定",
            "main_conflict": story_bible.get("main_conflict") or "待补充",
            "characters": story_bible.get("characters") or [],
            "locations": story_bible.get("locations") or [],
            "chapters": chapters
        }
    }


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

    async def convert(self, project: Dict, selected_chapter_ids: Optional[List[str]] = None) -> Dict:
        """转换小说为剧本"""
        project["status"] = "converting"
        chapters = project["chapters"]
        story_bible = project.get("story_bible", {})

        if selected_chapter_ids:
            selected = set(selected_chapter_ids)
            chapters = [ch for ch in chapters if ch.get("chapter_id") in selected]
            if len(chapters) < 3:
                raise ValueError(f"所选章节数不足 3 章，当前选择 {len(chapters)} 章。")

        script_chapters = []
        total = len(chapters)
        conversion_errors = []
        system_prompt = "你是一个专业的影视剧本改编助手，擅长将小说改编为结构化剧本 YAML。"

        for i, chapter in enumerate(chapters):
            print(f"[Convert] 正在转换第 {i+1}/{total} 章: {chapter.get('title', '未命名')}")

            try:
                prompt = convert_chapter_prompt(story_bible, chapter)

                response = await self.llm_provider.generate(prompt, system_prompt)
                chapter_data = parse_yaml_response(response)

                if chapter_data and isinstance(chapter_data, dict):
                    script_chapters.append(normalize_chapter_schema(chapter_data))
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
                    "elements": [{
                        "type": "narration",
                        "content": "原始生成内容已丢失，请重新生成。"
                    }]
                }]
            })

        # 构建最终结果
        result = build_script_result(story_bible, script_chapters)

        # 校验
        valid, errors = validate_script_yaml(result)
        if not valid:
            print(f"[Convert] YAML 校验失败: {errors}")
            # 尝试修复
            schema_desc = "需要包含 schema_version, script 字段；script 内包含 characters 和 chapters，chapters 至少 3 个章节；场景内使用 elements 字段。"
            repair_prompt = repair_yaml_prompt(schema_desc, "\n".join(errors), yaml.dump(result))
            try:
                repair_response = await self.llm_provider.generate(repair_prompt, system_prompt)
                fixed_result = parse_yaml_response(repair_response)
                if fixed_result and isinstance(fixed_result, dict):
                    result = fixed_result
                    for chapter in result.get("script", {}).get("chapters", []) or []:
                        normalize_chapter_schema(chapter)
                    valid, errors = validate_script_yaml(result)
                    print(f"[Convert] YAML 修复{'成功' if valid else '仍失败'}")
            except Exception as e:
                print(f"[Convert] YAML 修复异常: {e}")

        # 最终兜底：确保至少 3 个章节
        result.setdefault("script", {}).setdefault("chapters", [])
        if len(result["script"].get("chapters", [])) < 3:
            print(f"[Convert] 最终兜底：确保至少 3 个章节")
            while len(result["script"].get("chapters", [])) < 3:
                result["script"]["chapters"].append({
                    "chapter_id": f"chapter_{len(result['script']['chapters']) + 1:03d}",
                    "title": f"第 {len(result['script']['chapters']) + 1} 章",
                    "scenes": [{
                        "scene_id": "scene_001",
                        "scene_title": "系统生成章节",
                        "location": "未指定",
                        "time": "未指定",
                        "characters": [],
                        "summary": "系统自动生成以满足最小章节要求",
                        "elements": [{
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

        return project


def create_fallback_chapter(chapter: Dict, story_bible: Dict) -> Dict:
    """创建兜底章节结构"""
    characters = story_bible.get("characters", [])[:3] if story_bible else []
    character_names = [
        char.get("name", str(char)) if isinstance(char, dict) else str(char)
        for char in characters
    ]
    return {
        "chapter_id": chapter.get("chapter_id", "chapter_001"),
        "title": chapter.get("title", "未命名章节"),
        "scenes": [{
            "scene_id": "scene_001",
            "scene_title": "待整理场景",
            "location": "未指定",
            "time": "未指定",
            "characters": character_names,
            "summary": "AI 返回内容格式异常，已生成基础结构。",
            "elements": [{
                "type": "narration",
                "content": chapter.get("content", "内容待整理")[:500] + "..."
            }]
        }]
    }
