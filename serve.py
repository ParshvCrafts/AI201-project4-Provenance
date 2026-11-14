"""
The one command that runs Provenance Guard for real (capstone, Path B).

    python serve.py

What it does that `python app.py` doesn't:

1. Loads GPT-2 BEFORE it accepts requests, so the first writer doesn't wait
   for the model and /health says detector_loaded: true from the start.
2. Writes a `startup` line to logs/audit.jsonl with how long that took.
3. Serves through waitress, a production WSGI server that runs on Windows
   (gunicorn doesn't). No debugger, no reloader.

HOST and PORT come from the environment, same as app.py. Ctrl+C stops it.
"""

import os
import platform
import sys
import time

import waitress

import audit
import config
import detector
from app import app

THREADS = int(os.getenv("AI201_THREADS", "4"))


def main():
    t0 = time.perf_counter()
    try:
        detector.warm_up()
    except detector.DetectorUnavailable as exc:
        audit.log_event("startup_failed", reason="detector_unavailable", detail=str(exc)[:200])
        print(f"Could not load {config.DETECTOR_MODEL}: {exc}\nRun `python detector.py` once to download it.")
        sys.exit(1)
    load_s = round(time.perf_counter() - t0, 2)

    audit.log_event(
        "startup",
        model=config.DETECTOR_MODEL,
        model_load_s=load_s,
        host=config.HOST,
        port=config.PORT,
        threads=THREADS,
        python=platform.python_version(),
        rate_limiting=config.RATE_LIMITING_ENABLED,
    )
    print(f"Provenance Guard on http://{config.HOST}:{config.PORT}  "
          f"(model loaded in {load_s}s, {THREADS} threads, log: {config.AUDIT_LOG})", flush=True)
    waitress.serve(app, host=config.HOST, port=config.PORT, threads=THREADS, ident="provenance-guard")


if __name__ == "__main__":
    main()
