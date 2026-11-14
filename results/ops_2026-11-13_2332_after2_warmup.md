# Capstone run: after2_warmup (2026-11-13_2332)

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Cold start under 30 s | 3 of 3 | 8.89s | 8.9s | 24.42s | MET |
| 2. Every request leaves one complete log line | 28 of 28, every trial | 28/28 | 28/28 | 28/28 | MET |
| 3. Accepted submissions under 1,000 ms | 14 of 15, every trial | 15/15 | 14/15 | 15/15 | MET |
| 4. Mean CPU per accepted submission | at most 1,000 ms, every trial | 850 ms | 4119 ms | 3903 ms | MISSED |
| 5. Human texts labelled AI | 0 of 10, every trial | 0/10 | 0/10 | 0/10 | MET |

| Trial | p50 ms | p95 ms | max ms | GPT-2 ms | style ms | scoring ms | client ms | model load s |
|---|---|---|---|---|---|---|---|---|
| 1 | 164.4 | 240.6 | 240.6 | 178.0 | 0.4 | 0.0 | 182.3 | 8.07 |
| 2 | 631.6 | 1008.9 | 1008.9 | 671.0 | 1.6 | 0.0 | 684.0 | 7.79 |
| 3 | 698.7 | 977.8 | 977.8 | 713.8 | 1.5 | 0.0 | 727.4 | 22.3 |

Status codes, in send order:

- trial 1: 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 400 400 400 413 413 404 400 400 400 400 400 429
- trial 2: 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 400 400 400 413 413 404 400 400 400 400 400 429
- trial 3: 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 400 400 400 413 413 404 400 400 400 400 400 429
