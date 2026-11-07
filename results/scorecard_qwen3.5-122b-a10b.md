# Scorecard: qwen3.5-122b-a10b

`Qwen/Qwen3.5-122B-A10B` · Alibaba Qwen · size class: **mid**

## Tier: GMI Recommended

Recommended for: Coding, Tool use, Documents (mid models).

Best for: documents (100.0% pass rate, $0.00101 per successful task).

## 1. Capability

| Task set | Status | Runs | Pass rate | Consistency |
|---|---|---|---|---|
| Coding | ok | 60/60 | 98.3% | 95.0% |
| Tool use | ok | 60/60 | 100.0% | 100.0% |
| Documents | ok | 60/60 | 100.0% | 100.0% |
| Coding (hard) | ok | 60/60 | 85.0% | 65.0% |
| Tool use (hard) | ok | 60/60 | 86.7% | 80.0% |
| Documents (hard) | ok | 60/60 | 100.0% | 100.0% |
| **All core sets (tier)** | | 180 | **99.4%** | 98.3% |
| **Stress: all hard sets** | | 180 | **90.6%** | 81.7% |

The tier uses the core sets only. The hard sets are a separate stress score.

## 2. Efficiency

- Median output speed: 159.7 tokens/s
- Median time to first token: 1.09 s
- Quality per active parameter: 9.94 pass-rate points per active B (active params: 10B)

## 3. Agent reliability

- Tool-call accuracy: 100.0%
- Mean API retries per task: 0.00
- Consistency (tasks passed in every run): 98.3%
- Error rate (runs that failed after retries): 0.00%
- Truncated runs (hit max_tokens before finishing): 0
- Empty answers (finished, but no visible text; e.g. the answer went to the reasoning channel): 0

## 4. Unit economics

Prices: $0.4 in / $3.2 out per 1M tokens.

| Task set | Prompt tokens | Completion tokens | Cost | Cost per successful task |
|---|---|---|---|---|
| Coding | 6,780 | 420,719 | $1.3490 | $0.0229 |
| Tool use | 86,625 | 10,107 | $0.0670 | $0.00112 |
| Documents | 53,499 | 12,205 | $0.0605 | $0.00101 |
| Coding (hard) | 8,448 | 713,647 | $2.2870 | $0.0448 |
| Tool use (hard) | 1,411,922 | 67,433 | $0.7806 | $0.0150 |
| Documents (hard) | 55,599 | 20,515 | $0.0879 | $0.00146 |
| **All core sets** | 146,904 | 443,031 | $1.4765 | **$0.00825** |

## 5. Deployability

| Check | Result |
|---|---|
| License is OSI-approved or OpenMDW (apache-2.0) | pass |
| Served context ≥ 128k (262,144 tokens) | pass |
| Served precision documented (FP8) | pass |
| Weights downloadable | pass |
