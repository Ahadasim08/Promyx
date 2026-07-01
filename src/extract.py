"""Step 1: extract promises from a meeting transcript using Groq.

Usage:
    python src/extract.py data/transcripts/meeting1.txt
    python src/extract.py --all
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

ROOT = Path(__file__).resolve().parent.parent
TICKETS_PATH = ROOT / "data" / "jira_tickets.json"
TRANSCRIPTS_DIR = ROOT / "data" / "transcripts"
OUT_DIR = ROOT / "data" / "extracted"

MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You extract promises people made during a meeting transcript.

A promise is a real commitment to do something ("I'll fix X by Friday", "I'm going to finish Y soon").
Do NOT extract opinions, suggestions, or general chatter ("we should look into X", "might need a refresh eventually").

You are given a list of known Jira tickets (key, summary, status). For EVERY promise, you MUST check
it against EVERY ticket summary for a match before deciding there is none. Match by meaning, not just
exact word overlap - a promise can reuse the ticket summary's wording closely (e.g. promise "fix the
broken password reset email" against ticket summary "Fix broken password reset email" is an obvious
direct match: use that ticket's key) or paraphrase it loosely (e.g. "that thing with the checkout
tests" against ticket summary "Fix flaky checkout test" is still a match on topic). Go ticket by ticket
and check for wording overlap before giving up. Only use null if you have checked every ticket in the
list and genuinely none relate to the promise's subject.

Deadlines: if the speaker states a date or day, convert it to YYYY-MM-DD using the meeting date as
reference. If no deadline is stated, use the JSON value null (not the string "null").

Respond with ONLY a JSON object of this exact shape, no prose, no markdown fences. Use real JSON null
(not the string "null") for missing ticket or deadline:
{
  "promises": [
    {
      "speaker": "string",
      "promise_text": "exact quote from transcript",
      "ticket": "PROM-4" or null,
      "deadline": "YYYY-MM-DD" or null
    }
  ]
}
"""


def load_tickets():
    data = json.loads(TICKETS_PATH.read_text(encoding="utf-8"))
    return data["tickets"]


def extract_meeting_date(transcript_text: str) -> str:
    m = re.search(r"(\d{4}-\d{2}-\d{2})", transcript_text)
    return m.group(1) if m else "unknown"


def build_user_prompt(transcript_text: str, meeting_date: str, tickets: list) -> str:
    ticket_lines = "\n".join(
        f"- {t['key']}: {t['summary']} (status: {t['status']})" for t in tickets
    )
    return f"""Meeting date: {meeting_date}

Known Jira tickets:
{ticket_lines}

Transcript:
{transcript_text}
"""


def run_extraction(client: Groq, transcript_path: Path, tickets: list) -> dict:
    text = transcript_path.read_text(encoding="utf-8")
    meeting_date = extract_meeting_date(text)
    user_prompt = build_user_prompt(text, meeting_date, tickets)

    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )
    content = resp.choices[0].message.content
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        print(f"WARNING: model returned invalid JSON for {transcript_path.name}", file=sys.stderr)
        print(content, file=sys.stderr)
        return {"promises": []}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("transcript", nargs="?", help="path to a single transcript file")
    parser.add_argument("--all", action="store_true", help="process every transcript in data/transcripts")
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("GROQ_API_KEY not set. Put it in .env at project root.", file=sys.stderr)
        sys.exit(1)

    client = Groq(api_key=api_key)
    tickets = load_tickets()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.all:
        targets = sorted(TRANSCRIPTS_DIR.glob("*.txt"))
    elif args.transcript:
        targets = [Path(args.transcript)]
    else:
        parser.error("give a transcript path or --all")
        return

    for path in targets:
        print(f"Extracting: {path.name}")
        result = run_extraction(client, path, tickets)
        out_path = OUT_DIR / (path.stem + ".json")
        out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"  -> {out_path} ({len(result.get('promises', []))} promises)")


if __name__ == "__main__":
    main()
