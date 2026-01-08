import importlib.util
import sys
from pathlib import Path


def _load_assignment_analysis_module():
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    module_path = Path(__file__).resolve().parents[1] / "app" / "services" / "analysis.py"
    spec = importlib.util.spec_from_file_location("assignment_analysis", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


assignment_analysis = _load_assignment_analysis_module()
_parse_llm_json = assignment_analysis._parse_llm_json


def test_build_assignment_extraction_prompt_includes_schema():
    from app.services.prompts import build_assignment_extraction_prompt

    prompt = build_assignment_extraction_prompt("Sample content")
    assert '"concepts"' in prompt
    assert '"questions"' in prompt
    assert "Sample content" in prompt


def test_build_assignment_scoring_prompt_includes_payload():
    from app.services.prompts import build_assignment_scoring_prompt

    payload = {"assignment_id": 1, "questions": [], "concepts": [], "chat_logs": []}
    prompt = build_assignment_scoring_prompt(payload)
    assert '"scores"' in prompt
    assert str(payload) in prompt


def test_parse_llm_json_strips_wrapped_text():
    raw = "Here is the result:\n{\"concepts\": [], \"questions\": []}\nThanks!"
    payload = _parse_llm_json(raw)
    assert payload["concepts"] == []
    assert payload["questions"] == []
