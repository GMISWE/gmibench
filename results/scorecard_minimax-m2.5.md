# Scorecard: minimax-m2.5

`MiniMaxAI/MiniMax-M2.5` · MiniMax · size class: **large**

Scored under **GMI Open Model Standard v1.0**.

## Tier: Meets production bar

Not met for the next tier:
- not the lowest cost per successful task in any workload for its size class

Best for: tool use (100.0% pass rate, $0.00052 per successful task).

## 1. Capability

| Suite | Role | Status | Runs | Pass rate | Consistency |
|---|---|---|---|---|---|
| Coding | core | ok | 60/60 | 91.7% | 80.0% |
| Tool use | core | ok | 60/60 | 100.0% | 100.0% |
| Documents | core | n/a (no vision) | – | – | – |
| Coding (hard) | stress | ok | 60/60 | 71.7% | 60.0% |
| Tool use (hard) | stress | ok | 60/60 | 88.3% | 70.0% |
| Documents (hard) | stress | n/a (no vision) | – | – | – |
| **All core suites (tier)** | | | 120 | **95.8%** | 90.0% |
| **Stress: all stress suites** | | | 120 | **80.0%** | 65.0% |

The tier uses the core suites only. Stress suites are a separate score; experimental suites are shown but never count.

## 2. Efficiency

- Median output speed: 73.0 tokens/s
- Median time to first token: 0.93 s (one client location, San Jose; see the README limits)
- Quality per active parameter: 9.58 pass-rate points per active B (active params: 10B)

## 3. Agent reliability

- Tool-call accuracy: 100.0%
- Mean API retries per task: 0.00
- Consistency (tasks passed in every run): 90.0%
- Error rate (runs that failed after retries): 0.00%
- Truncated runs (hit max_tokens before finishing): 3
- Empty answers (finished, but no visible text; e.g. the answer went to the reasoning channel): 0

### Platform notes

Serving-side events, shown so they are not mistaken for model quality (all suites):

- API errors that were retried and then succeeded: 0 (not in the error rate above, which counts final attempts)
- Runs that fell back to a non-streamed call: 0
- Answers with unparsed tool-call text: 0
- Runs cut off at the output-token limit (counted as failures): 16

## 4. Unit economics

Prices: $0.3 in / $1.2 out per 1M tokens (GMI list prices at run time; no cache or account discounts).

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
| License id on our allowlist: OSI-approved or OpenMDW (modified-mit) | fail |
| Served context ≥ 128k (196,608 tokens) | pass |
| Served precision documented (FP8) | pass |
| Weights downloadable | pass |
