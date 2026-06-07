from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


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


class ScriptElement(BaseModel):
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
    elements: List[ScriptElement]


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


class Script(BaseModel):
    title: str
    genre: str
    theme: str
    world_setting: str
    main_conflict: str
    characters: List[Character]
    locations: List[Location]
    chapters: List[Chapter]


class ScriptYaml(BaseModel):
    schema_version: str = "1.0"
    script: Script


class ChapterInfo(BaseModel):
    chapter_id: str
    title: str
    content: str
    word_count: int


class ProjectCreate(BaseModel):
    name: str
    novel_text: str


class ConvertRequest(BaseModel):
    chapter_ids: Optional[List[str]] = None


class ProjectResponse(BaseModel):
    project_id: str
    name: str
    status: str
    created_at: str
    chapters: Optional[List[ChapterInfo]] = None
    story_bible: Optional[StoryBible] = None
    result: Optional[ScriptYaml] = None
    validation_result: Optional[dict] = None


class AnalyzeResponse(BaseModel):
    status: str
    chapters_count: int
    story_bible: Optional[StoryBible] = None


class ConvertResponse(BaseModel):
    status: str
    progress: float
    current_step: str


class ValidateResponse(BaseModel):
    valid: bool
    errors: List[str]
    stats: dict
