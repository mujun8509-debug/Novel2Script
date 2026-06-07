"""
FastAPI 路由定义
"""
import os
import json
import yaml
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from datetime import datetime

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

from models import (
    ProjectCreate, ProjectResponse, AnalyzeResponse,
    ConvertResponse, ValidateResponse, ConvertRequest
)
from services.novel_service import NovelService
from services.llm_provider import create_llm_provider

router = APIRouter(prefix="/api")

# 简单的内存存储（生产环境应使用数据库）
projects = {}

# 创建 LLM Provider 和 Novel Service
logger.info("正在创建 LLM Provider...")
llm_provider = create_llm_provider()
logger.info("LLM Provider 创建成功")
novel_service = NovelService(llm_provider)
logger.info("NovelService 创建成功")


@router.post("/projects", response_model=dict)
async def create_project(data: ProjectCreate):
    """创建新项目"""
    project = await novel_service.create_project(data.name, data.novel_text)
    projects[project["project_id"]] = project
    return {
        "project_id": project["project_id"],
        "status": project["status"]
    }


@router.get("/projects/{project_id}", response_model=dict)
async def get_project(project_id: str):
    """获取项目信息"""
    if project_id not in projects:
        raise HTTPException(status_code=404, detail="项目不存在")

    project = projects[project_id]
    return {
        "project_id": project["project_id"],
        "name": project["name"],
        "status": project["status"],
        "created_at": project["created_at"],
        "chapters_count": len(project.get("chapters", [])),
        "has_story_bible": project.get("story_bible") is not None,
        "has_result": project.get("result") is not None
    }


@router.get("/projects/{project_id}/analysis", response_model=dict)
async def get_analysis(project_id: str):
    """获取项目分析结果（章节列表和story_bible）"""
    if project_id not in projects:
        raise HTTPException(status_code=404, detail="项目不存在")
    project = projects[project_id]
    return {
        "chapters": project.get("chapters", []),
        "story_bible": project.get("story_bible"),
        "chapters_count": len(project.get("chapters", []))
    }


