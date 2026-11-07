# Scorecard: glm-5.3-flash

`zai-org/GLM-5.3-Flash` · Zhipu AI (Z.ai) · size class: **large**

Scored under **GMI Open Model Standard v1.0**.

## Tier: Best value in class

Lowest cost per successful task among large models that meet the production bar, at GMI list prices, for: Documents (uncontested: no other large model met the bar here); Tool use.

Best for: tool use (100.0% pass rate, $0.00022 per successful task).

## 1. Capability

| Suite | Role | Status | Runs | Pass rate | Consistency |
|---|---|---|---|---|---|
| Coding | core | ok | 60/60 | 91.7% | 85.0% |
| Tool use | core | ok | 60/60 | 100.0% | 100.0% |
| Documents | core | ok | 60/60 | 100.0% | 100.0% |
| Coding (hard) | stress | ok | 60/60 | 83.3% | 75.0% |
| Tool use (hard) | stress | ok | 60/60 | 85.0% | 85.0% |
| Documents (hard) | stress | ok | 60/60 | 100.0% | 100.0% |
| **All core suites (tier)** | | | 180 | **97.2%** | 95.0% |
| **Stress: all stress suites** | | | 180 | **89.4%** | 86.7% |

The tier uses the core suites only. Stress suites are a separate score; experimental suites are shown but never count.

## 2. Efficiency

- Median output speed: 95.1 tokens/s
- Median time to first token: 0.60 s (one client location, San Jose; see the README limits)
- Note: 4 core runs did not stream, so they have no TTFT or speed measurement; the median uses the other runs.
- Quality per active parameter: 5.40 pass-rate points per active B (active params: 18B)

## 3. Agent reliability

- Tool-call accuracy: 100.0%
- Mean API retries per task: 0.13
- Consistency (tasks passed in every run): 95.0%
- Error rate (runs that failed after retries): 0.00%
- Truncated runs (hit max_tokens before finishing): 5
- Empty answers (finished, but no visible text; e.g. the answer went to the reasoning channel): 0

### Platform notes

Serving-side events, shown so they are not mistaken for model quality (all suites):

- API errors that were retried and then succeeded: 53 (not in the error rate above, which counts final attempts)
- Runs that fell back to a non-streamed call: 12
- Answers with unparsed tool-call text: 0
- Runs cut off at the output-token limit (counted as failures): 14

## 4. Unit economics

Prices: $0.15 in / $0.5 out per 1M tokens (GMI list prices at run time; no cache or account discounts).

| Task set | Prompt tokens | Completion tokens | Cost | Cost per successful task |
|---|---|---|---|---|
| Coding | 6,723 | 229,319 | $0.1157 | $0.00210 |
| Tool use | 63,326 | 7,110 | $0.0131 | $0.00022 |
| Documents | 68,421 | 18,421 | $0.0195 | $0.00032 |
| Coding (hard) | 8,241 | 650,751 | $0.3266 | $0.00653 |
| Tool use (hard) | 641,912 | 40,869 | $0.1167 | $0.00229 |
| Documents (hard) | 71,346 | 28,910 | $0.0252 | $0.00042 |
| **All core sets** | 138,470 | 254,850 | $0.1482 | **$0.00085** |

## 5. Deployability

| Check | Result |
|---|---|
| License id on our allowlist: OSI-approved or OpenMDW (mit) | pass |
| Served context ≥ 128k (1,048,576 tokens) | pass |
| Served precision documented (FP8) | pass |
| Weights downloadable | pass |
