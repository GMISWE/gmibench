# Scorecard: qwen3.5-27b

`Qwen/Qwen3.5-27B` · Alibaba Qwen · size class: **small**

Scored under **GMI Open Model Standard v1.0**.

## Tier: GMI Verified

Not met for the next tier:
- consistency 76.7 < 80
- TTFT median 1.95s > 1.5s

Best for: tool use (98.3% pass rate, $0.00092 per successful task).

## 1. Capability

| Suite | Role | Status | Runs | Pass rate | Consistency |
|---|---|---|---|---|---|
| Coding | core | ok | 60/60 | 80.0% | 65.0% |
| Tool use | core | ok | 60/60 | 98.3% | 95.0% |
| Documents | core | ok | 60/60 | 85.0% | 70.0% |
| Coding (hard) | stress | ok | 60/60 | 65.0% | 55.0% |
| Tool use (hard) | stress | ok | 60/60 | 100.0% | 100.0% |
| Documents (hard) | stress | ok | 60/60 | 76.7% | 65.0% |
| **All core suites (tier)** | | | 180 | **87.8%** | 76.7% |
| **Stress: all stress suites** | | | 180 | **80.6%** | 73.3% |

The tier uses the core suites only. Stress suites are a separate score; experimental suites are shown but never count.

## 2. Efficiency

- Median output speed: 58.2 tokens/s
- Median time to first token: 1.95 s
- Quality per active parameter: 3.16 pass-rate points per active B (active params: 27.8B)

## 3. Agent reliability

- Tool-call accuracy: 100.0%
- Mean API retries per task: 0.00
- Consistency (tasks passed in every run): 76.7%
- Error rate (runs that failed after retries): 0.00%
- Truncated runs (hit max_tokens before finishing): 0
- Empty answers (finished, but no visible text; e.g. the answer went to the reasoning channel): 0

## 4. Unit economics

Prices: $0.3 in / $2.4 out per 1M tokens.

| Task set | Prompt tokens | Completion tokens | Cost | Cost per successful task |
|---|---|---|---|---|
| Coding | 6,780 | 288,166 | $0.6936 | $0.0145 |
| Tool use | 86,747 | 11,781 | $0.0543 | $0.00092 |
| Documents | 53,499 | 12,258 | $0.0455 | $0.00089 |
| Coding (hard) | 8,448 | 263,794 | $0.6356 | $0.0163 |
| Tool use (hard) | 1,474,273 | 58,103 | $0.5817 | $0.00970 |
| Documents (hard) | 55,599 | 20,701 | $0.0664 | $0.00144 |
| **All core sets** | 147,026 | 312,205 | $0.7934 | **$0.00502** |

## 5. Deployability

| Check | Result |
|---|---|
| License is OSI-approved or OpenMDW (apache-2.0) | pass |
| Served context ≥ 128k (262,144 tokens) | pass |
| Served precision documented (FP8) | pass |
| Weights downloadable | pass |
