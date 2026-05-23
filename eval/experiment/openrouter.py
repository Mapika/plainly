"""
OpenRouter API client — stdlib only (urllib, json, time, os).
"""
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

# ---------------------------------------------------------------------------
# Key loading
# ---------------------------------------------------------------------------

def _load_key() -> str:
    env_key = os.environ.get("OPENROUTER_API_KEY", "")
    if env_key:
        return env_key.strip()
    key_path = Path(__file__).parent.parent / ".secrets" / "openrouter.key"
    if key_path.exists():
        return key_path.read_text().strip()
    raise RuntimeError(
        "No OpenRouter API key found. Set OPENROUTER_API_KEY env var or "
        "create eval/.secrets/openrouter.key"
    )


# ---------------------------------------------------------------------------
# Core chat completion
# ---------------------------------------------------------------------------

def chat_completion(
    model: str,
    messages: list[dict],
    temperature: float = 0.7,
    max_tokens: int = 500,
    timeout: int = 120,
    retries: int = 3,
) -> dict:
    """
    POST to OpenRouter chat completions.

    Returns one of:
      {"text": str, "usage": dict, "raw_model": str}
      {"error": str}
    """
    key = _load_key()
    url = "https://openrouter.ai/api/v1/chat/completions"
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }

    last_error = ""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            choices = body.get("choices") or []
            if not choices:
                return {"error": f"No choices in response: {body}"}
            text = choices[0].get("message", {}).get("content", "")
            usage = body.get("usage", {})
            raw_model = body.get("model", model)
            return {"text": text, "usage": usage, "raw_model": raw_model}
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            last_error = f"HTTP {e.code}: {err_body}"
            if e.code in (400, 401, 403, 404):
                # Non-retryable
                return {"error": last_error}
        except urllib.error.URLError as e:
            last_error = f"URLError: {e.reason}"
        except TimeoutError:
            last_error = "Timeout"
        except Exception as e:
            last_error = f"Unexpected: {e}"

        if attempt < retries - 1:
            wait = 2 ** attempt
            time.sleep(wait)

    return {"error": last_error}


# ---------------------------------------------------------------------------
# Account usage helper
# ---------------------------------------------------------------------------

def account_usage() -> float:
    """
    GET /api/v1/auth/key and return cumulative data.usage (USD).
    Returns float or raises on error.
    """
    key = _load_key()
    url = "https://openrouter.ai/api/v1/auth/key"
    headers = {"Authorization": f"Bearer {key}"}
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        return float(body.get("data", {}).get("usage", 0.0))
    except Exception as e:
        print(f"[openrouter] account_usage() failed: {e}")
        return 0.0
