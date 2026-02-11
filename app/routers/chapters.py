from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.core.db import get_db
from app.schemas.chapters import ChapterRead, ChapterCreate, ChapterUpdate, ChapterLinkUpdate
from app.services.school import chapters as chapter_service

router = APIRouter(
    prefix="/school/chapters",
    tags=["chapters"]
)

@router.post("/", response_model=ChapterRead)
def create_chapter(chapter: ChapterCreate, db: Session = Depends(get_db)):
    db_chapter = chapter_service.create_chapter(db, chapter)
    return chapter_service.chapter_to_schema(db_chapter)

@router.get("/", response_model=List[ChapterRead])
def get_chapters(class_id: int, db: Session = Depends(get_db)):
    chapters = chapter_service.get_chapters(db, class_id)
    return [chapter_service.chapter_to_schema(c) for c in chapters]

@router.get("/{chapter_id}", response_model=ChapterRead)
def get_chapter(chapter_id: int, db: Session = Depends(get_db)):
    chapter = chapter_service.get_chapter(db, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return chapter_service.chapter_to_schema(chapter)

@router.put("/{chapter_id}", response_model=ChapterRead)
def update_chapter(chapter_id: int, chapter: ChapterUpdate, db: Session = Depends(get_db)):
    updated_chapter = chapter_service.update_chapter(db, chapter_id, chapter)
    if not updated_chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return chapter_service.chapter_to_schema(updated_chapter)

@router.delete("/{chapter_id}")
def delete_chapter(chapter_id: int, db: Session = Depends(get_db)):
    success = chapter_service.delete_chapter(db, chapter_id)
    if not success:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return {"ok": True}

@router.post("/{chapter_id}/concepts", response_model=ChapterRead)
def add_concepts(chapter_id: int, payload: ChapterLinkUpdate, db: Session = Depends(get_db)):
    chapter = chapter_service.add_concepts_to_chapter(db, chapter_id, payload.ids)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return chapter_service.chapter_to_schema(chapter)

@router.post("/{chapter_id}/assignments", response_model=ChapterRead)
def add_assignments(chapter_id: int, payload: ChapterLinkUpdate, db: Session = Depends(get_db)):
    chapter = chapter_service.add_assignments_to_chapter(db, chapter_id, payload.ids)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return chapter_service.chapter_to_schema(chapter)

@router.post("/{chapter_id}/materials", response_model=ChapterRead)
def add_materials(chapter_id: int, payload: ChapterLinkUpdate, db: Session = Depends(get_db)):
    chapter = chapter_service.add_materials_to_chapter(db, chapter_id, payload.ids)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return chapter_service.chapter_to_schema(chapter)
