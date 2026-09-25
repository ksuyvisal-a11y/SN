import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

transcript_path = r'C:\Users\TUF\.gemini\antigravity-ide\brain\f2f5bbfd-bd88-424a-a486-d0906bda188e\.system_generated\logs\transcript.jsonl'

with open(transcript_path, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if '"type":"USER_INPUT"' in line:
            obj = json.loads(line)
            content = obj.get('content', '')
            print(f"\n=== User Input #{i} ===")
            print(content[:600])
