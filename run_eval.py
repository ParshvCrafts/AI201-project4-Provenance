#!/usr/bin/env python3
"""
Run your five criteria three times each.  <- UNIT 8, MILESTONE 3

    python app.py                              # in one terminal
    python run_eval.py --label before          # in another
    python run_eval.py --label after

The attack set tests what staff thought to test. This tests what *you* thought
to test, and the two rarely overlap much. Both count.

Fill in `scenarios.py` first — that's where you say what each criterion needs
run against it. A criterion about false positives needs your own writing. One
about label coverage needs inputs across the score range.

!! Three trials, and **your first signal runs a model, so identical input can
score differently twice.** That's exactly why repeats matter here.

This does the sending and the recording. It does not decide whether a trial
passed — that depends on the criterion you wrote, so the Verdict column comes
back blank.
"""

import argparse
import datetime as dt
import json
import sys
import uuid
from pathlib import Path

import config

# Windows consoles often run a codepage that can't print every character in
# this file's help text. Without this, `--help` ends in a UnicodeEncodeError
# traceback instead of the help — which is a miserable first thing to hit.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(errors="replace")
    except (AttributeError, ValueError):  # not a normal text stream
        pass


DEFAULT_URL = f"http://{config.HOST}:{config.PORT}"


def bodies_for(scenario):
    """
    The request bodies one scenario sends.

    A "texts" scenario gets a creator_id made up for it. A "bodies" scenario is
    sent exactly as written, which is how a bad-input criterion says things a
    string can't — no `text` field, a null, something enormous.
    """
    if scenario.get("bodies"):
        return list(scenario["bodies"])
    return [
        {"text": text, "creator_id": f"eval_{scenario['name'][:12]}_{i}"}
        for i, text in enumerate(scenario["texts"], 1)
    ]


def log_count(http, url):
    """How many entries the audit log holds right now (from GET /health)."""
    return http.get(f"{url}/health", timeout=10).json()["log_entries"]


def recent_entries(http, url, content_id, n=10):
    """The last few log entries that belong to one content_id."""
    entries = http.get(f"{url}/log", params={"limit": n}, timeout=10).json()["entries"]
    return [e for e in entries if e.get("content_id") == content_id]


def check_appeal(http, url, content_id, timeout):
    """
    Appeal one real content_id and check what criterion 4 asks for: a 200 with
    status under_review, exactly one new appeal entry, and the original
    decision entry still there with status `decided`.
    """
    response = http.post(f"{url}/appeal", timeout=timeout,
                             json={"content_id": content_id,
                                   "reasoning": "I wrote this myself. (run_eval appeal check)"})
    body = response.json() if response.content else {}
    mine = recent_entries(http, url, content_id)
    decisions = [e for e in mine if e.get("event", "decision") == "decision"
                 and e.get("status") == "decided"]
    return {
        "appeal_status": response.status_code,
        "appeal_body_status": body.get("status"),
        "status_after": http.get(f"{url}/content/{content_id}",
                                     timeout=10).json().get("status"),
        "appeal_entries": sum(1 for e in mine if e.get("event") == "appeal"),
        "original_decision_intact": len(decisions) == 1,
    }


def check_fake_appeal(http, url, timeout):
    """An appeal against an id that was never issued: 404, no appeal entry."""
    fake_id = f"never-issued-{uuid.uuid4()}"
    response = http.post(f"{url}/appeal", timeout=timeout,
                             json={"content_id": fake_id, "reasoning": "Made-up id."})
    tail = http.get(f"{url}/log", params={"limit": 3}, timeout=10).json()["entries"]
    return {
        "sent": "appeal against a made-up content_id",
        "appeal_status": response.status_code,
        "appeal_entries": sum(1 for e in tail if e.get("event") == "appeal"
                              and e.get("content_id") == fake_id),
    }