@router.post("/projects/{project_id}/analyze", response_model=dict)
async def analyze_project(project_id: str):
    """分析小说：识别章节，提取全局信息"""
    logger.info(f"开始分析项目: {project_id}")
    
    if project_id not in projects:
        logger.error(f"项目不存在: {project_id}")
        raise HTTPException(status_code=404, detail="项目不存在")

    project = projects[project_id]

    try:
        logger.info(f"调用 novel_service.analyze")
        project = await novel_service.analyze(project)
        projects[project_id] = project
        logger.info(f"分析完成，章节数: {len(project.get('chapters', []))}")
        return {
            "status": "analyzed",
            "chapters_count": len(project.get("chapters", [])),
            "chapters": project.get("chapters", []),
            "story_bible": project.get("story_bible")
        }
    except ValueError as e:
        logger.error(f"验证错误: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"分析失败: {e}", exc_info=True)
        project["status"] = "error"
        projects[project_id] = project
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@router.post("/projects/{project_id}/convert", response_model=dict)
async def convert_project(project_id: str, data: Optional[ConvertRequest] = None):
    """转换小说为剧本"""
    if project_id not in projects:
        raise HTTPException(status_code=404, detail="项目不存在")

    project = projects[project_id]

    if project["status"] != "analyzed":
        raise HTTPException(status_code=400, detail="请先完成分析步骤")

    try:
        selected_chapter_ids = data.chapter_ids if data and data.chapter_ids else None
        project = await novel_service.convert(project, selected_chapter_ids)
        projects[project_id] = project
        return {
            "status": "completed",
            "message": "剧本生成完成"
        }
    except ValueError as e:
        project["status"] = "analyzed"
        projects[project_id] = project
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        project["status"] = "error"
        projects[project_id] = project
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/result")
async def get_result(project_id: str):
    """获取生成结果"""
    if project_id not in projects:
        raise HTTPException(status_code=404, detail="项目不存在")

    project = projects[project_id]
    if not project.get("result"):
        raise HTTPException(status_code=400, detail="结果尚未生成")

    return project["result"]


@router.post("/projects/{project_id}/validate", response_model=dict)
async def validate_result(project_id: str):
    """校验 YAML Schema"""
    if project_id not in projects:
        raise HTTPException(status_code=404, detail="项目不存在")

    project = projects[project_id]
    if not project.get("result"):
        raise HTTPException(status_code=400, detail="结果尚未生成")

    from services.novel_service import validate_script_yaml, collect_stats
    valid, errors = validate_script_yaml(project["result"])
    stats = collect_stats(project["result"])

    return {
        "valid": valid,
        "errors": errors,
        "stats": stats
    }


@router.get("/projects/{project_id}/export")
async def export_result(project_id: str, format: str = "yaml"):
    """导出结果"""
    if project_id not in projects:
        raise HTTPException(status_code=404, detail="项目不存在")

    project = projects[project_id]
    if not project.get("result"):
        raise HTTPException(status_code=400, detail="结果尚未生成")

    result = project["result"]

    if format == "yaml":
        content = yaml.dump(result, allow_unicode=True, sort_keys=False, default_flow_style=False)
        filename = f"{project['name']}_script.yaml"
        return StreamingResponse(
            iter([content]),
            media_type="application/x-yaml",
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"}
        )
    elif format == "md":
        # 生成 Markdown 格式
        md_content = generate_markdown(result, project["name"])
        filename = f"{project['name']}_script.md"
        return StreamingResponse(
            iter([md_content]),
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"}
        )
    else:
        raise HTTPException(status_code=400, detail="不支持的格式")


def generate_markdown(result: dict, title: str) -> str:
    """生成 Markdown 格式的剧本"""
    lines = []
    lines.append(f"# {title}\n")

    script = result.get("script", {})
    lines.append(f"**类型**: {script.get('genre', 'N/A')}")
    lines.append(f"**主题**: {script.get('theme', 'N/A')}")
    lines.append(f"**世界观**: {script.get('world_setting', 'N/A')}")
    lines.append(f"**核心冲突**: {script.get('main_conflict', 'N/A')}\n")

    lines.append("## 人物\n")
    for char in script.get("characters", []):
        lines.append(f"- **{char.get('name', 'N/A')}** ({char.get('role', 'N/A')})")
        if char.get('personality'):
            lines.append(f"  - 性格: {char['personality']}")
        if char.get('goal'):
            lines.append(f"  - 目标: {char['goal']}")

    lines.append("\n## 地点\n")
    for loc in script.get("locations", []):
        lines.append(f"- **{loc.get('name', 'N/A')}**: {loc.get('description', 'N/A')}")

    for chapter in script.get("chapters", []):
        lines.append(f"\n---\n\n## {chapter.get('title', 'N/A')}\n")
        for scene in chapter.get("scenes", []):
            lines.append(f"### {scene.get('scene_title', 'N/A')}\n")
            lines.append(f"**地点**: {scene.get('location', 'N/A')} | **时间**: {scene.get('time', 'N/A')}\n")
            lines.append(f"**人物**: {', '.join(scene.get('characters', []))}\n")
            lines.append(f"**摘要**: {scene.get('summary', 'N/A')}\n")

            for element in scene.get("elements", []):
                element_type = element.get("type", "")
                content = element.get("content", "")
                speaker = element.get("speaker", "")

                if element_type == "dialogue":
                    lines.append(f"**{speaker}**: {content}\n")
                elif element_type == "action":
                    lines.append(f"【动作】{content}\n")
                elif element_type == "narration":
                    lines.append(f"【旁白】{content}\n")
                elif element_type == "transition":
                    lines.append(f"【转场】{content}\n")

    return "\n".join(lines)
