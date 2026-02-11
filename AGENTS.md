# Icarus-API Architecture & Guidelines

This document outlines the architectural principles and coding standards for the `Icarus-API` backend. Future agents and developers should follow these guidelines to maintain code quality and prevent technical debt.

## 1. Architecture Overview
The application follows a **Service-Controller (Router)** pattern using **FastAPI** and **SQLAlchemy**.

### Structure
- `app/routers/`: **Controllers**. Handle HTTP requests, validation, and response formatting. **NO BUSINESS LOGIC ALLOWED.**
- `app/services/`: **Business Logic**. Pure Python functions. Handle complex operations, DB queries, and external API calls.
- `app/models/`: **Database Entities**. SQLAlchemy ORM definitions.
- `app/schemas/`: **Data Transfer Objects**. Pydantic models for request/response validation.
- `app/core/`: **Infrastructure**. Config, DB connection, Security.

## 2. Core Principles

### ❌ Anti-Pattern: Logic Leaks in Routers
**Do NOT** put business logic or detailed aggregations in `app/routers/`.
*   **Bad**: Iterating over assignments to aggregate concepts inside a route handler.
*   **Good**: Call `classes_service.get_class_concepts(class_obj)`.

### ❌ Anti-Pattern: God Modules
**Do NOT** allow single files to grow indefinitely (e.g., `analysis.py` handling PDF extraction, LLM parsing, _and_ scoring).
*   **Split by Responsibility**:
    *   `services/extraction.py`: File processing.
    *   `services/scoring.py`: Domain logic.
    *   `services/llm_utils.py`: Utilities.

### ❌ Anti-Pattern: Hardcoded Configuration
**Do NOT** hardcode:
*   File paths (e.g., use `pathlib` relative properties or config).
*   CORS Origins (use `.env` / `settings`).
*   Secrets (use `.env` - `config.py` should fail if sensitive env vars are missing).

## 3. LLM & AI Integration

### Robust JSON Parsing
**Do NOT** use Regex to parse JSON from LLMs. It is fragile and breaks easily.
*   **Use**: `LangChain`'s `JsonOutputParser` (or `instructor`).
*   **Reference**: `app/services/llm_utils.py`.

### Prompt Engineering
*   Keep prompts in `app/services/prompts.py` or dedicated prompt files.
*   Do not hardcode massive prompt strings inside logic functions.

## 4. Database & Async
*   We are transitioning to `AsyncSession`. Prefer `await db.execute(select(Model))` over `db.query(Model)`.
*   Ensure all DB sessions are properly closed (handled by dependency injection).

## 5. Directory Structure
*   Group related domain logic.
*   Example: RAG logic belongs in `app/services/rag/`, not at the root `app/RAG`.

## 6. Development Workflow
1.  **Check `task.md`** for active objectives.
2.  **Verify** changes with local scripts or tests before notifying.
3.  **Refactor** proactively if you see the anti-patterns listed above.
