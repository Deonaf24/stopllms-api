from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.school import Chapter, Class, Concept, Assignment, Material
from app.schemas.chapters import ChapterCreate, ChapterUpdate, ChapterRead

def chapter_to_schema(chapter: Chapter) -> ChapterRead:
    return ChapterRead(
        id=chapter.id,
        title=chapter.title,
        description=chapter.description,
        class_id=chapter.class_id,
        order=chapter.order,
        created_at=chapter.created_at,
        updated_at=chapter.updated_at,
        concept_ids=[c.id for c in chapter.concepts],
        assignment_ids=[a.id for a in chapter.assignments],
        material_ids=[m.id for m in chapter.materials],
    )

def create_chapter(db: Session, chapter_in: ChapterCreate) -> Chapter:
    db_chapter = Chapter(
        title=chapter_in.title,
        description=chapter_in.description,
        class_id=chapter_in.class_id,
        order=chapter_in.order
    )
    db.add(db_chapter)
    db.commit()
    db.refresh(db_chapter)
    return db_chapter

def get_chapters(db: Session, class_id: int) -> list[Chapter]:
    stmt = select(Chapter).where(Chapter.class_id == class_id).order_by(Chapter.order)
    return db.scalars(stmt).all()

def get_chapter(db: Session, chapter_id: int) -> Chapter | None:
    return db.get(Chapter, chapter_id)

def update_chapter(db: Session, chapter_id: int, chapter_in: ChapterUpdate) -> Chapter | None:
    db_chapter = get_chapter(db, chapter_id)
    if not db_chapter:
        return None
    
    update_data = chapter_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_chapter, field, value)
    
    db.add(db_chapter)
    db.commit()
    db.refresh(db_chapter)
    return db_chapter

def delete_chapter(db: Session, chapter_id: int) -> bool:
    db_chapter = get_chapter(db, chapter_id)
    if not db_chapter:
        return False
    
    db.delete(db_chapter)
    db.commit()
    return True

def add_concepts_to_chapter(db: Session, chapter_id: int, concept_ids: list[int]) -> Chapter | None:
    db_chapter = get_chapter(db, chapter_id)
    if not db_chapter:
        return None
    
    concepts = db.scalars(select(Concept).where(Concept.id.in_(concept_ids))).all()
    for concept in concepts:
        if concept not in db_chapter.concepts:
            db_chapter.concepts.append(concept)
            
    db.commit()
    db.refresh(db_chapter)
    return db_chapter

def add_assignments_to_chapter(db: Session, chapter_id: int, assignment_ids: list[int]) -> Chapter | None:
    db_chapter = get_chapter(db, chapter_id)
    if not db_chapter:
        return None
    
    assignments = db.scalars(select(Assignment).where(Assignment.id.in_(assignment_ids))).all()
    for assignment in assignments:
        if assignment not in db_chapter.assignments:
            db_chapter.assignments.append(assignment)
            
    db.commit()
    db.refresh(db_chapter)
    return db_chapter

def add_materials_to_chapter(db: Session, chapter_id: int, material_ids: list[int]) -> Chapter | None:
    db_chapter = get_chapter(db, chapter_id)
    if not db_chapter:
        return None
    
    materials = db.scalars(select(Material).where(Material.id.in_(material_ids))).all()
    for material in materials:
        if material not in db_chapter.materials:
            db_chapter.materials.append(material)
            
    db.commit()
    db.refresh(db_chapter)
    return db_chapter
