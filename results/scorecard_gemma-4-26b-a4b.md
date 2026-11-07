# Scorecard: gemma-4-26b-a4b

`google/gemma-4-26b-a4b-it` · Google · size class: **small**

## Tier: GMI Recommended

Recommended for: Coding, Tool use (small models).

Best for: coding (100.0% pass rate, $0.00012 per successful task).

## 1. Capability

| Task set | Status | Runs | Pass rate | Consistency |
|---|---|---|---|---|
| Coding | ok | 60/60 | 100.0% | 100.0% |
| Tool use | ok | 60/60 | 100.0% | 100.0% |
| Documents | n/a (no vision) | – | – | – |
| Coding (hard) | ok | 60/60 | 93.3% | 90.0% |
| Tool use (hard) | ok | 60/60 | 88.3% | 80.0% |
| Documents (hard) | n/a (no vision) | – | – | – |
| **All core sets (tier)** | | 120 | **100.0%** | 100.0% |
| **Stress: all hard sets** | | 120 | **90.8%** | 85.0% |

The tier uses the core sets only. The hard sets are a separate stress score.

## 2. Efficiency

- Median output speed: 95.4 tokens/s
- Median time to first token: 0.52 s
- Note: 60 runs could not stream (the endpoint returned an empty stream with tools), so they ran without streaming and have no TTFT or speed measurement.
- Quality per active parameter: 25.00 pass-rate points per active B (active params: 4B)

## 3. Agent reliability

- Tool-call accuracy: 100.0%
- Mean API retries per task: 0.07
- Consistency (tasks passed in every run): 100.0%
- Error rate (runs that failed after retries): 0.00%
- Truncated runs (hit max_tokens before finishing): 0
- Empty answers (finished, but no visible text; e.g. the answer went to the reasoning channel): 0

## 4. Unit economics

Prices: $0.13 in / $0.4 out per 1M tokens.

| Task set | Prompt tokens | Completion tokens | Cost | Cost per successful task |
|---|---|---|---|---|
| Coding | 7,146 | 15,068 | $0.00696 | $0.00012 |
| Tool use | 53,073 | 3,286 | $0.00821 | $0.00014 |
| Coding (hard) | 8,811 | 48,581 | $0.0206 | $0.00037 |
| Tool use (hard) | 1,105,577 | 22,923 | $0.1529 | $0.00288 |
| **All core sets** | 60,219 | 18,354 | $0.0152 | **$0.00013** |

## 5. Deployability

| Check | Result |
|---|---|
| License is OSI-approved or OpenMDW (apache-2.0) | pass |
| Served context ≥ 128k (256,000 tokens) | pass |
| Served precision documented (FP8) | pass |
| Weights downloadable | pass |
