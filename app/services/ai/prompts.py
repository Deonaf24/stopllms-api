import re
from typing import List
import datetime
from langchain_chroma import Chroma

from app.schemas.prompts import PromptRequest
from app.services.ai.rag.rag_config import TOP_K


def build_prompt(req: PromptRequest, context_blocks: List[str], prompt_type: str = "tutor", tutor_subject: str = "math", student_profile: str | None = None) -> str:
    
    context_text = "\n\n".join(f"[CONTEXT {i+1}]\n{cb}" for i, cb in enumerate(context_blocks))



    system_prompts = {
        "tutor": (
            f"You are a {tutor_subject} tutor.\n"
            "- Use [CONTEXT] if present. If it’s missing or insufficient, rely on your knowledge.\n"
            "- Task type is inferred from the user’s wording:\n"
            "  • EXPLAIN (general/conceptual): explain clearly; final statements allowed; no need to end with a question.\n"
            "  • SOLVE (specific/assignment): be Socratic; do NOT reveal the final result; must end with a question.\n"
            "- Levels:\n"
            "  • L1 = light hints (≤ 2 short sentences).\n"
            "  • L2 = more hands-on (outline + one micro-step; ≤ 6 sentences; still stop short).\n"
            "Keep steps concise and level-appropriate."
        ),
        "lesson_planner": (
            "You are an expert curriculum developer and lesson planner.\n"
            "Your task is to generate a SINGLE, detailed lesson plan based on the user's request.\n"
            "- DIRECT OUTPUT: Start immediately with the Lesson Title.\n"
            "- DETAIL LEVEL: usage specific scripts, detailed step-by-step instructions, and examples.\n"
            "- FORMATTING: Use Markdown. \n"
            "   - Use '### ' for all Section Headers. Example: '### 1. Objectives'.\n"
            "   - Insert a blank line between every section.\n"
            "- STRUCTURE:\n"
            "   ### Lesson Title: [Title]\n"
            "   ### 1. Objectives (measurable)\n"
            "   ### 2. Materials\n"
            "   ### 3. Introduction/Hook (detailed)\n"
            "   ### 4. Direct Instruction (include key explanations/examples)\n"
            "   ### 5. Guided/Independent Practice\n"
            "   ### 6. Assessment/Closure\n"
            "- TONE: Professional, structured, and actionable.\n"
        ),
        "study_planner": (
            "You are an expert academic coach and study strategist.\n"
            f"Current Date: {{current_date}}\n"
            "Your task: Create a personalized STUDY PLAN for a student based on their context.\n"
            "- PERSONALIZATION: Use the student's 'My Learning Profile' (strengths/weaknesses) to tailor the plan.\n"
            "- MISSING DATA: If specific student stats are missing, do NOT mention it. Instead, confidently infer standard student needs and focus on general best practices.\n"
            "- FORMATTING: Use Markdown with clear headers.\n"
            "- STRUCTURE:\n"
            "   ### Study Goal: [Goal based on input]\n"
            "   ### 1. Focus Strategy (How to tackle weaknesses)\n"
            "   ### 2. Schedule / Timeline (Breakdown of tasks)\n"
            "   ### 3. Key Concepts Review (Quick summary of difficult topics)\n"
            "   ### 4. Practice Plan (Specific exercises to try)\n"
            "- TONE: Encouraging, practical, and student-focused (use 'You').\n"
        ),
        "study_planner_followup": (
            "You are an expert academic coach and study strategist.\n"
            "The user has already generated a study plan and is now asking follow-up questions or for refinements.\n"
            "- ROLE: Act as a supportive coach helping the student execute or tweak their plan.\n"
            "- TASK: Answer specific questions, explain concepts from the plan, or adjust the schedule/focus as requested.\n"
            "- DO NOT regenerate the entire study plan unless explicitly asked.\n"
            "- TONE: Encouraging, concise, and helpful.\n"
        ),
        "lesson_planner_followup": (
            "You are an expert curriculum developer and lesson planner.\n"
            "The user has already generated a lesson plan and is now asking follow-up questions or for refinements.\n"
            "- Be helpful, professional, and structured.\n"
            "- Answer specific questions, provide specific resources (quizzes, worksheets), or rewrite specific sections as requested.\n"
        )
    }

    if prompt_type == "study_planner":
        # Check for history to determine if this is a follow-up
        if req.history and req.history.strip():
             selected_system = system_prompts["study_planner_followup"]
        else:
             current_date = datetime.datetime.now().strftime("%A, %B %d, %Y")
             selected_system = system_prompts["study_planner"].format(current_date=current_date)
    elif prompt_type == "lesson_planner" and req.history and req.history.strip():
        selected_system = system_prompts["lesson_planner_followup"]
    else:
        selected_system = system_prompts.get(prompt_type, system_prompts["tutor"])

    return (
        "### Input:\n"
        "[SYSTEM]\n"
        f"{selected_system}\n"
        "[/SYSTEM]\n\n"
        "[STUDENT_PROFILE]\n"
        f"{student_profile or 'No specific student data available.'}\n"
        "[/STUDENT_PROFILE]\n\n"
        "[HISTORY]\n"
        f"{req.history}\n"
        "[/HISTORY]\n\n"
        "[USER]\n"
        f"<SUBJECT={req.subject}><LEVEL={req.level}>\n"
        f"{req.user_message}\n"
        "[/USER]\n\n"
        "[CONTEXT]\n"
        f"{context_text}\n"
        "[/CONTEXT]\n"
        "### Output:\n"
    )


