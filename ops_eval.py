"""
Capstone test: start the service the way RUNNING.md says, push a fixed mix of
requests through it, and score my five capstone criteria from the audit log.

    python ops_eval.py --label before            # three trials (default)
    python ops_eval.py --label after --trials 3

Each trial is a fresh `python serve.py` process on its own port, so trial 2
doesn't inherit trial 1's loaded model, warm caches or rate-limit counters.
Requests go one at a time, which keeps the process-wide CPU timer honest.

Per trial it sends 28 requests:
  15 real submissions   the 10 human texts from criterion 1 of unit 8 plus the
                        5 AI texts from criterion 2, each as its own creator
   1 appeal             against the first submission
   6 bad inputs         not JSON, no text, too short, too long (20,001 chars),
                        a 1.1 MB body, an appeal for an id that doesn't exist
   6 flood requests     one creator, six times in a row: 5 refused as too
                        short, then a 429 from the rate limiter

Writes results/ops_<stamp>_<label>.json and .md.
"""

import argparse
import json
import math
import statistics
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

import config
from scenarios import SCENARIOS

ROOT = Path(__file__).parent
PORT = 5055
URL = f"http://127.0.0.1:{PORT}"
REQUIRED = ("timestamp", "request_id", "route", "http_status", "input_bytes", "duration_ms", "cpu_ms")

HUMAN = SCENARIOS[0]["texts"]       # criterion 1 of unit 8, 10 Gutenberg passages
AI = SCENARIOS[1]["texts"][:5]      # criterion 2 of unit 8, the 5 AI texts

# Targets, copied from criteria.md (capstone section).
COLD_START_MAX_S = 30
FAST_MS = 1000
FAST_NEEDED = 14            # of 15
CPU_MEAN_MAX_MS = 1000
SHORT = "far too short to judge"


def wait_until_ready(proc, timeout=120):
    """Seconds from launch until /health says the model is loaded."""
    t0 = time.perf_counter()
    while time.perf_counter() - t0 < timeout:
        if proc.poll() is not None:
            raise RuntimeError(f"serve.py exited with code {proc.returncode}")
        try:
            r = requests.get(f"{URL}/health", timeout=2)
            if r.ok and r.json().get("detector_loaded"):
                return time.perf_counter() - t0
        except requests.RequestException:
            pass
        time.sleep(0.2)
    raise TimeoutError("service never became ready")


def request_plan(tag):
    """(kind, method, path, json_body or None, raw_data or None). Order matters."""
    plan = []
    for i, text in enumerate(HUMAN):
        plan.append(("human", "POST", "/submit", {"text": text, "creator_id": f"{tag}-h{i}"}, None))
    for i, text in enumerate(AI):
        plan.append(("ai", "POST", "/submit", {"text": text, "creator_id": f"{tag}-a{i}"}, None))
    plan.append(("appeal", "POST", "/appeal", "FIRST_ID", None))
    plan += [
        ("bad", "POST", "/submit", None, b"this is not json"),
        ("bad", "POST", "/submit", {"creator_id": f"{tag}-b1"}, None),
        ("bad", "POST", "/submit", {"text": SHORT, "creator_id": f"{tag}-b2"}, None),
        ("bad", "POST", "/submit", {"text": "word " * 4000 + "x", "creator_id": f"{tag}-b3"}, None),
        ("bad", "POST", "/submit", None, b'{"text": "' + b"a" * 1_100_000 + b'"}'),
        ("bad", "POST", "/appeal", {"content_id": "00000000-0000-4000-8000-000000000000",
                                    "reasoning": "I wrote this."}, None),
    ]
    plan += [("flood", "POST", "/submit", {"text": SHORT, "creator_id": f"{tag}-flood"}, None)] * 6
    return plan


