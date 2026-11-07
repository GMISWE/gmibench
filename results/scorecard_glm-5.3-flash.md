# Scorecard: glm-5.3-flash

`zai-org/GLM-5.3-Flash` · Zhipu AI (Z.ai) · size class: **large**

Scored under **GMI Open Model Standard v1.0**.

## Tier: GMI Recommended

Recommended for: Coding, Documents, Tool use (large models).

Best for: tool use (100.0% pass rate, $0.00021 per successful task).

## 1. Capability

| Suite | Role | Status | Runs | Pass rate | Consistency |
|---|---|---|---|---|---|
| Coding | core | ok | 60/60 | 91.7% | 85.0% |
| Tool use | core | ok | 60/60 | 100.0% | 100.0% |
| Documents | core | ok | 60/60 | 98.3% | 95.0% |
| Coding (hard) | stress | ok | 60/60 | 83.3% | 75.0% |
| Tool use (hard) | stress | ok | 60/60 | 85.0% | 85.0% |
| Documents (hard) | stress | ok | 60/60 | 100.0% | 100.0% |
| **All core suites (tier)** | | | 180 | **96.7%** | 93.3% |
| **Stress: all stress suites** | | | 180 | **89.4%** | 86.7% |

The tier uses the core suites only. Stress suites are a separate score; experimental suites are shown but never count.

## 2. Efficiency

- Median output speed: 105.2 tokens/s
- Median time to first token: 0.64 s
- Quality per active parameter: – pass-rate points per active B (active params: unknown)

## 3. Agent reliability

- Tool-call accuracy: 100.0%
- Mean API retries per task: 0.05
- Consistency (tasks passed in every run): 93.3%
- Error rate (runs that failed after retries): 0.00%
- Truncated runs (hit max_tokens before finishing): 5
- Empty answers (finished, but no visible text; e.g. the answer went to the reasoning channel): 0

## 4. Unit economics

Prices: $0.15 in / $0.5 out per 1M tokens.

| Task set | Prompt tokens | Completion tokens | Cost | Cost per successful task |
|---|---|---|---|---|
| Coding | 6,723 | 245,645 | $0.1238 | $0.00225 |
| Tool use | 60,720 | 6,793 | $0.0125 | $0.00021 |
| Documents | 68,421 | 15,205 | $0.0179 | $0.00030 |
| Coding (hard) | 8,241 | 650,751 | $0.3266 | $0.00653 |
| Tool use (hard) | 641,912 | 40,869 | $0.1167 | $0.00229 |
| Documents (hard) | 71,346 | 28,910 | $0.0252 | $0.00042 |
| **All core sets** | 135,864 | 267,643 | $0.1542 | **$0.00089** |

## 5. Deployability

| Check | Result |
|---|---|
| License is OSI-approved or OpenMDW (mit) | pass |
| Served context ≥ 128k (1,048,576 tokens) | pass |
| Served precision documented (FP8) | pass |
| Weights downloadable | pass |
