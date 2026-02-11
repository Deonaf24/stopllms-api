
from app.services.prompts import build_assignment_extraction_prompt
from app.services.llm import generate_text
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

# Test content
assignment_text = """
Assignment 1: Introduction to Algebra
1. Solve for x: 2x + 5 = 15
2. Explain the concept of a variable.
"""


prompt = (
    "You are a helpful assistant. Analyze the assignment text below and extract the structure.\n"
    "Identify:\n"
    "1. Concepts (topics)\n"
    "2. Questions\n"
    "3. Relationships between them\n\n"
    "Return the result as a valid JSON object with these exact keys:\n"
    "- 'concepts': list of {id, name, description}\n"
    "- 'questions': list of {id, prompt, position}\n"
    "- 'question_concepts': list of {question_id, concept_id}\n"
    "- 'assignment_concepts': list of {concept_id}\n\n"
    "Do not include any explanation, just the JSON.\n\n"
    "Text:\n"
    f"{assignment_text}\n"
)

print(f"Prompt preview: {prompt[:100]}...")

print("\nCalling Gemini...")
try:
    response = generate_text(prompt)
    print("\n--- Response ---")
    print(response)
    print("----------------")
except Exception as e:
    print(f"Error: {e}")