def run_trial(n, label, log_offset):
    tag = f"ops-{label}-t{n}-{datetime.now():%H%M%S}"
    env = {**__import__("os").environ, "PORT": str(PORT), "HOST": "127.0.0.1"}
    proc = subprocess.Popen([sys.executable, "serve.py"], cwd=ROOT, env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        cold_s = wait_until_ready(proc)
        http = requests.Session()
        sent, first_id = [], None
        for kind, method, path, body, raw in request_plan(tag):
            if body == "FIRST_ID":
                body = {"content_id": first_id, "reasoning": "I wrote this myself."}
            t0 = time.perf_counter()
            if raw is not None:
                r = http.request(method, URL + path, data=raw,
                                 headers={"Content-Type": "application/json"}, timeout=60)
            else:
                r = http.request(method, URL + path, json=body, timeout=60)
            client_ms = (time.perf_counter() - t0) * 1000
            data = r.json() if r.headers.get("Content-Type", "").startswith("application/json") else {}
            if first_id is None and kind == "human" and r.status_code == 200:
                first_id = data["content_id"]
            sent.append({"kind": kind, "path": path, "status": r.status_code,
                         "request_id": r.headers.get("X-Request-ID"),
                         "client_ms": round(client_ms, 1), "guess": data.get("guess"),
                         "error": data.get("error")})
    finally:
        proc.terminate()
        proc.wait(timeout=30)

    # Read back only the lines this trial wrote.
    lines = config.AUDIT_LOG.read_text(encoding="utf-8").splitlines()[log_offset:]
    entries = [json.loads(l) for l in lines if l.strip()]
    by_id = {}
    for e in entries:
        if e.get("request_id"):
            by_id.setdefault(e["request_id"], []).append(e)

    # Criterion 2: exactly one complete line per request, status matching the response.
    logged_ok = 0
    for s in sent:
        hits = by_id.get(s["request_id"], [])
        if (len(hits) == 1 and all(k in hits[0] for k in REQUIRED)
                and hits[0]["http_status"] == s["status"]):
            logged_ok += 1
            s["log"] = hits[0]
        else:
            s["log_problem"] = f"{len(hits)} lines" if len(hits) != 1 else "missing field or wrong status"

    accepted = [s for s in sent if s["kind"] in ("human", "ai") and s["status"] == 200 and "log" in s]
    durations = [s["log"]["duration_ms"] for s in accepted]
    cpus = [s["log"]["cpu_ms"] for s in accepted]
    stages = {k: statistics.mean(s["log"][k] for s in accepted) for k in ("model_ms", "style_ms", "score_ms")}
    human_ai = sum(1 for s in sent if s["kind"] == "human" and s["guess"] == "ai")
    startup = [e for e in entries if e.get("event") == "startup"]

    return {
        "trial": n,
        "c1_cold_start_s": round(cold_s, 2),
        "model_load_s": startup[-1]["model_load_s"] if startup else None,
        "c2_logged": logged_ok, "c2_sent": len(sent),
        "c3_fast": sum(1 for d in durations if d < FAST_MS), "c3_of": len(durations),
        "c4_cpu_mean_ms": round(statistics.mean(cpus), 1),
        "c5_human_as_ai": human_ai,
        "duration_ms": {"p50": statistics.median(durations), "max": max(durations),
                        "p95": sorted(durations)[math.ceil(0.95 * len(durations)) - 1]},
        "stage_mean_ms": {k: round(v, 1) for k, v in stages.items()},
        "client_ms_mean": round(statistics.mean(s["client_ms"] for s in accepted), 1),
        "statuses": [s["status"] for s in sent],
        "requests": sent,
    }


def verdicts(trials):
    c = {
        1: ("Cold start under 30 s", "3 of 3", [f"{t['c1_cold_start_s']}s" for t in trials],
            all(t["c1_cold_start_s"] < COLD_START_MAX_S for t in trials)),
        2: ("Every request leaves one complete log line", "28 of 28, every trial",
            [f"{t['c2_logged']}/{t['c2_sent']}" for t in trials],
            all(t["c2_logged"] == t["c2_sent"] for t in trials)),
        3: ("Accepted submissions under 1,000 ms", "14 of 15, every trial",
            [f"{t['c3_fast']}/{t['c3_of']}" for t in trials],
            all(t["c3_fast"] >= FAST_NEEDED for t in trials)),
        4: ("Mean CPU per accepted submission", "at most 1,000 ms, every trial",
            [f"{t['c4_cpu_mean_ms']:.0f} ms" for t in trials],
            all(t["c4_cpu_mean_ms"] <= CPU_MEAN_MAX_MS for t in trials)),
        5: ("Human texts labelled AI", "0 of 10, every trial",
            [f"{t['c5_human_as_ai']}/10" for t in trials],
            all(t["c5_human_as_ai"] == 0 for t in trials)),
    }
    return c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--trials", type=int, default=3)
    args = ap.parse_args()

    trials = []
    for n in range(1, args.trials + 1):
        config.LOG_DIR.mkdir(exist_ok=True)
        config.AUDIT_LOG.touch()
        offset = len(config.AUDIT_LOG.read_text(encoding="utf-8").splitlines())
        print(f"trial {n}: starting serve.py ...", flush=True)
        t = run_trial(n, args.label, offset)
        trials.append(t)
        print(f"  cold {t['c1_cold_start_s']}s  logged {t['c2_logged']}/{t['c2_sent']}  "
              f"fast {t['c3_fast']}/{t['c3_of']}  cpu {t['c4_cpu_mean_ms']}ms  "
              f"human->ai {t['c5_human_as_ai']}  p50 {t['duration_ms']['p50']}ms  "
              f"stages {t['stage_mean_ms']}", flush=True)

    stamp = f"{datetime.now():%Y-%m-%d_%H%M}"
    out = config.RESULTS_DIR / f"ops_{stamp}_{args.label}"
    out.with_suffix(".json").write_text(json.dumps(trials, indent=2), encoding="utf-8")

    rows = verdicts(trials)
    md = [f"# Capstone run: {args.label} ({stamp})", "",
          "| Criterion | Target | " + " | ".join(f"Run {t['trial']}" for t in trials) + " | Verdict |",
          "|---|---|" + "---|" * len(trials) + "---|"]
    for n, (name, target, vals, met) in rows.items():
        md.append(f"| {n}. {name} | {target} | " + " | ".join(vals) + f" | {'MET' if met else 'MISSED'} |")
    md += ["", "| Trial | p50 ms | p95 ms | max ms | GPT-2 ms | style ms | scoring ms | client ms | model load s |",
           "|---|---|---|---|---|---|---|---|---|"]
    for t in trials:
        d, s = t["duration_ms"], t["stage_mean_ms"]
        md.append(f"| {t['trial']} | {d['p50']} | {d['p95']} | {d['max']} | {s['model_ms']} | "
                  f"{s['style_ms']} | {s['score_ms']} | {t['client_ms_mean']} | {t['model_load_s']} |")
    md += ["", "Status codes, in send order:", ""]
    md += [f"- trial {t['trial']}: {' '.join(map(str, t['statuses']))}" for t in trials]
    out.with_suffix(".md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))
    print(f"\nwrote {out}.md and .json")


if __name__ == "__main__":
    main()
