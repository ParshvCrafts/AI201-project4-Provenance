# Capstone run: after3_pcores (2026-11-13_2335)

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Cold start under 30 s | 3 of 3 | 14.31s | 13.36s | 13.84s | MET |
| 2. Every request leaves one complete log line | 28 of 28, every trial | 28/28 | 28/28 | 28/28 | MET |
| 3. Accepted submissions under 1,000 ms | 14 of 15, every trial | 15/15 | 15/15 | 15/15 | MET |
| 4. Mean CPU per accepted submission | at most 1,000 ms, every trial | 1350 ms | 1338 ms | 1332 ms | MISSED |
| 5. Human texts labelled AI | 0 of 10, every trial | 0/10 | 0/10 | 0/10 | MET |

| Trial | p50 ms | p95 ms | max ms | GPT-2 ms | style ms | scoring ms | client ms | model load s |
|---|---|---|---|---|---|---|---|---|
| 1 | 254.0 | 387.8 | 387.8 | 268.1 | 0.9 | 0.0 | 278.0 | 13.06 |
| 2 | 261.3 | 376.0 | 376.0 | 270.5 | 0.9 | 0.0 | 279.5 | 12.31 |
| 3 | 261.2 | 393.6 | 393.6 | 271.7 | 0.9 | 0.0 | 282.5 | 12.49 |

Status codes, in send order:

- trial 1: 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 400 400 400 413 413 404 400 400 400 400 400 429
- trial 2: 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 400 400 400 413 413 404 400 400 400 400 400 429
- trial 3: 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 400 400 400 413 413 404 400 400 400 400 400 429
