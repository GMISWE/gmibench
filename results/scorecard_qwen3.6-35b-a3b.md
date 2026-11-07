# Scorecard: qwen3.6-35b-a3b

`Qwen/Qwen3.6-35B-A3B` · Alibaba Qwen · size class: **small**

Scored under **GMI Open Model Standard v1.0**.

## Tier: Best value in class

Lowest cost per successful task among small models that meet the production bar, at GMI list prices, for: Documents (uncontested: no other small model met the bar here).

Best for: tool use (100.0% pass rate, $0.00076 per successful task).

## 1. Capability

| Suite | Role | Status | Runs | Pass rate | Consistency |
|---|---|---|---|---|---|
| Coding | core | ok | 60/60 | 96.7% | 90.0% |
| Tool use | core | ok | 60/60 | 100.0% | 100.0% |
| Documents | core | ok | 60/60 | 100.0% | 100.0% |
| Coding (hard) | stress | ok | 60/60 | 88.3% | 70.0% |
| Tool use (hard) | stress | ok | 60/60 | 98.3% | 95.0% |
| Documents (hard) | stress | ok | 60/60 | 100.0% | 100.0% |
| **All core suites (tier)** | | | 180 | **98.9%** | 96.7% |
| **Stress: all stress suites** | | | 180 | **95.6%** | 88.3% |

The tier uses the core suites only. Stress suites are a separate score; experimental suites are shown but never count.

## 2. Efficiency

- Median output speed: 130.9 tokens/s
- Median time to first token: 0.99 s (one client location, San Jose; see the README limits)
- Quality per active parameter: 32.96 pass-rate points per active B (active params: 3B)

## 3. Agent reliability

- Tool-call accuracy: 100.0%
- Mean API retries per task: 0.00
- Consistency (tasks passed in every run): 96.7%
- Error rate (runs that failed after retries): 0.00%
- Truncated runs (hit max_tokens before finishing): 1
- Empty answers (finished, but no visible text; e.g. the answer went to the reasoning channel): 0

### Platform notes

Serving-side events, shown so they are not mistaken for model quality (all suites):

- API errors that were retried and then succeeded: 0 (not in the error rate above, which counts final attempts)
- Runs that fell back to a non-streamed call: 0
- Answers with unparsed tool-call text: 0
- Runs cut off at the output-token limit (counted as failures): 1

## 4. Unit economics

Prices: $0.248 in / $1.485 out per 1M tokens (GMI list prices at run time; no cache or account discounts).

| Task set | Prompt tokens | Completion tokens | Cost | Cost per successful task |
|---|---|---|---|---|
| Coding | 6,780 | 635,884 | $0.9460 | $0.0163 |
| Tool use | 85,776 | 16,558 | $0.0459 | $0.00076 |
| Documents | 53,379 | 24,052 | $0.0490 | $0.00082 |
| Coding (hard) | 8,448 | 1,347,359 | $2.0029 | $0.0378 |
| Tool use (hard) | 977,656 | 92,019 | $0.3791 | $0.00643 |
| Documents (hard) | 55,479 | 39,449 | $0.0723 | $0.00121 |
| **All core sets** | 145,935 | 676,494 | $1.0408 | **$0.00585** |

## 5. Deployability

| Check | Result |
|---|---|
| License id on our allowlist: OSI-approved or OpenMDW (apache-2.0) | pass |
| Served context ≥ 128k (262,144 tokens) | pass |
| Served precision documented (FP8) | pass |
| Weights downloadable | pass |
