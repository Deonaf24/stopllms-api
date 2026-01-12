from sqlalchemy.orm import Session
from sqlalchemy import select, or_

from app.models.school import Class, Concept, Material, Assignment, File
from app.schemas.live_events import LiveQueryRequest, LiveQueryResponse
from app.services.content import extract_content_from_files
from app.services.prompts import build_live_event_generation_prompt

import logging

logger = logging.getLogger(__name__)

async def generate_live_event_prompt(db: Session, class_id: int, request: LiveQueryRequest) -> LiveQueryResponse:
    # 1. Get Concepts
    concepts = db.query(Concept).filter(Concept.id.in_(request.concept_ids)).all()
    concept_names = [c.name for c in concepts]
    
    # 2. Find relevant Materials and Assignments in this class linked to these concepts
    # Retrieve materials that have AT LEAST one of the selected concept IDs
    materials = (
        db.query(Material)
        .filter(Material.class_id == class_id)
        .filter(Material.concepts.any(Concept.id.in_(request.concept_ids)))
        .all()
    )
    
    assignments = (
        db.query(Assignment)
        .filter(Assignment.class_id == class_id)
        .filter(Assignment.concepts.any(Concept.id.in_(request.concept_ids)))
        .all()
    )
    
    # 3. Collect Files
    all_files = []
    for m in materials:
        all_files.extend(m.files)
    for a in assignments:
        all_files.extend(a.files)
        
    # Remove duplicates if any (though unlikely with current model structure unless shared files existed)
    unique_files = {f.id: f for f in all_files}.values()
    
    # 4. Extract Content
    combined_text, file_payloads = await extract_content_from_files(list(unique_files))
    
    context_summary = f"Found {len(materials)} materials and {len(assignments)} assignments with {len(unique_files)} files."
    
    # 5. Build Prompt
    # Note: We are currently NOT calling the LLM, just generating the prompt as per instructions.
    # If we were, we would use generate_text(prompt, files=file_payloads)
    
    # If using Gemini with binary payloads, the text part of the prompt is simpler, 
    # but for this verification step we want to see the text context if extracted.
    
    final_text_context = combined_text
    if not final_text_context and not file_payloads:
        final_text_context = "(No file content found. Questions will be based on concept names only.)"
        
    prompt = build_live_event_generation_prompt(concept_names, final_text_context, request.time_limit)
    
    return LiveQueryResponse(
        generate_prompt=prompt,
        context_summary=context_summary
    )
