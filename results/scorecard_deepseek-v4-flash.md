# Scorecard: deepseek-v4-flash

`deepseek-ai/DeepSeek-V4-Flash` · DeepSeek · size class: **large**

Scored under **GMI Open Model Standard v1.0**.

## Tier: Best value in class

Lowest cost per successful task among large models that meet the production bar, at GMI list prices, for: Coding.

Best for: tool use (98.3% pass rate, $0.00025 per successful task).

## 1. Capability

| Suite | Role | Status | Runs | Pass rate | Consistency |
|---|---|---|---|---|---|
| Coding | core | ok | 60/60 | 96.7% | 95.0% |
| Tool use | core | ok | 60/60 | 98.3% | 95.0% |
| Documents | core | n/a (no vision) | – | – | – |
| Coding (hard) | stress | ok | 60/60 | 63.3% | 45.0% |
| Tool use (hard) | stress | ok | 60/60 | 100.0% | 100.0% |
| Documents (hard) | stress | n/a (no vision) | – | – | – |
| **All core suites (tier)** | | | 120 | **97.5%** | 95.0% |
| **Stress: all stress suites** | | | 120 | **81.7%** | 72.5% |

The tier uses the core suites only. Stress suites are a separate score; experimental suites are shown but never count.

## 2. Efficiency

- Median output speed: 402.1 tokens/s
- Median time to first token: 0.49 s (one client location, San Jose; see the README limits)
- Quality per active parameter: 7.50 pass-rate points per active B (active params: 13B)

## 3. Agent reliability

- Tool-call accuracy: 98.3%
- Mean API retries per task: 0.00
- Consistency (tasks passed in every run): 95.0%
- Error rate (runs that failed after retries): 0.00%
- Truncated runs (hit max_tokens before finishing): 2
- Empty answers (finished, but no visible text; e.g. the answer went to the reasoning channel): 0

### Platform notes

Serving-side events, shown so they are not mistaken for model quality (all suites):

- API errors that were retried and then succeeded: 0 (not in the error rate above, which counts final attempts)
- Runs that fell back to a non-streamed call: 0
- Answers with unparsed tool-call text: 0
- Runs cut off at the output-token limit (counted as failures): 24

## 4. Unit economics

Prices: $0.14 in / $0.28 out per 1M tokens (GMI list prices at run time; no cache or account discounts).

| Task set | Prompt tokens | Completion tokens | Cost | Cost per successful task |
|---|---|---|---|---|
| Coding | 11,055 | 112,640 | $0.0331 | $0.00057 |
| Tool use | 86,934 | 9,359 | $0.0148 | $0.00025 |
| Coding (hard) | 12,591 | 1,339,593 | $0.3768 | $0.00992 |
| Tool use (hard) | 1,010,257 | 111,747 | $0.1727 | $0.00288 |
| **All core sets** | 97,989 | 121,999 | $0.0479 | **$0.00041** |

## 5. Deployability

| Check | Result |
|---|---|
| License id on our allowlist: OSI-approved or OpenMDW (mit) | pass |
| Served context ≥ 128k (1,048,575 tokens) | pass |
| Served precision documented (FP8) | pass |
| Weights downloadable | pass |
