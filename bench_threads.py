"""
Diagnosis tool for capstone criterion C4: how does torch's thread count change
the wall time and the CPU time of one GPT-2 scoring call?

    python bench_threads.py            # tries 1, 2, 4, 8 and torch's default

Scores the same 15 texts the capstone test uses, one at a time, after one
warm-up call, and prints mean wall ms and mean CPU ms per text.
"""

import statistics
import sys
import time

import torch

import detector
from scenarios import SCENARIOS

TEXTS = SCENARIOS[0]["texts"] + SCENARIOS[1]["texts"][:5]


def run(threads):
    torch.set_num_threads(threads)
    detector.model_signal(TEXTS[0])  # warm-up, not counted
    walls, cpus = [], []
    for text in TEXTS:
        w0, c0 = time.perf_counter(), time.process_time()
        detector.model_signal(text)
        walls.append((time.perf_counter() - w0) * 1000)
        cpus.append((time.process_time() - c0) * 1000)
    return statistics.mean(walls), max(walls), statistics.mean(cpus)


def main():
    default = torch.get_num_threads()
    counts = [int(a) for a in sys.argv[1:]] or [1, 2, 4, 8, default]
    detector.warm_up()
    print(f"torch default threads: {default}")
    print("threads  mean wall ms  max wall ms  mean CPU ms  CPU/wall")
    for n in counts:
        wall, worst, cpu = run(n)
        print(f"{n:7d}  {wall:12.1f}  {worst:11.1f}  {cpu:11.1f}  {cpu / wall:8.1f}")


if __name__ == "__main__":
    main()
