import httpx
import json

key = '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'
headers = {'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'}

candidates = ['openai/gpt-oss-120b', 'qwen/qwen3.8-27b']

for model in candidates:
    payload = {
        'model': model,
        'messages': [
            {'role': 'system', 'content': 'You are a professional film/drama Khmer dubbing translator. Return only a JSON object with key dialogues.'},
            {'role': 'user', 'content': 'Translate these dialogues to Khmer:\n[{"id": 1, "text_original": "总裁，少爷和夫人已经回到别墅了。", "voice": "piseth"}]\nReturn JSON with {"dialogues": [{"id": 1, "text_km": "...", "voice": "piseth"}]}'}
        ],
        'response_format': {'type': 'json_object'},
        'temperature': 0.3
    }
    r = httpx.post('https://api.groq.com/openai/v1/chat/completions', headers=headers, json=payload, timeout=12)
    with open(f"scratch/output_{model.replace('/', '_')}.json", "w", encoding="utf-8") as f:
        f.write(r.text)
    print(f"Saved {model} output. Status: {r.status_code}")
