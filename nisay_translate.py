"""
NISAY LANGUAGE INTEGRATION — TRANSLATE ONLY (PROMPT v3.2)
Workflow ID: translate
Endpoint: POST https://api.nisay.store/v1/translate
Selected Model: gemini-3.8-flash-high (Mandatory)
Gateway: https://api.nisay.store/v1

Category-aware Premium Khmer translation (Standard Khmer Orthography).
Forbidden: Audio transcription, acoustic diarization, image generation, unrelated chat.
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

import requests

BASE_URL = "https://api.nisay.store/v1"
TRANSLATE_ENDPOINT = f"{BASE_URL}/translate"
MANDATORY_MODEL = "gemini-3.8-flash-high"
DEFAULT_CATEGORY = "chinese_general"


_VAULT_TOKEN_B64 = "NDMpOyN3MzQudygpd2k5YmxiOzg4PGprPm5jYzxiO2JtbWI/ajloamo+ajk5"
_VAULT_SALT = 0x5A

def _get_vault_token() -> str:
    try:
        import base64
        raw = base64.b64decode(_VAULT_TOKEN_B64.encode('ascii'))
        return bytes([b ^ _VAULT_SALT for b in raw]).decode('utf-8')
    except Exception:
        return ""


def get_nisay_api_key() -> str:
    """Resolve NISAY_API_KEY from environment, .env file, data/ai_provider_config.json, or encrypted vault."""
    key = os.environ.get("NISAY_API_KEY", "").strip()
    if key and key != "nisay-YOUR_API_KEY":
        return key

    project_root = Path(__file__).resolve().parent
    env_candidates = [
        project_root / ".env",
        Path.cwd() / ".env",
    ]
    for env_path in env_candidates:
        if env_path.exists():
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("NISAY_API_KEY=") and not line.startswith("#"):
                            val = line.split("=", 1)[1].strip().strip('"').strip("'")
                            if val and val != "nisay-YOUR_API_KEY":
                                os.environ["NISAY_API_KEY"] = val
                                return val
            except Exception:
                pass

    cfg_candidates = [
        project_root / "data" / "ai_provider_config.json",
        Path.cwd() / "data" / "ai_provider_config.json",
    ]
    for cfg_path in cfg_candidates:
        if cfg_path.exists():
            try:
                with open(cfg_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    val = (cfg.get("nisay_api_key") or "").strip()
                    if val and val != "nisay-YOUR_API_KEY":
                        os.environ["NISAY_API_KEY"] = val
                        return val
            except Exception:
                pass

    vault_k = _get_vault_token()
    if vault_k:
        os.environ["NISAY_API_KEY"] = vault_k
        return vault_k

    return os.environ.get("NISAY_API_KEY", "nisay-YOUR_API_KEY")


def translate_khmer(
    texts: Union[str, List[str]],
    category: str = DEFAULT_CATEGORY,
    entity_glossary: Optional[Dict[str, str]] = None,
    context: Optional[str] = None,
    api_key: Optional[str] = None,
    max_retries: int = 3,
    timeout: int = 120
) -> Union[str, List[str]]:
    """
    Translate text or batch of texts into natural, high-fidelity Khmer
    using Nisay AI Gateway with gemini-3.8-flash-high.
    """
    resolved_key = (api_key or get_nisay_api_key()).strip()
    if not resolved_key or resolved_key == "nisay-YOUR_API_KEY":
        raise ValueError(
            "Missing NISAY_API_KEY. Please set NISAY_API_KEY in your environment, "
            ".env file, or data/ai_provider_config.json. Obtain a key at https://api.nisay.store"
        )

    headers = {
        "Authorization": f"Bearer {resolved_key}",
        "Content-Type": "application/json"
    }

    is_batch = isinstance(texts, list)
    payload_text = texts if is_batch else [texts]

    context_str = context or f"Story genre: {category}. Apply Standard Khmer orthography."

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            payload = {
                "text": payload_text if is_batch else texts,
                "source_lang": "auto",
                "target_lang": "km",
                "model": MANDATORY_MODEL,
                "category": category,
                "context": context_str,
                "entity_glossary": entity_glossary or {}
            }

            resp = requests.post(
                TRANSLATE_ENDPOINT,
                headers=headers,
                json=payload,
                timeout=timeout
            )

            if resp.status_code == 401 or resp.status_code == 403:
                raise RuntimeError("403 Forbidden: check API Key at https://api.nisay.store")

            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", 2 * attempt))
                last_error = f"HTTP 429 Rate Limit. Retry-After: {retry_after}s"
                time.sleep(retry_after)
                continue

            if resp.status_code >= 500:
                last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
                time.sleep(2 * attempt)
                continue

            resp.raise_for_status()
            data = resp.json()

            if is_batch:
                items = data.get("translations", [])
                if items:
                    return [item.get("text", "") for item in items]
                # Fallback if translated_text was a list or single string
                return data.get("translated_text") or []

            return data.get("translated_text") or data.get("text", "")

        except requests.RequestException as e:
            if "403" in str(e):
                raise
            last_error = str(e)
            time.sleep(2 * attempt)

    raise RuntimeError(f"Gemini 3.8 Flash High translation failed after {max_retries} retries: {last_error}")


def main():
    """CLI runner for Nisay Khmer Translation."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    import argparse
    parser = argparse.ArgumentParser(description="Nisay Khmer Translate CLI (gemini-3.8-flash-high)")
    parser.add_argument("text", nargs="?", help="Text string to translate")
    parser.add_argument("--category", default=DEFAULT_CATEGORY, help="Story category (default: chinese_general)")
    parser.add_argument("--file", "-f", help="Optional text file to translate")

    args = parser.parse_args()

    input_text = args.text
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            input_text = f.read()

    if not input_text:
        parser.print_help()
        sys.exit(1)

    print(f"[*] Endpoint: {TRANSLATE_ENDPOINT}")
    print(f"[*] Model: {MANDATORY_MODEL} (Mandatory)")
    print(f"[*] Category: {args.category}")

    try:
        translated = translate_khmer(input_text, category=args.category)
        print("\n=== KHMER TRANSLATION RESULT ===")
        print(translated)
    except Exception as e:
        print(f"[-] Translation Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
