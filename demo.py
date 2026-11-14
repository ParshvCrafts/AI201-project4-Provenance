"""
A two-minute walkthrough against a running service.

    python serve.py          # terminal 1 (on my laptop: AI201_CPU_CORES=0-15 python serve.py)
    python demo.py           # terminal 2

Sends an AI-written text, a human one, a bad input and an appeal, and prints
what came back plus the log line each request left behind.
"""

import json
import os
import sys

import requests

from scenarios import SCENARIOS

URL = os.getenv("DEMO_URL", "http://127.0.0.1:5000")
AI_TEXT = SCENARIOS[1]["texts"][0]       # Claude-written explainer on remote work
HUMAN_TEXT = SCENARIOS[0]["texts"][2]    # Thoreau, Walden (1854)


def log_line(request_id):
    """The audit log line this request wrote, found by its X-Request-ID."""
    entries = requests.get(f"{URL}/log", params={"limit": 20}, timeout=10).json()["entries"]
    return next((e for e in reversed(entries) if e.get("request_id") == request_id), None)


def show(title, r, keys):
    body = r.json()
    print(f"\n=== {title}  ->  HTTP {r.status_code}")
    for k in keys:
        if k in body:
            print(f"  {k:12s} {body[k]}")
    line = log_line(r.headers.get("X-Request-ID"))
    if line:
        ops = {k: line[k] for k in ("request_id", "http_status", "duration_ms", "cpu_ms",
                                    "model_ms", "style_ms", "reason") if k in line}
        print(f"  log line     {json.dumps(ops)}")
    return body


def main():
    try:
        health = requests.get(f"{URL}/health", timeout=5).json()
    except requests.RequestException:
        sys.exit(f"Nothing answering at {URL}. Start it first: python serve.py")
    print(f"Service up. Model loaded: {health['detector_loaded']}. Log entries so far: {health['log_entries']}")

    ai = show("1. AI-written text (Claude)", requests.post(f"{URL}/submit", json={
        "text": AI_TEXT, "creator_id": "demo-ai"}, timeout=60),
        ["guess", "confidence", "model_score", "style_score", "label"])

    show("2. Human text (Thoreau, 1854)", requests.post(f"{URL}/submit", json={
        "text": HUMAN_TEXT, "creator_id": "demo-human"}, timeout=60),
        ["guess", "confidence", "model_score", "style_score", "label"])

    show("3. Bad input: too short", requests.post(f"{URL}/submit", json={
        "text": "Only five words in here.", "creator_id": "demo-bad"}, timeout=10),
        ["error", "message"])

    show("4. Appeal against result 1", requests.post(f"{URL}/appeal", json={
        "content_id": ai["content_id"], "reasoning": "I wrote this myself for class."}, timeout=10),
        ["status", "message"])

    status = requests.get(f"{URL}/content/{ai['content_id']}", timeout=10).json()
    print(f"\n=== 5. Item 1 now: status={status['status']}, appeals={status['appeal_count']}")
    print("\nNumbers over everything logged so far: python ops_report.py")


if __name__ == "__main__":
    main()
