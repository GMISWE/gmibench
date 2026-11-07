# Scorecard: gpt-oss-120b

`openai/gpt-oss-120b` · OpenAI · size class: **mid**

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
| Documents | n/a (no vision) | – | – | – |
| Coding (hard) | incomplete | 11/60 | 0.0% | 0.0% |
| Documents (hard) | n/a (no vision) | – | – | – |
| **All core sets (tier)** | | 11 | **0.0%** | 0.0% |
| **Stress: all hard sets** | | 11 | **0.0%** | 0.0% |

The tier uses the core sets only. The hard sets are a separate stress score.

## 2. Efficiency

- Median output speed: – tokens/s
- Median time to first token: – s
- Quality per active parameter: 0.00 pass-rate points per active B (active params: 5.1B)

## 3. Agent reliability

- Tool-call accuracy: –%
- Mean API retries per task: 3.00
- Consistency (tasks passed in every run): 0.0%
- Error rate (runs that failed after retries): 100.00%
- Truncated runs (hit max_tokens before finishing): 0
- Empty answers (finished, but no visible text; e.g. the answer went to the reasoning channel): 0

## 4. Unit economics

Prices: $0.05 in / $0.25 out per 1M tokens.

| Task set | Prompt tokens | Completion tokens | Cost | Cost per successful task |
|---|---|---|---|---|
| Coding | 0 | 0 | $0.00000 | – |
| Coding (hard) | 0 | 0 | $0.00000 | – |
| **All core sets** | 0 | 0 | $0.00000 | **–** |

## 5. Deployability

| Check | Result |
|---|---|
| License is OSI-approved or OpenMDW (apache-2.0) | pass |
| Served context ≥ 128k (131,072 tokens) | pass |
| Served precision documented (FP8) | pass |
| Weights downloadable | pass |
