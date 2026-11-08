#!/usr/bin/env python3
"""
Turn a run_eval.py result into my run-log table.

    python score_eval.py results/run_<stamp>_before.json

run_eval.py records what came back. This applies each criterion's rule from
criteria.md to every trial, so the Run columns are counted by code and not by
me squinting at JSON. A criterion is MET only if it passes in every trial.

Each criterion_N takes one trial's results (a list of dicts, in the order the
scenario sent them) and returns (passed, cell_text).
"""

import json
import sys
from pathlib import Path

LABELS = ("human", "unsure", "ai")

TARGETS = {
    1: "0 of 10 human texts get the AI label",
    2: "AI mean minus human mean >= 0.40",
    3: "all 3 labels appear",
    4: "10/10 appeals correct, fake id 404",
    5: "7/7 bad bodies get a logged 4xx",
}


def _scored(results):
    return [r for r in results if r.get("status") == 200 and r.get("guess") in LABELS]


def criterion_1(results):
    """No known-human text gets the AI label. A text that crashed doesn't count as safe."""
    scored = _scored(results)
    flagged = sum(1 for r in scored if r["guess"] == "ai")
    missing = len(results) - len(scored)
    cell = f"{flagged}/{len(results)}" + (f" ({missing} not scored)" if missing else "")
    return flagged == 0 and missing == 0, cell


def criterion_2(results, n_ai=5):
    """First n_ai results are AI texts, the rest human. Gap of the means >= 0.40."""
    confidences = [r.get("confidence") for r in results]
    if any(not isinstance(c, (int, float)) for c in confidences) or len(results) <= n_ai:
        missing = sum(1 for c in confidences if not isinstance(c, (int, float)))
        return False, f"{missing} not scored"
    ai = confidences[:n_ai]
    human = confidences[n_ai:]
    gap = round(sum(ai) / len(ai) - sum(human) / len(human), 4)
    return gap >= 0.40, f"gap {gap:.2f}"


def criterion_3(results):
    """Each of the three labels shows up at least once."""
    seen = {r["guess"] for r in _scored(results)}
    missing = [label for label in LABELS if label not in seen]
    cell = f"{len(seen)}/3" + (f" (no {', '.join(missing)})" if missing else "")
    return not missing, cell


def _appeal_ok(r):
    return (r.get("status") == 200 and r.get("appeal_status") == 200
            and r.get("appeal_body_status") == "under_review"
            and r.get("status_after") == "under_review"
            and r.get("appeal_entries") == 1
            and r.get("original_decision_intact") is True)


def criterion_4(results):
    """Every real appeal correct, and at least one made-up id refused with no entry."""
    fakes = [r for r in results if "made-up" in str(r.get("sent", ""))]
    real = [r for r in results if r not in fakes]
    good = sum(1 for r in real if _appeal_ok(r))
    fake_ok = bool(fakes) and all(r.get("appeal_status") == 404 and r.get("appeal_entries") == 0
                                  for r in fakes)
    cell = f"{good}/{len(real)}, fake id {'404' if fake_ok else 'FAILED'}"
    return good == len(real) and fake_ok, cell


def criterion_5(results):
    """Each bad body: a 4xx with a JSON error code, and exactly one new log entry."""
    good = sum(1 for r in results
               if isinstance(r.get("status"), int) and 400 <= r["status"] < 500
               and r.get("error") and r.get("log_delta") == 1)
    return good == len(results), f"{good}/{len(results)}"


RULES = {1: criterion_1, 2: criterion_2, 3: criterion_3, 4: criterion_4, 5: criterion_5}


def verdict(passes):
    return "MET" if passes and all(passes) else "MISSED"


def table(run):
    """One markdown row per criterion: target, a cell per trial, verdict."""
    rows = []
    for scenario in sorted(run, key=lambda s: s.get("criterion") or 99):
        number = scenario.get("criterion")
        rule = RULES.get(number)
        if rule is None:
            continue
        outcomes = [rule(trial) for trial in scenario["trials"]]
        cells = " | ".join(cell for _, cell in outcomes)
        rows.append(f"| {number}. {scenario['name']} | {TARGETS[number]} | {cells} | "
                    f"{verdict([ok for ok, _ in outcomes])} |")
    return rows


def main():
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    run = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    trials = max(len(s["trials"]) for s in run)
    print("| Criterion | Target | " + " | ".join(f"Run {i}" for i in range(1, trials + 1))
          + " | Verdict |")
    print("|---|---|" + "---|" * trials + "---|")
    print("\n".join(table(run)))


if __name__ == "__main__":
    main()
