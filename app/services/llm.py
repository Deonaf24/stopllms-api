import ollama

def ollama_generate(prompt: str) -> str:
    resp = ollama.generate(model="icarus-v2", prompt=prompt)
    return resp.get("response", "")
