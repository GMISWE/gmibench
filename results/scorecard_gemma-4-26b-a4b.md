# Scorecard: gemma-4-26b-a4b

`google/gemma-4-26b-a4b-it` · Google · size class: **small**

Scored under **GMI Open Model Standard v1.0**.

## Tier: Best value in class

Lowest cost per successful task among small models that meet the production bar, at GMI list prices, for: Coding; Tool use.

Best for: tool use (100.0% pass rate, $0.00014 per successful task).

## 1. Capability

| Suite | Role | Status | Runs | Pass rate | Consistency |
|---|---|---|---|---|---|
| Coding | core | ok | 60/60 | 98.3% | 95.0% |
| Tool use | core | ok | 60/60 | 100.0% | 100.0% |
| Documents | core | n/a (no vision) | – | – | – |
| Coding (hard) | stress | ok | 60/60 | 93.3% | 90.0% |
| Tool use (hard) | stress | ok | 60/60 | 88.3% | 80.0% |
| Documents (hard) | stress | n/a (no vision) | – | – | – |
| **All core suites (tier)** | | | 120 | **99.2%** | 97.5% |
| **Stress: all stress suites** | | | 120 | **90.8%** | 85.0% |

The tier uses the core suites only. Stress suites are a separate score; experimental suites are shown but never count.

## 2. Efficiency

- Median output speed: 202.6 tokens/s
- Median time to first token: 0.53 s (one client location, San Jose; see the README limits)
- Note: 60 core runs did not stream, so they have no TTFT or speed measurement; the median uses the other runs.
- Quality per active parameter: 26.10 pass-rate points per active B (active params: 3.8B)

## 3. Agent reliability

- Tool-call accuracy: 100.0%
- Mean API retries per task: 0.20
- Consistency (tasks passed in every run): 97.5%
- Error rate (runs that failed after retries): 0.00%
- Truncated runs (hit max_tokens before finishing): 0
- Empty answers (finished, but no visible text; e.g. the answer went to the reasoning channel): 0

### Platform notes

Serving-side events, shown so they are not mistaken for model quality (all suites):

- API errors that were retried and then succeeded: 0 (not in the error rate above, which counts final attempts)
- Runs that fell back to a non-streamed call: 120
- Answers with unparsed tool-call text: 1
- Runs cut off at the output-token limit (counted as failures): 0

## 4. Unit economics

Prices: $0.13 in / $0.4 out per 1M tokens (GMI list prices at run time; no cache or account discounts).

| Task set | Prompt tokens | Completion tokens | Cost | Cost per successful task |
|---|---|---|---|---|
| Coding | 7,146 | 15,327 | $0.00706 | $0.00012 |
| Tool use | 54,677 | 3,342 | $0.00844 | $0.00014 |
| Coding (hard) | 8,811 | 48,581 | $0.0206 | $0.00037 |
| Tool use (hard) | 1,105,577 | 22,923 | $0.1529 | $0.00288 |
| **All core sets** | 61,823 | 18,669 | $0.0155 | **$0.00013** |

## 5. Deployability

| Check | Result |
|---|---|
| License id on our allowlist: OSI-approved or OpenMDW (apache-2.0) | pass |
| Served context ≥ 128k (256,000 tokens) | pass |
| Served precision documented (FP8) | pass |
| Weights downloadable | pass |
