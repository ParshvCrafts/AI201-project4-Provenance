"""
Read the audit log back and print what the service cost and where the time went.

    python ops_report.py              # every instrumented line in the log
    python ops_report.py --last 10    # only the last 10 scored submissions

Only lines written since the capstone instrumentation have `duration_ms`, so
older unit 7/8 lines are skipped automatically.
"""

import argparse
import math
import statistics

import audit


def pct(values, p):
    """Nearest-rank percentile: the smallest value with at least p% of values at or below it."""
    ordered = sorted(values)
    return ordered[max(0, math.ceil(p / 100 * len(ordered)) - 1)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--last", type=int, help="only the last N scored submissions")
    args = ap.parse_args()

    timed = [e for e in audit.read_entries() if "duration_ms" in e]
    scored = [e for e in timed if e.get("status") == "decided" and "model_ms" in e]
    if args.last:
        scored = scored[-args.last:]
    if not scored:
        print("No instrumented submissions in the log yet. Start `python serve.py` and send some.")
        return

    dur = [e["duration_ms"] for e in scored]
    cpu = [e["cpu_ms"] for e in scored]
    print(f"Scored submissions: {len(scored)}  ({scored[0]['timestamp']} to {scored[-1]['timestamp']})")
    print(f"  wall ms   mean {statistics.mean(dur):7.1f}  p50 {pct(dur, 50):7.1f}  "
          f"p95 {pct(dur, 95):7.1f}  max {max(dur):7.1f}")
    print(f"  CPU ms    mean {statistics.mean(cpu):7.1f}  p50 {pct(cpu, 50):7.1f}  "
          f"p95 {pct(cpu, 95):7.1f}  max {max(cpu):7.1f}")
    print(f"  CPU / wall: {statistics.mean(cpu) / statistics.mean(dur):.1f} cores busy on average")

    print("\nWhere the time goes (mean ms per scored submission):")
    total = statistics.mean(dur)
    for stage, name in (("model_ms", "GPT-2 (signal one)"), ("style_ms", "style (signal two)"),
                        ("score_ms", "combine + label")):
        m = statistics.mean(e[stage] for e in scored)
        print(f"  {name:20s} {m:7.1f}  ({m / total:5.1%})")
    rest = total - sum(statistics.mean(e[s] for e in scored) for s in ("model_ms", "style_ms", "score_ms"))
    print(f"  {'validation + log':20s} {rest:7.1f}  ({rest / total:5.1%})")

    other = [e for e in timed if e not in scored and e.get("status") != "decided"]
    if other:
        print(f"\nOther instrumented lines (rejections, appeals, errors): {len(other)}")
        counts = {}
        for e in other:
            key = f"{e.get('http_status')} {e.get('reason') or e.get('event')}"
            counts[key] = counts.get(key, 0) + 1
        for key, n in sorted(counts.items()):
            print(f"  {n:4d}  {key}")


if __name__ == "__main__":
    main()
