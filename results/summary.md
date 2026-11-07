# GMI Open Model Standard: cohort summary (2026-11-06)

Scored under **GMI Open Model Standard v1.0**.

## Overall (sorted by cost per successful task)

| Model | Tier | Size | Pass rate | Hard pass rate | Consistency | TTFT median | Tokens/s | Cost / success | Deployability | Best for |
|---|---|---|---|---|---|---|---|---|---|---|
| gemma-4-26b-a4b | GMI Recommended | small | 100.0% | 90.8% | 100.0% | 0.52 s | 95.4 | $0.00013 | 4/4 | Coding |
| deepseek-v4-flash | GMI Verified | large | 90.8% | 81.7% | 85.0% | 1.69 s | 203.7 | $0.00078 | 4/4 | Tool use |
| glm-5.3-flash | GMI Recommended | large | 96.7% | 89.4% | 93.3% | 0.64 s | 105.2 | $0.00089 | 4/4 | Tool use |
| minimax-m2.5 | GMI Production Ready | large | 95.8% | 80.0% | 90.0% | 0.93 s | 73.0 | $0.00184 | 3/4 | Tool use |
| qwen3.5-27b | GMI Verified | small | 87.8% | 80.6% | 76.7% | 1.95 s | 58.2 | $0.00502 | 4/4 | Tool use |
| qwen3.6-35b-a3b | GMI Recommended | small | 97.2% | 95.6% | 93.3% | 0.90 s | 136.1 | $0.00740 | 4/4 | Tool use |
| qwen3.5-122b-a10b | GMI Recommended | mid | 99.4% | 90.6% | 98.3% | 1.09 s | 159.7 | $0.00825 | 4/4 | Documents |

Pass rate, consistency, TTFT and cost use the core suites (these set the tier). Hard pass rate is the separate stress score over the stress suites.

## Coding (core: sets the tier; sorted by cost per successful task)

| Model | Size | Status | Pass rate | Consistency | TTFT median | Cost / success | Recommended |
|---|---|---|---|---|---|---|---|
| gemma-4-26b-a4b | small | ok | 100.0% | 100.0% | 0.52 s | $0.00012 | yes |
| deepseek-v4-flash | large | ok | 81.7% | 70.0% | 1.70 s | $0.00141 |  |
| glm-5.3-flash | large | ok | 91.7% | 85.0% | 0.51 s | $0.00225 | yes |
| minimax-m2.5 | large | ok | 91.7% | 80.0% | 0.97 s | $0.00327 |  |
| qwen3.5-27b | small | ok | 80.0% | 65.0% | 1.89 s | $0.0145 |  |
| qwen3.6-35b-a3b | small | ok | 91.7% | 80.0% | 0.83 s | $0.0218 |  |
| qwen3.5-122b-a10b | mid | ok | 98.3% | 95.0% | 0.98 s | $0.0229 | yes |

## Tool use (core: sets the tier; sorted by cost per successful task)

| Model | Size | Status | Pass rate | Consistency | TTFT median | Cost / success | Recommended |
|---|---|---|---|---|---|---|---|
| gemma-4-26b-a4b | small | ok | 100.0% | 100.0% | – s | $0.00014 | yes |
| glm-5.3-flash | large | ok | 100.0% | 100.0% | 0.57 s | $0.00021 | yes |
| deepseek-v4-flash | large | ok | 100.0% | 100.0% | 1.66 s | $0.00026 |  |
| minimax-m2.5 | large | ok | 100.0% | 100.0% | 0.93 s | $0.00052 |  |
| qwen3.6-35b-a3b | small | ok | 100.0% | 100.0% | 0.74 s | $0.00079 |  |
| qwen3.5-27b | small | ok | 98.3% | 95.0% | 2.03 s | $0.00092 |  |
| qwen3.5-122b-a10b | mid | ok | 100.0% | 100.0% | 0.92 s | $0.00112 | yes |

## Documents (core: sets the tier; sorted by cost per successful task)

| Model | Size | Status | Pass rate | Consistency | TTFT median | Cost / success | Recommended |
|---|---|---|---|---|---|---|---|
| glm-5.3-flash | large | ok | 98.3% | 95.0% | 0.88 s | $0.00030 | yes |
| qwen3.6-35b-a3b | small | ok | 100.0% | 100.0% | 2.90 s | $0.00081 | yes |
| qwen3.5-27b | small | ok | 85.0% | 70.0% | 2.20 s | $0.00089 |  |
| qwen3.5-122b-a10b | mid | ok | 100.0% | 100.0% | 1.71 s | $0.00101 | yes |

n/a (not vision-capable): gemma-4-26b-a4b, deepseek-v4-flash, minimax-m2.5

## Coding (hard) (stress: separate score; sorted by cost per successful task)

| Model | Size | Status | Pass rate | Consistency | TTFT median | Cost / success | Recommended |
|---|---|---|---|---|---|---|---|
| gemma-4-26b-a4b | small | ok | 93.3% | 90.0% | 0.51 s | $0.00037 |  |
| glm-5.3-flash | large | ok | 83.3% | 75.0% | 0.49 s | $0.00653 |  |
| deepseek-v4-flash | large | ok | 63.3% | 45.0% | 1.70 s | $0.00992 |  |
| qwen3.5-27b | small | ok | 65.0% | 55.0% | 1.94 s | $0.0163 |  |
| minimax-m2.5 | large | ok | 71.7% | 60.0% | 0.96 s | $0.0225 |  |
| qwen3.6-35b-a3b | small | ok | 88.3% | 70.0% | 0.94 s | $0.0378 |  |
| qwen3.5-122b-a10b | mid | ok | 85.0% | 65.0% | 0.90 s | $0.0448 |  |

## Tool use (hard) (stress: separate score; sorted by cost per successful task)

| Model | Size | Status | Pass rate | Consistency | TTFT median | Cost / success | Recommended |
|---|---|---|---|---|---|---|---|
| glm-5.3-flash | large | ok | 85.0% | 85.0% | 0.55 s | $0.00229 |  |
| deepseek-v4-flash | large | ok | 100.0% | 100.0% | 0.51 s | $0.00288 |  |
| gemma-4-26b-a4b | small | ok | 88.3% | 80.0% | – s | $0.00288 |  |
| minimax-m2.5 | large | ok | 88.3% | 70.0% | 0.88 s | $0.00533 |  |
| qwen3.6-35b-a3b | small | ok | 98.3% | 95.0% | 0.76 s | $0.00643 |  |
| qwen3.5-27b | small | ok | 100.0% | 100.0% | 1.67 s | $0.00970 |  |
| qwen3.5-122b-a10b | mid | ok | 86.7% | 80.0% | 0.92 s | $0.0150 |  |

## Documents (hard) (stress: separate score; sorted by cost per successful task)

| Model | Size | Status | Pass rate | Consistency | TTFT median | Cost / success | Recommended |
|---|---|---|---|---|---|---|---|
| glm-5.3-flash | large | ok | 100.0% | 100.0% | 1.41 s | $0.00042 |  |
| qwen3.6-35b-a3b | small | ok | 100.0% | 100.0% | 7.29 s | $0.00121 |  |
| qwen3.5-27b | small | ok | 76.7% | 65.0% | 4.40 s | $0.00144 |  |
| qwen3.5-122b-a10b | mid | ok | 100.0% | 100.0% | 3.16 s | $0.00146 |  |

n/a (not vision-capable): gemma-4-26b-a4b, deepseek-v4-flash, minimax-m2.5
