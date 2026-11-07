# Scorecard: nemotron-3.5-lightning

`nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-BF16` · NVIDIA · size class: **small**

Scored under **GMI Open Model Standard v1.0**.

## Tier: Not verified

Not met for the next tier:
- did not complete all applicable task sets
- error rate 100.0% >= 2%

Best for: not enough data yet.

## 1. Capability

| Suite | Role | Status | Runs | Pass rate | Consistency |
|---|---|---|---|---|---|
| Coding | core | incomplete | 11/60 | 0.0% | 0.0% |
| Tool use | core | not run | 0/60 | –% | –% |
| Documents | core | not run | 0/60 | –% | –% |
| Coding (hard) | stress | incomplete | 11/60 | 0.0% | 0.0% |
| **All core suites (tier)** | | | 11 | **0.0%** | 0.0% |
| **Stress: all stress suites** | | | 11 | **0.0%** | 0.0% |

The tier uses the core suites only. Stress suites are a separate score; experimental suites are shown but never count.

## 2. Efficiency

- Median output speed: – tokens/s
- Median time to first token: – s
- Quality per active parameter: 0.00 pass-rate points per active B (active params: 3B)

## 3. Agent reliability

- Tool-call accuracy: –%
- Mean API retries per task: 3.00
- Consistency (tasks passed in every run): 0.0%
- Error rate (runs that failed after retries): 100.00%
- Truncated runs (hit max_tokens before finishing): 0
- Empty answers (finished, but no visible text; e.g. the answer went to the reasoning channel): 0

## 4. Unit economics

Prices: $0.15 in / $1 out per 1M tokens.

| Task set | Prompt tokens | Completion tokens | Cost | Cost per successful task |
|---|---|---|---|---|
| Coding | 0 | 0 | $0.00000 | – |
| Coding (hard) | 0 | 0 | $0.00000 | – |
| **All core sets** | 0 | 0 | $0.00000 | **–** |

## 5. Deployability

| Check | Result |
|---|---|
| License is OSI-approved or OpenMDW (openmdw-1.1) | pass |
| Served context ≥ 128k (65,536 tokens) | fail |
| Served precision documented (BF16) | pass |
| Weights downloadable | pass |
