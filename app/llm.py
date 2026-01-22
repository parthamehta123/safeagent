import json
import re
from typing import List
from openai import OpenAI

from app.models import AgentPlan
from app.config import settings

client = OpenAI(api_key=settings.openai_api_key)

MODEL = "gpt-4o-mini"

SYSTEM_SELECT = """\
You are SafeAgent.

Task:
Given a user request and a list of files in a repository, return ONLY a JSON list
of the files that should be edited.

Rules:
- Only choose files that already exist
- Do not invent files
- Return JSON only, no commentary

Example:
["README.md", "app/main.py"]
"""

SYSTEM_PATCH = """\
You are SafeAgent, a secure code modification assistant.

You must output ONLY valid JSON in this schema:

{
  "edits": [
    {
      "file_path": "string",
      "original_hash": "string",
      "unified_diff": "string"
    }
  ]
}

Rules:
- No explanations
- Do not invent files
- unified_diff must be valid git apply format
- Only include minimal required changes
"""

SYSTEM_REPAIR = """\
You are SafeAgent fixing a failed git patch.

You will be given:
- The original user intent
- The file content
- The previous diff
- The git apply error

You must return ONLY valid JSON in this schema:

{
  "edits": [
    {
      "file_path": "string",
      "original_hash": "string",
      "unified_diff": "string"
    }
  ]
}

Rules:
- unified_diff must be valid git diff format
- Must apply cleanly with git apply
- Do not change unrelated lines
- Do not invent files
- No explanations
"""


# -------------------------------
# Robust JSON extraction
# -------------------------------


def extract_json(text: str) -> str:
    """
    Extract first JSON object or array from model output.
    Handles markdown fences, commentary, etc.
    """
    # Try direct parse first
    try:
        json.loads(text)
        return text
    except Exception:
        pass

    # Strip ```json fences
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)

    # Try again
    try:
        json.loads(text)
        return text
    except Exception:
        pass

    # Fallback: regex extraction of first {...} or [...]
    match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON found in model output:\n{text}")

    return match.group(1)


# -------------------------------
# Core JSON LLM caller
# -------------------------------


def _ask_json(system: str, user: str, retries: int = 3):
    last_raw = None

    for i in range(retries):
        resp = client.chat.completions.create(
            model=MODEL,
            temperature=0,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )

        raw = resp.choices[0].message.content.strip()
        last_raw = raw

        try:
            cleaned = extract_json(raw)
            return json.loads(cleaned)
        except Exception as e:
            if i == retries - 1:
                raise RuntimeError(
                    f"LLM failed JSON after {retries} attempts.\n\nRaw output:\n{last_raw}"
                )


# -------------------------------
# File selection
# -------------------------------


def choose_files(prompt: str, file_list: List[str]) -> List[str]:
    limited = file_list[:300]

    data = _ask_json(
        SYSTEM_SELECT,
        f"User request:\n{prompt}\n\nFiles:\n{json.dumps(limited, indent=2)}",
    )

    if not isinstance(data, list):
        raise RuntimeError(f"Model did not return list. Got: {type(data)} → {data}")

    # Product guardrail: if root README.md selected, only use that
    if "README.md" in data:
        return ["README.md"]

    return data


# -------------------------------
# Patch planning
# -------------------------------


def build_plan(prompt: str, files: dict, manifest: dict) -> AgentPlan:
    context = ""
    for path, content in files.items():
        context += f"\n### {path}\n{content[:4000]}\n"

    payload = {
        "prompt": prompt,
        "files": list(files.keys()),
        "hashes": {k: manifest[k] for k in files.keys()},
    }

    data = _ask_json(
        SYSTEM_PATCH,
        f"""
User request:
{prompt}

Context:
{context}

Manifest:
{json.dumps(payload, indent=2)}
""",
    )

    return AgentPlan(**data)


def repair_plan(prompt: str, files: dict, manifest: dict, failed_diff: str, error: str):
    context = ""
    for path, content in files.items():
        context += f"\n### {path}\n{content[:4000]}\n"

    payload = {
        "prompt": prompt,
        "files": list(files.keys()),
        "hashes": {k: manifest[k] for k in files.keys()},
        "previous_diff": failed_diff,
        "git_error": error,
    }

    data = _ask_json(
        SYSTEM_REPAIR,
        f"Context:\n{context}\n\nFailure info:\n{json.dumps(payload, indent=2)}",
    )

    return AgentPlan(**data)


SYSTEM_REWRITE = """\
You are SafeAgent performing a full file rewrite.

You must return ONLY the updated file content.
No explanations.
No markdown fences.
No JSON.
Just the raw file.
"""


def repair_full_file(prompt: str, file_path: str, content: str) -> str:
    resp = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_REWRITE},
            {
                "role": "user",
                "content": f"""
User intent:
{prompt}

File: {file_path}

Current content:
{content}

Task:
Return the full updated file content with minimal changes.
""",
            },
        ],
    )

    return resp.choices[0].message.content.strip()
