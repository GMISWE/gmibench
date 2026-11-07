# Scorecard: minimax-m2.5

`MiniMaxAI/MiniMax-M2.5` · MiniMax · size class: **large**

## Tier: GMI Production Ready

Not met for the next tier:
- not the lowest cost per successful task in any workload for its size class

Best for: tool use (100.0% pass rate, $0.00052 per successful task).

## 1. Capability

| Task set | Status | Runs | Pass rate | Consistency |
|---|---|---|---|---|
| Coding | ok | 60/60 | 91.7% | 80.0% |
| Tool use | ok | 60/60 | 100.0% | 100.0% |
| Documents | n/a (no vision) | – | – | – |
| Coding (hard) | ok | 60/60 | 71.7% | 60.0% |
| Tool use (hard) | ok | 60/60 | 88.3% | 70.0% |
| Documents (hard) | n/a (no vision) | – | – | – |
| **All core sets (tier)** | | 120 | **95.8%** | 90.0% |
| **Stress: all hard sets** | | 120 | **80.0%** | 65.0% |

The tier uses the core sets only. The hard sets are a separate stress score.

## 2. Efficiency

- Median output speed: 73.0 tokens/s
- Median time to first token: 0.93 s
- Quality per active parameter: 9.58 pass-rate points per active B (active params: 10B)

## 3. Agent reliability

- Tool-call accuracy: 100.0%
- Mean API retries per task: 0.00
- Consistency (tasks passed in every run): 90.0%
- Error rate (runs that failed after retries): 0.00%
- Truncated runs (hit max_tokens before finishing): 3
- Empty answers (finished, but no visible text; e.g. the answer went to the reasoning channel): 0

## 4. Unit economics

Prices: $0.3 in / $1.2 out per 1M tokens.

| Task set | Prompt tokens | Completion tokens | Cost | Cost per successful task |
|---|---|---|---|---|
| Coding | 8,583 | 147,889 | $0.1800 | $0.00327 |
| Tool use | 67,343 | 9,234 | $0.0313 | $0.00052 |
| Coding (hard) | 10,113 | 805,110 | $0.9692 | $0.0225 |
| Tool use (hard) | 657,700 | 70,788 | $0.2823 | $0.00533 |
| **All core sets** | 75,926 | 157,123 | $0.2113 | **$0.00184** |

## 5. Deployability

| Check | Result |
|---|---|
| License is OSI-approved or OpenMDW (modified-mit) | fail |
| Served context ≥ 128k (196,608 tokens) | pass |
| Served precision documented (FP8) | pass |
| Weights downloadable | pass |
