# Scorecard: nemotron-3.5-super-vl

`nvidia/NVIDIA-Nemotron-3.5-Super-VL-120B-A12B-BF16` · NVIDIA · size class: **mid**

## Tier: Not verified

Not met for the next tier:
- did not complete all applicable task sets
- error rate 100.0% >= 2%

Best for: not enough data yet.

## 1. Capability

| Task set | Status | Runs | Pass rate | Consistency |
|---|---|---|---|---|
| Coding | incomplete | 11/60 | 0.0% | 0.0% |
| Tool use | not run | 0/60 | –% | –% |
| Documents | not run | 0/60 | –% | –% |
| Coding (hard) | incomplete | 11/60 | 0.0% | 0.0% |
| **All core sets (tier)** | | 11 | **0.0%** | 0.0% |
| **Stress: all hard sets** | | 11 | **0.0%** | 0.0% |

The tier uses the core sets only. The hard sets are a separate stress score.

## 2. Efficiency

- Median output speed: – tokens/s
- Median time to first token: – s
- Quality per active parameter: 0.00 pass-rate points per active B (active params: 12B)

## 3. Agent reliability

- Tool-call accuracy: –%
- Mean API retries per task: 0.00
- Consistency (tasks passed in every run): 0.0%
- Error rate (runs that failed after retries): 100.00%
- Truncated runs (hit max_tokens before finishing): 0
- Empty answers (finished, but no visible text; e.g. the answer went to the reasoning channel): 0

## 4. Unit economics

Prices: $0.1 in / $0.5 out per 1M tokens.

| Task set | Prompt tokens | Completion tokens | Cost | Cost per successful task |
|---|---|---|---|---|
| Coding | 0 | 0 | $0.00000 | – |
| Coding (hard) | 0 | 0 | $0.00000 | – |
| **All core sets** | 0 | 0 | $0.00000 | **–** |

## 5. Deployability

| Check | Result |
|---|---|
| License is OSI-approved or OpenMDW (openmdw-1.1) | pass |
| Served context ≥ 128k (32,768 tokens) | fail |
| Served precision documented (BF16) | pass |
| Weights downloadable | pass |
