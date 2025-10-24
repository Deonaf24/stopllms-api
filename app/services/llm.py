import ollama

def ollama_generate(prompt: str) -> str:
    resp = ollama.generate(model="icarus", prompt=prompt)
    return resp.get("response", "")
