# agent/run_agent.py
# PURPOSE: Reasoning layer of the agent.
# Takes fetched content → sends to Groq LLM → returns structured JSON digest.
# This is the orchestrator — it calls fetch_content.py and talks to Groq.

import os
import json
import requests
from dotenv import load_dotenv
from fetch_content import fetch_all_sources

# Load secrets from your .env file
# In GitHub Actions, these come from GitHub Secrets instead
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
print("GROQ KEY CHECK:", "✅ Found" if os.getenv("GROQ_API_KEY") else "❌ NOT FOUND")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.3-70b-versatile"  # best free model on Groq

def build_context(sources: list[dict]) -> str:
    """
    Takes the list of fetched source dicts and formats them
    into one big text block the LLM can read.
    
    Agent concept: this is called "context packing" —
    stuffing everything the LLM needs into one prompt.
    """
    blocks = []
    for source in sources:
        # Skip sources that errored out during fetching
        if source["content"].startswith("[Error") or \
           source["content"].startswith("[Timeout") or \
           source["content"].startswith("[No AI"):
            continue

        block = (
            f"=== SOURCE: {source['label']} ===\n"
            f"URL: {source['url']}\n"
            f"CONTENT:\n{source['content']}"
        )
        blocks.append(block)

    return "\n\n".join(blocks)


def call_groq(context: str) -> dict:
    """
    Sends the context to Groq and returns parsed JSON digest.
    
    Agent concept: this is the "reasoning step" —
    the LLM reads everything and extracts what matters.
    """

    # The system prompt is the agent's instructions —
    # it tells the LLM exactly what role to play and what to return.
    # Being specific here = better, consistent output every time.
    system_prompt = """You are an expert AI researcher building a morning digest.
You will be given content scraped from trusted AI news sources.
Your job is to extract the most important AI, ML, and Deep Learning updates.

STRICT RULES:
- Only include topics related to AI, ML, Deep Learning, LLMs, or AI research
- Ignore anything unrelated (sports, politics, general tech, finance)
- Return ONLY valid JSON — no markdown, no backticks, no explanation
- If a field is unknown, use null

Return this exact JSON structure:
{
  "date": "YYYY-MM-DD",
  "summary": "2-3 sentence overview of today's biggest AI story",
  "products": [
    {
      "title": "product or feature name",
      "summary": "what it does and why it matters",
      "source": "source name",
      "url": "article url if available else null"
    }
  ],
  "research": [
    {
      "title": "paper or research name",
      "summary": "what was found or proposed",
      "authors": "authors if mentioned else null",
      "url": "link if available else null"
    }
  ],
  "industry": [
    {
      "title": "company move or industry news",
      "summary": "what happened and why it matters",
      "source": "source name",
      "url": "link if available else null"
    }
  ],
  "concept_of_the_day": {
    "title": "one AI/ML concept mentioned today worth learning",
    "explanation": "explain it simply in 2-3 sentences",
    "why_today": "why is this concept relevant to today's news"
  }
}

Include 3-5 items in each list. Quality over quantity."""

    today = __import__("datetime").date.today().isoformat()

    user_prompt = f"""Today is {today}.

Extract the AI morning digest from these sources:

{context}

Remember: return ONLY the JSON object, nothing else."""

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL,
        "temperature": 0.3,       # low = more factual, less creative
        "max_tokens": 3000,        # enough for full digest JSON
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
    }

    print("🧠 Sending to Groq...")
    response = requests.post(GROQ_URL, headers=headers, json=payload, timeout=30)
    print("Groq status code:", response.status_code)
    print("Groq response:", response.text[:300])
    response.raise_for_status()

    data = response.json()

    # Extract the raw text response from Groq
    raw = data["choices"][0]["message"]["content"]

    # Clean up in case LLM added markdown fences despite instructions
    # (LLMs sometimes ignore formatting rules — always defensive parse)
    clean = raw.strip()
    if clean.startswith("```"):
        # Remove ```json ... ``` wrapper
        clean = clean.split("```")[1]
        if clean.startswith("json"):
            clean = clean[4:]

    # Find the JSON object boundaries defensively
    json_start = clean.find("{")
    json_end = clean.rfind("}") + 1
    json_str = clean[json_start:json_end]

    digest = json.loads(json_str)
    print(f"✅ Digest generated for {digest.get('date', today)}")
    return digest


def run_agent() -> dict:
    """
    Master function — orchestrates the full agent pipeline:
    1. Fetch all sources (perception)
    2. Build context string
    3. Call Groq LLM (reasoning)
    4. Return structured digest
    
    send_email.py will import and call this.
    """
    print("🚀 Agent starting...\n")

    # Step 1: Perception
    sources = fetch_all_sources()

    # Step 2: Pack context
    context = build_context(sources)
    print(f"📦 Context built — {len(context)} characters sent to LLM\n")

    # Step 3: Reasoning
    digest = call_groq(context)

    return digest


# ── Quick test: run this file directly to see the digest JSON ─────────
# Command: python agent/run_agent.py
if __name__ == "__main__":
    digest = run_agent()
    # Pretty print the full JSON so you can inspect it
    print("\n📰 DIGEST OUTPUT:")
    print(json.dumps(digest, indent=2))