# Scorecard: deepseek-v4-flash

`deepseek-ai/DeepSeek-V4-Flash` · DeepSeek · size class: **large**

## Tier: GMI Verified

Not met for the next tier:
- TTFT median 1.69s > 1.5s

Best for: tool use (100.0% pass rate, $0.00026 per successful task).

## 1. Capability

| Task set | Status | Runs | Pass rate | Consistency |
|---|---|---|---|---|
| Coding | ok | 60/60 | 81.7% | 70.0% |
| Tool use | ok | 60/60 | 100.0% | 100.0% |
| Documents | n/a (no vision) | – | – | – |
| Coding (hard) | ok | 60/60 | 63.3% | 45.0% |
| Tool use (hard) | ok | 60/60 | 100.0% | 100.0% |
| Documents (hard) | n/a (no vision) | – | – | – |
| **All core sets (tier)** | | 120 | **90.8%** | 85.0% |
| **Stress: all hard sets** | | 120 | **81.7%** | 72.5% |

The tier uses the core sets only. The hard sets are a separate stress score.

## 2. Efficiency

- Median output speed: 203.7 tokens/s
- Median time to first token: 1.69 s
- Quality per active parameter: – pass-rate points per active B (active params: unknown)

## 3. Agent reliability

- Tool-call accuracy: 100.0%
- Mean API retries per task: 0.00
- Consistency (tasks passed in every run): 85.0%
- Error rate (runs that failed after retries): 0.00%
- Truncated runs (hit max_tokens before finishing): 11
- Empty answers (finished, but no visible text; e.g. the answer went to the reasoning channel): 0

## 4. Unit economics

Prices: $0.14 in / $0.28 out per 1M tokens.

| Task set | Prompt tokens | Completion tokens | Cost | Cost per successful task |
|---|---|---|---|---|
| Coding | 10,818 | 242,080 | $0.0693 | $0.00141 |
| Tool use | 94,489 | 8,207 | $0.0155 | $0.00026 |
| Coding (hard) | 12,591 | 1,339,593 | $0.3768 | $0.00992 |
| Tool use (hard) | 1,010,257 | 111,747 | $0.1727 | $0.00288 |
| **All core sets** | 105,307 | 250,287 | $0.0848 | **$0.00078** |

## 5. Deployability

| Check | Result |
|---|---|
| License is OSI-approved or OpenMDW (mit) | pass |
| Served context ≥ 128k (1,048,575 tokens) | pass |
| Served precision documented (FP8) | pass |
| Weights downloadable | pass |
