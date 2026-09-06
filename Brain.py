import requests
import json
from Config import GROQ_API_KEY

API_URL = "https://api.groq.com/openai/v1/chat/completions"
TIMEOUT = 10


def get_reply(user_text, memory, mood="curious"):
    system_prompt = (
        f"You are Nova, a witty, warm AI companion. "
        f"Known facts about the user: {memory}. "
        f"Your current mood is {mood}. Reply naturally, in 1-3 sentences."
    )

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "openai/gpt-oss-120b",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text}
        ],
        "temperature": 0.8
    }

    response = requests.post(API_URL, headers=headers, json=payload, timeout=TIMEOUT)
    data = response.json()

    return data["choices"][0]["message"]["content"]


def analyze_message(user_text):
    system_prompt = (
        "Analyze the user's message and reply ONLY with a single JSON object with these keys:\n"
        '"action": one of check_battery, check_wifi, open_url, open_app, list_photos, show_photo, or none\n'
        '"target": only if action is open_url or open_app, else empty string\n'
        '"mood": one of happy, curious, annoyed, neutral (emotional tone toward the assistant)\n'
        '"facts": an object of any personal facts the user stated about themselves (name, likes, job, etc). '
        "Only include a 'name' if they clearly state it (e.g. 'my name is X', 'I'm X'). "
        "A single word or the assistant's own name is NOT a fact. Use {} if none.\n\n"
        "Example:\n"
        '{"action": "none", "target": "", "mood": "happy", "facts": {}}\n'
        '{"action": "open_app", "target": "whatsapp", "mood": "neutral", "facts": {}}\n'
        '{"action": "none", "target": "", "mood": "neutral", "facts": {"name": "Ivan"}}\n'
        "'show me a photo' -> {\"action\": \"show_photo\", \"target\": \"\", \"mood\": \"neutral\", \"facts\": {}}\n\n"
        "Reply ONLY with the JSON object, nothing else."
    )

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "openai/gpt-oss-120b",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text}
        ],
        "temperature": 0
    }

    response = requests.post(API_URL, headers=headers, json=payload, timeout=TIMEOUT)
    data = response.json()

    try:
        content = data["choices"][0]["message"]["content"]
        result = json.loads(content)
        result.setdefault("action", "none")
        result.setdefault("target", "")
        result.setdefault("mood", "neutral")
        result.setdefault("facts", {})
        return result
    except Exception:
        return {"action": "none", "target": "", "mood": "neutral", "facts": {}}


if __name__ == "__main__":
    from Memory import load_memory
    memory = load_memory()
    reply = get_reply("Hey Nova, remember me?", memory)
    print(reply)