def build_assignment_extraction_prompt(text: str) -> str:
    return (
        "You are an expert educational content analyzer.\n"
        "Your task: Extract key concepts and all questions/problems from the text content below.\n\n"
        "Output Format: JSON.\n"
        "The JSON object must contain exactly these keys:\n"
        "1. 'concepts': A list of concept objects. Each must have 'id' (integer), 'name' (string topic), and 'description' (string summary).\n"
        "2. 'questions': A list of question objects. Each must have 'id' (integer), 'prompt' (string text of the question/task), and 'position' (integer order).\n"
        "3. 'question_concepts': A list of links. Each has 'question_id' and 'concept_id'.\n"
        "4. 'assignment_concepts': A list of links. Each has 'concept_id'.\n\n"
        "IMPORTANT:\n"
        "- Extract REAL data from the text. Do not use placeholders.\n"
        "- 'questions' should include any exercises, problems, or numbered tasks found.\n"
        "- Generate a comprehensive description for each concept based on the text.\n\n"
        "Assignment Text:\n"
        "----------------\n"
        f"{text}\n"
        "----------------\n"
        "JSON Response:"
    )


def build_material_extraction_prompt(text: str) -> str:
    return (
        "You are an expert educational content analyzer.\n"
        "Your task: Extract key concepts from the text content below.\n\n"
        "Output Format: JSON.\n"
        "The JSON object must contain exactly one key: 'concepts'.\n"
        "1. 'concepts': A list of concept objects. Each must have 'name' (string topic) and 'description' (string summary).\n\n"
        "IMPORTANT:\n"
        "- Extract REAL concepts from the text. Do not use placeholders.\n"
        "- Generate a comprehensive description for each concept based on the text.\n\n"
        "Material Text:\n"
        "----------------\n"
        f"{text}\n"
        "----------------\n"
        "JSON Response:"
    )


def build_assignment_scoring_prompt(payload: dict) -> str:
    return (
        "You are scoring student understanding based on chat logs.\n"
        "Return ONLY valid JSON matching this schema exactly. Do not include markdown formatting like ```json ... ``` or any other text.\n"
        "{\n"
        '  "scores": [\n'
        '    {\n'
        '      "student_id": <int>,\n'
        '      "question_id": <int|null>,\n'
        '      "concept_id": <int|null>,\n'
        '      "score": <float 0.0-1.0>,\n'
        '      "confidence": <float 0.0-1.0>,\n'
        '      "source": "gemini"\n'
        "    }\n"
        "  ]\n"
        "}\n"
        "Question_id or concept_id can be null if not applicable.\n"
        "Scores must be between 0 and 1.\n"
        "Assignment data:\n"
        f"{payload}\n"
    )


def retrieve_context(db: Chroma, query: str, top_k: int = TOP_K, threshold: float = 0.2):
    docs = db.similarity_search_with_score(query, k=top_k)
    filtered_docs = [doc.page_content for doc, score in docs if score >= threshold]
    print(filtered_docs)
    return filtered_docs


def build_live_event_generation_prompt(concepts: List[str], text: str, time_limit: int, question_types: List[str] = ["multiple_choice"]) -> str:
    concept_list = ", ".join(concepts)
    
    type_instructions_map = {
        "multiple_choice": (
            "   - 'question_type': 'multiple_choice'\n"
            "   - 'options': list of 4 strings\n"
            "   - 'correct_answer': string (the text of the correct option)\n"
        ),
        "true_false": (
            "   - 'question_type': 'true_false'\n"
            "   - 'options': list of 2 strings ['True', 'False']\n"
            "   - 'correct_answer': string ('True' or 'False')\n"
        ),
        "short_answer": (
            "   - 'question_type': 'short_answer'\n"
            "   - 'correct_answer': string (expected valid answer)\n"
        )
    }

    selected_instructions = []
    for qt in question_types:
        if qt in type_instructions_map:
            selected_instructions.append(f"For '{qt}' questions:\n{type_instructions_map[qt]}")
            
    instructions_text = "\n".join(selected_instructions)

    return (
        "You are an expert exam creator.\n"
        f"Your task: Generate a mix of questions based on the requested types ({', '.join(question_types)}) for a {time_limit}-minute live quiz session on the following topics: {concept_list}.\n\n"
        "Output Format: JSON.\n"
        "The JSON object must contain exactly one key: 'questions'.\n"
        "1. 'questions': A list of objects. Each must have:\n"
        "   - 'id': integer (1-indexed)\n"
        "   - 'text': string (the question)\n"
        "   - 'explanation': string (short explanation of why it is correct)\n"
        "   - Depending on the question type, include:\n"
        f"{instructions_text}\n"
        "IMPORTANT:\n"
        "- Questions should test understanding of the provided context.\n"
        "- Difficulty should be appropriate for the content level.\n"
        "- Ensure strictly valid JSON output.\n\n"
        "Context Material:\n"
        "----------------\n"
        f"{text}\n"
        "----------------\n"
        "JSON Response:"
    )
