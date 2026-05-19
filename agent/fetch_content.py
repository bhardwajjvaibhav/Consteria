# agent/fetch_content.py
# PURPOSE: Perception layer of the agent.
# Fetches HTML from your trusted URLs and extracts clean readable text.
# The LLM in run_agent.py will only see what THIS file returns.

import requests
from bs4 import BeautifulSoup

# ── Your 10 trusted sources ──────────────────────────────────────────
# The agent reads ONLY these. No random web search. You control the inputs.
SOURCES = [
    {"url": "https://venturebeat.com/category/ai/", "label": "VentureBeat AI"},
    {"url": "https://www.theneurondaily.com/",                                                       "label": "The Neuron Daily"},
    {"url": "https://techcrunch.com/category/artificial-intelligence/",                              "label": "TechCrunch AI"},
    {"url": "https://bdtechtalks.com/category/ai-research/", "label": "BD Tech Talks AI Research"},
    {"url": "https://indianexpress.com/section/technology/artificial-intelligence/",                 "label": "Indian Express AI"},
    {"url": "https://openai.com/news/",                                                              "label": "OpenAI News"},
    {"url": "https://www.anthropic.com/research/introducing-anthropic-science",                      "label": "Anthropic Research"},
    {"url": "https://www.uber.com/in/en/blog/",                                                      "label": "Uber Engineering Blog"},
    {"url": "https://slogix.in/artificial-intelligence/latest-research-papers-in-artificial-intelligence/", "label": "Slogix AI Papers"},
    {"url": "https://paperswithcode.com/latest", "label": "Papers With Code",}
    ]

# ── AI/ML keyword filter ─────────────────────────────────────────────
# Since some sources (Uber blog, Science.org) cover non-AI topics,
# we only keep paragraphs that mention these keywords.
# This is called "relevance filtering" — a core agent technique.
AI_KEYWORDS = [
    "artificial intelligence", "machine learning", "deep learning",
    "neural network", "llm", "large language model", "generative ai",
    "transformer", "model", "training", "inference", "dataset",
    "gpt", "claude", "gemini", "mistral", "reinforcement learning",
    "computer vision", "nlp", "natural language", "diffusion", "agent",
]

def is_ai_relevant(text: str) -> bool:
    """Returns True if the text contains at least one AI/ML keyword."""
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in AI_KEYWORDS)


def fetch_source(source: dict) -> dict:
    """
    Fetches one URL, strips HTML noise, filters for AI content.
    Returns a dict with label, url, and clean content string.
    """
    headers = {
        # Pretend to be a real browser — some sites block plain Python requests
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    try:
        print(f"📡 Fetching: {source['label']}")
        response = requests.get(source["url"], headers=headers, timeout=12)
        response.raise_for_status()  # raises error if 404, 500 etc.

        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")

        # Remove noise tags — these never contain real content
        for tag in soup(["script", "style", "nav", "footer",
                          "header", "aside", "form", "iframe"]):
            tag.decompose()  # completely removes the tag from the tree

        # Extract all paragraphs and headings
        text_blocks = []
        for tag in soup.find_all(["p", "h1", "h2", "h3", "li", "a"]):
            text = tag.get_text(separator=" ").strip()

            # Only keep blocks that are:
            # 1. Long enough to be meaningful (not "Click here", "Home", etc.)
            # 2. Relevant to AI/ML based on our keyword filter
            if len(text) > 60 and is_ai_relevant(text):
                text_blocks.append(text)

        # Join all relevant blocks, cap at 4000 chars to save LLM tokens
        # (Groq free tier has token limits — we respect that here)
        content = "\n".join(text_blocks)[:4000]

        if not content:
            # Site was fetched but had no AI-relevant content after filtering
            content = "[No AI-relevant content found on this page]"

        return {
            "label": source["label"],
            "url": source["url"],
            "content": content,
        }

    except requests.exceptions.Timeout:
        print(f"⏱ Timeout: {source['label']}")
        return {"label": source["label"], "url": source["url"], "content": "[Timeout]"}

    except requests.exceptions.RequestException as e:
        print(f"⚠️  Failed: {source['label']} — {e}")
        return {"label": source["label"], "url": source["url"], "content": f"[Error: {e}]"}


def fetch_all_sources() -> list[dict]:
    """
    Fetches all 10 sources and returns a list of content dicts.
    This is the only function run_agent.py will import and call.
    """
    results = []
    for source in SOURCES:
        result = fetch_source(source)
        results.append(result)
    print(f"\n✅ Fetched {len(results)} sources\n")
    return results


# ── Quick test: run this file directly to see what gets fetched ───────
# Command: python agent/fetch_content.py
if __name__ == "__main__":
    sources = fetch_all_sources()
    for s in sources:
        print(f"\n{'='*50}")
        print(f"SOURCE: {s['label']}")
        print(f"URL: {s['url']}")
        print(f"CONTENT PREVIEW:\n{s['content'][:300]}...")