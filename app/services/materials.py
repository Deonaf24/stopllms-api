from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.school import Material, File, Concept
from app.schemas.school import MaterialCreate, MaterialRead, FileCreate
from app.services.llm import generate_text
from app.services.prompts import build_material_extraction_prompt
from app.core.config import settings

import logging
import json
import re

logger = logging.getLogger(__name__)


def create_material(db: Session, material: MaterialCreate) -> Material:
    db_material = Material(
        title=material.title,
        description=material.description,
        class_id=material.class_id,
        teacher_id=material.teacher_id,
    )
    
    if material.concept_ids:
        concepts = db.query(Concept).filter(Concept.id.in_(material.concept_ids)).all()
        db_material.concepts = concepts

    db.add(db_material)
    db.commit()
    db.refresh(db_material)
    return db_material


def list_materials(db: Session, class_id: int) -> List[Material]:
    return db.query(Material).filter(Material.class_id == class_id).all()


def get_material(db: Session, material_id: int) -> Optional[Material]:
    return db.query(Material).filter(Material.id == material_id).first()


def material_to_schema(material: Material) -> MaterialRead:
    return MaterialRead(
        id=material.id,
        title=material.title,
        description=material.description,
        class_id=material.class_id,
        teacher_id=material.teacher_id,
        created_at=material.created_at,
        updated_at=material.updated_at,
        file_ids=[file.id for file in material.files],
        concept_ids=[concept.id for concept in material.concepts],
    )


def create_material_file(db: Session, file: FileCreate) -> File:
    db_file = File(
        filename=file.filename,
        path=file.storage_path,
        url=file.storage_url,
        material_id=file.material_id,
        mime_type=file.mime_type,
        size=file.size,
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file


def _parse_llm_json(raw: str) -> dict:
    if "```" in raw:
        match = re.search(r"```(?:json)?(.*?)```", raw, re.DOTALL)
        if match:
            raw = match.group(1).strip()
    raw = re.sub(r'\\(?![/u"bfnrt\\])', r'\\\\', raw)
    try:
        return json.loads(raw)
    except Exception:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                pass
    return {}


async def analyze_material_content(db: Session, material: Material) -> List[Concept]:
    from app.services.content import extract_content_from_files

    if not material.files:
        return []

    combined_text, file_payloads = await extract_content_from_files(material.files)

    if not combined_text.strip() and not file_payloads:
        return []

    prompt_text = combined_text
    files_to_send = None
    if settings.LLM_PROVIDER == "gemini" and file_payloads:
        prompt_text = "Refer to the attached documents for the material content."
        files_to_send = file_payloads

    prompt = build_material_extraction_prompt(prompt_text)
    
    try:
        raw = generate_text(prompt, files=files_to_send)
        payload = _parse_llm_json(raw)
    except Exception as e:
        logger.error(f"LLM analysis failed for material {material.id}: {e}")
        return []

    concepts_data = payload.get("concepts", [])
    linked_concepts = []
    
    for c_data in concepts_data:
        name = c_data.get("name")
        if not name:
            continue
            
        # Check if concept exists
        concept = db.query(Concept).filter(Concept.name == name).first()
        if not concept:
            # Create new concept
            concept = Concept(name=name, description=c_data.get("description"))
            db.add(concept)
            db.commit()
            db.refresh(concept)
        
        linked_concepts.append(concept)

    # Update material concepts
    # Merge with existing concepts
    existing_ids = {c.id for c in material.concepts}
    for c in linked_concepts:
        if c.id not in existing_ids:
            material.concepts.append(c)
            existing_ids.add(c.id)
            
    db.commit()
    db.refresh(material)
    
    return material.concepts
