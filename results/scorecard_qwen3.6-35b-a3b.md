# Scorecard: qwen3.6-35b-a3b

`Qwen/Qwen3.6-35B-A3B` · Alibaba Qwen · size class: **small**

Scored under **GMI Open Model Standard v1.0**.

## Tier: GMI Recommended

Recommended for: Documents (small models).

Best for: tool use (100.0% pass rate, $0.00079 per successful task).

## 1. Capability

| Suite | Role | Status | Runs | Pass rate | Consistency |
|---|---|---|---|---|---|
| Coding | core | ok | 60/60 | 91.7% | 80.0% |
| Tool use | core | ok | 60/60 | 100.0% | 100.0% |
| Documents | core | ok | 60/60 | 100.0% | 100.0% |
| Coding (hard) | stress | ok | 60/60 | 88.3% | 70.0% |
| Tool use (hard) | stress | ok | 60/60 | 98.3% | 95.0% |
| Documents (hard) | stress | ok | 60/60 | 100.0% | 100.0% |
| **All core suites (tier)** | | | 180 | **97.2%** | 93.3% |
| **Stress: all stress suites** | | | 180 | **95.6%** | 88.3% |

The tier uses the core suites only. Stress suites are a separate score; experimental suites are shown but never count.

## 2. Efficiency

- Median output speed: 136.1 tokens/s
- Median time to first token: 0.90 s
- Quality per active parameter: 32.41 pass-rate points per active B (active params: 3B)

## 3. Agent reliability

- Tool-call accuracy: 100.0%
- Mean API retries per task: 0.00
- Consistency (tasks passed in every run): 93.3%
- Error rate (runs that failed after retries): 0.00%
- Truncated runs (hit max_tokens before finishing): 3
- Empty answers (finished, but no visible text; e.g. the answer went to the reasoning channel): 0

## 4. Unit economics

Prices: $0.248 in / $1.485 out per 1M tokens.

| Task set | Prompt tokens | Completion tokens | Cost | Cost per successful task |
|---|---|---|---|---|
| Coding | 6,780 | 806,524 | $1.1994 | $0.0218 |
| Tool use | 86,222 | 17,325 | $0.0471 | $0.00079 |
| Documents | 53,379 | 23,972 | $0.0488 | $0.00081 |
| Coding (hard) | 8,448 | 1,347,359 | $2.0029 | $0.0378 |
| Tool use (hard) | 977,656 | 92,019 | $0.3791 | $0.00643 |
| Documents (hard) | 55,479 | 39,449 | $0.0723 | $0.00121 |
| **All core sets** | 146,381 | 847,821 | $1.2953 | **$0.00740** |

## 5. Deployability

| Check | Result |
|---|---|
| License is OSI-approved or OpenMDW (apache-2.0) | pass |
| Served context ≥ 128k (262,144 tokens) | pass |
| Served precision documented (FP8) | pass |
| Weights downloadable | pass |
