# -*- coding: utf-8 -*-
import sys
import os
from pathlib import Path

# Ensure root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Ensure utf-8 output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import requests
import json
from nisay_translate import get_nisay_api_key

def main():
    key = get_nisay_api_key()
    if not key or key == "nisay-YOUR_API_KEY":
        print("[ERROR] Nisay API Key not configured!")
        return

    url = "https://api.nisay.store/api/public/usage"
    payload = {
        "key": key,
        "page": 1,
        "pageSize": 20,
        "includeRequestDetails": False
    }

    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code == 200:
            d = r.json()
            quota_tok = d.get("quotaTokens", 100000000)
            used_tok = d.get("usedTokens", 0)
            rem_tok = d.get("remainingTokens", 0)
            pct = d.get("percentUsed", 0)
            rem_bal = d.get("remainingBalance", 0.0)
            today_tok = d.get("usagePeriods", {}).get("today", {}).get("total_tokens", 0)
            today_req = d.get("usagePeriods", {}).get("today", {}).get("requests", 0)
            exp = d.get("expiresAt", "")[:10]

            print("=" * 65)
            print(" 💎 NISAY AI GATEWAY - ACCOUNT & TOKEN USAGE")
            print("=" * 65)
            print(f" 👤 Account Name:     {d.get('name', 'Nisay User')}")
            print(f" 🟢 Key Status:       {d.get('status', 'active').upper()}")
            print(f" 📅 Expires On:       {exp}")
            print("-" * 65)
            print(f" 💎 Total Capacity:   {quota_tok:,} Tokens (100M)")
            print(f" 📉 Consumed Tokens:  {used_tok:,} Tokens ({pct}%)")
            print(f" 🔥 REMAINING TOKENS: {rem_tok:,} Tokens ({100 - pct}%)")
            print(f" 💵 Remaining Balance: ${rem_bal:.2f}")
            print("-" * 65)
            print(f" 📊 Today Usage:      {today_tok:,} Tokens ({today_req} requests)")
            print("=" * 65)
            print(f"\n👉 Direct Web Dashboard: https://api.nisay.store/checkusage?key={key}\n")
        else:
            print(f"[ERROR] API responded with code {r.status_code}: {r.text}")
    except Exception as e:
        print(f"[ERROR] Could not connect to Nisay Gateway: {e}")

if __name__ == "__main__":
    main()
