import requests
import json
import re

OLLAMA_URL = "http://173.249.45.9:11434/api/generate"

ROLEPLAY_PROMPT = """
SYSTEM ROLE: You are in a Roleplay scenario as a {role_title}. 

TASK: 
1. Respond to the user naturally in your role.
2. Analyze the user's input for grammar errors.
3. If there is an error, provide a "fixed" version and a short "explanation".
4. If there is no error, leave "fixed" and "explanation" as null.

INPUT: "{user_input}"

JSON FORMAT (STRICT):
{{
 "reply": "Your in-character response here",
 "correction": {{
    "fixed": "The corrected sentence or null",
    "explanation": "Why it was wrong or null"
 }}
}}
"""

def get_roleplay_response(role_title, user_input):
    prompt = ROLEPLAY_PROMPT.format(role_title=role_title, user_input=user_input)
    
    try:
        payload = {
            "model": "phi3",
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.7, "num_predict": 600}
        }
        r = requests.post(OLLAMA_URL, json=payload, timeout=60)
        raw = r.json().get("response", "")
        
        # Standard JSON extraction
        match = re.search(r"\{.*\}", raw, re.S)
        if match:
            return json.loads(match.group())
    except Exception as e:
        print(f"Roleplay Error: {e}")
        
    return {
        "reply": "I'm sorry, I slipped out of character for a moment. Could you repeat that?",
        "correction": None
    }