from unittest.mock import MagicMock, patch
from app.services.ai.prompts import build_prompt, build_assignment_scoring_prompt
from app.services.ai.llm import generate_text
from app.schemas.prompts import PromptRequest
from app.core.config import settings

def test_build_prompt_tutor_formatting():
    req = PromptRequest(
        user_message="Explain gravity",
        subject="Physics",
        level="High School",
        assignment_id="1",
        history=""
    )
    context_blocks = ["Gravity is a force."]
    
    prompt = build_prompt(req, context_blocks, prompt_type="tutor")
    
    assert "[USER]" in prompt
    assert "Explain gravity" in prompt
    assert "[CONTEXT]" in prompt
    assert "Gravity is a force." in prompt
    assert "You are a math tutor" in prompt or "You are a" in prompt # Default might be math or dynamic

def test_build_scoring_prompt_json_structure():
    payload = {"assignment_id": 1}
    prompt = build_assignment_scoring_prompt(payload)
    assert "Return ONLY valid JSON" in prompt
    assert '"scores": [' in prompt

@patch("app.services.ai.llm.gemini_client")
def test_generate_text_gemini_mock(mock_gemini):
    # Setup Mock
    mock_response = MagicMock()
    mock_response.text = "Mocked Response"
    mock_gemini.models.generate_content.return_value = mock_response
    
    # Configure to use Gemini
    with patch("app.core.config.settings.LLM_PROVIDER", "gemini"):
        response = generate_text("Test prompt")
        
        assert response == "Mocked Response"
        mock_gemini.models.generate_content.assert_called_once()

@patch("app.services.ai.llm.ollama")
def test_generate_text_ollama_mock(mock_ollama):
    # Setup Mock
    mock_ollama.generate.return_value = {"response": "Ollama Response"}
    
    # Configure to use Ollama
    with patch("app.core.config.settings.LLM_PROVIDER", "ollama"):
        response = generate_text("Test prompt")
        
        assert response == "Ollama Response"
        mock_ollama.generate.assert_called_once()
