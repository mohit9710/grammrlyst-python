import requests
import json
import re

OLLAMA_URL = "http://173.249.45.9:11434/api/generate"

def extract_json(text: str):
    """
    Extract JSON object from AI response that may include code blocks.
    """
    text = re.sub(r"```json|```", "", text)
    match = re.search(r"\{.*\}", text, re.S)
    return match.group() if match else None

def correct_sentence(sentence_text: str):
    """
    Correct a sentence using Ollama API.
    Returns a dict: {"original": ..., "fixed": ..., "rule": ...}
    """
    # Very clear prompt for grammar correction
    prompt = f"""
    SYSTEM ROLE: You are an expert English editor.

    TASK:
    - Correct the grammar, punctuation, capitalization, and word order of the sentence.
    - Change verb tense only if it is clearly wrong.
    - Do not add extra words unless necessary.
    - Always keep the meaning identical to the original sentence.
    - Return strictly JSON, nothing else.

    INPUT: "{sentence_text}"

    JSON FORMAT:
    {{
      "original": "{sentence_text}",
      "fixed": "corrected sentence here",
      "rule": "Explain the correction briefly or 'Correct as is'"
    }}
    """

    try:
        payload = {
            "model": "phi3",
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0, "num_predict": 300}
        }

        r = requests.post(OLLAMA_URL, json=payload, timeout=60)
        r.raise_for_status()

        raw_response = r.json().get("response", "")
        cleaned_json = extract_json(raw_response)

        if cleaned_json:
            return json.loads(cleaned_json)

    except requests.exceptions.Timeout:
        return {
            "original": sentence_text,
            "fixed": sentence_text,
            "rule": "Server Timeout: AI server did not respond"
        }
    except Exception as e:
        return {
            "original": sentence_text,
            "fixed": sentence_text,
            "rule": f"Error: {str(e)}"
        }

    return {
        "original": sentence_text,
        "fixed": sentence_text,
        "rule": "Inference Error: Could not correct"
    }