def describe(body):
    """A short, readable note of what was sent — for the report."""
    if set(body) == {"text", "creator_id"} and isinstance(body.get("text"), str):
        text = body["text"]
        return text[:70] if text else "(empty text)"
    return json.dumps(body)[:120]


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--trials", type=int, default=3)
    parser.add_argument("--label", default="")
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--timeout", type=float, default=90.0)
    args = parser.parse_args()

    try:
        import requests
    except ImportError:
        print("The `requests` package isn't installed.\n"
              "Run: pip install -r requirements.txt", file=sys.stderr)
        sys.exit(1)

    try:
        import scenarios
    except ImportError:
        print("No scenarios.py found. Milestone 3 starts by filling it in.",
              file=sys.stderr)
        sys.exit(1)

    problems = scenarios.validate()
    if problems:
        print("scenarios.py has problems:\n", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        sys.exit(1)

    try:
        requests.get(f"{args.url}/health", timeout=5)
    except Exception:  # noqa: BLE001
        print(f"Nothing answering at {args.url}. Start it:  python app.py",
              file=sys.stderr)
        sys.exit(1)

    # In my first two "before" runs Windows refused to open a socket once
    # (WinError 10055) and that request never reached the service, so a trial
    # failed on my harness, not on my pipeline. Retrying only the *connect*
    # step is safe even for POST: if the connection never opened, nothing was
    # sent, so nothing can be submitted twice. Read errors are not retried.
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry

    http = requests.Session()
    http.mount("http://", HTTPAdapter(max_retries=Retry(
        total=None, connect=5, read=0, status=0, other=0,
        backoff_factor=0.5, allowed_methods=None)))

    if args.trials < 3:
        print(f"!! {args.trials} trial(s). The submission asks for three.\n")

    rows = []
    for scenario in scenarios.SCENARIOS:
        print(f"\n{scenario['name']}  (criterion {scenario.get('criterion') or '—'})")

        trials = []
        for trial in range(1, args.trials + 1):
            results = []
            for i, body in enumerate(bodies_for(scenario), 1):
                preview = describe(body)
                try:
                    entries_before = log_count(http, args.url)
                    response = http.post(f"{args.url}/submit", json=body,
                                             timeout=args.timeout)
                    payload = response.json() if response.content else {}
                    result = {
                        "status": response.status_code,
                        "guess": payload.get("guess"),
                        "confidence": payload.get("confidence"),
                        "model_score": payload.get("model_score"),
                        "style_score": payload.get("style_score"),
                        "label": payload.get("label"),
                        "error": payload.get("error"),
                        # Entries this one request added to the audit log.
                        "log_delta": log_count(http, args.url) - entries_before,
                        "sent": preview,
                    }
                    if scenario.get("appeal") and response.status_code == 200:
                        result.update(check_appeal(http, args.url,
                                                   payload["content_id"], args.timeout))
                    results.append(result)
                except Exception as exc:  # noqa: BLE001
                    results.append({"status": None, "error": f"{type(exc).__name__}: {exc}",
                                    "sent": preview})

            for _ in range(scenario.get("fake_appeals", 0)):
                try:
                    results.append(check_fake_appeal(http, args.url, args.timeout))
                except Exception as exc:  # noqa: BLE001
                    results.append({"appeal_status": None,
                                    "error": f"{type(exc).__name__}: {exc}",
                                    "sent": "appeal against a made-up content_id"})

            trials.append(results)
            guesses = [r.get("guess") or "—" for r in results]
            print(f"  trial {trial}: {', '.join(guesses)}")

        rows.append({"scenario": scenario, "trials": trials})

    write_report(rows, args)


def write_report(rows, args):
    config.RESULTS_DIR.mkdir(exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y-%m-%d_%H%M")
    label = f"_{args.label}" if args.label else ""
    path = config.RESULTS_DIR / f"run_{stamp}{label}.md"

    n = args.trials
    headers = " | ".join(f"Run {i}" for i in range(1, n + 1))
    divider = "|".join(["---"] * n)

    lines = [
        f"# Run log{f' — {args.label}' if args.label else ''}",
        "",
        "- Produced by: `run_eval.py::main`",
        "- Service: `app.py::submit` · scoring: `scoring.py::combine_signals`",
        f"- {n} trials per criterion · {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "Fill in Target from `criteria.md`, and Run and Verdict from the output",
        "underneath. Whether a trial passed depends on the criterion you wrote.",
        "",
        f"| Criterion | Target | {headers} | Verdict |",
        f"|---|---|{divider}|---|",
    ]

    for row in rows:
        scenario = row["scenario"]
        number = scenario.get("criterion")
        name = f"{number}. {scenario['name']}" if number else scenario["name"]
        lines.append(f"| {name} |  | {' | '.join([' '] * n)} |  |")

    lines += ["", "---", "", "## What actually came back", "",
              "Real output. Paste the relevant parts into your README — the rubric",
              "asks for the actual JSON, not a description of it.", ""]

    for row in rows:
        scenario = row["scenario"]
        lines += [f"### {scenario['name']}", ""]
        for trial_number, results in enumerate(row["trials"], 1):
            lines += [f"**Trial {trial_number}**", "", "```json",
                      json.dumps(results, indent=2), "```", ""]

    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWrote {path.relative_to(config.ROOT)}")

    # The same results as JSON, so score_eval.py can count them instead of me.
    raw = [{"name": r["scenario"]["name"], "criterion": r["scenario"].get("criterion"),
            "trials": r["trials"]} for r in rows]
    path.with_suffix(".json").write_text(json.dumps(raw, indent=2), encoding="utf-8")
    print(f"Wrote {path.with_suffix('.json').relative_to(config.ROOT)}")
    print("Commit it. It's the evidence the test actually happened.")


if __name__ == "__main__":
    main()
