# GMI Open Model Standard: cohort summary (2026-11-06)

Scored under **GMI Open Model Standard v1.0**.

## Overall (sorted by cost per successful task)

| Model | Tier | Size | Core suites | Core pass | Like-for-like pass | Stress pass | Consistency | TTFT median | Tokens/s | Cost / success | Truncated runs | Deployability |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gemma-4-26b-a4b | Best value in class | small | 2/3 | 99.2% | 99.2% | 90.8% | 97.5% | 0.53 s | 202.6 | $0.00013 | 0 | 4/4 |
| deepseek-v4-flash | Best value in class | large | 2/3 | 97.5% | 97.5% | 81.7% | 95.0% | 0.49 s | 402.1 | $0.00041 | 24 | 4/4 |
| glm-5.3-flash | Best value in class | large | 3/3 | 97.2% | 95.8% | 89.4% | 95.0% | 0.60 s | 95.1 | $0.00085 | 14 | 4/4 |
| minimax-m2.5 | Meets production bar | large | 2/3 | 95.8% | 95.8% | 80.0% | 90.0% | 0.93 s | 73.0 | $0.00184 | 16 | 3/4 |
| qwen3.5-27b | Completed | small | 3/3 | 87.8% | 89.2% | 80.6% | 76.7% | 1.95 s | 58.2 | $0.00502 | 0 | 4/4 |
| qwen3.6-35b-a3b | Best value in class | small | 3/3 | 98.9% | 98.3% | 95.6% | 96.7% | 0.99 s | 130.9 | $0.00585 | 1 | 4/4 |
| qwen3.5-122b-a10b | Best value in class | mid | 3/3 | 99.4% | 99.2% | 90.6% | 98.3% | 1.09 s | 159.7 | $0.00825 | 0 | 4/4 |

Core pass, consistency, TTFT and cost use the core suites (these set the tier). Models without vision skip the documents suite, so **Like-for-like pass** uses only the core suites every model ran (Coding, Tool use). Stress pass is a separate score. Truncated runs hit the output-token limit and count as failures. Cost uses GMI list prices without cache or account discounts.

## Coding (core: sets the tier; sorted by cost per successful task)

| Model | Size | Status | Pass rate | Consistency | TTFT median | Cost / success | Recommended |
|---|---|---|---|---|---|---|---|
| gemma-4-26b-a4b | small | ok | 98.3% | 95.0% | 0.53 s | $0.00012 | yes |
| deepseek-v4-flash | large | ok | 96.7% | 95.0% | 0.49 s | $0.00057 | yes |
| glm-5.3-flash | large | ok | 91.7% | 85.0% | 0.51 s | $0.00210 |  |
| minimax-m2.5 | large | ok | 91.7% | 80.0% | 0.97 s | $0.00327 |  |
| qwen3.5-27b | small | ok | 80.0% | 65.0% | 1.89 s | $0.0145 |  |
| qwen3.6-35b-a3b | small | ok | 96.7% | 90.0% | 0.86 s | $0.0163 |  |
| qwen3.5-122b-a10b | mid | ok | 98.3% | 95.0% | 0.98 s | $0.0229 | yes |

## Tool use (core: sets the tier; sorted by cost per successful task)

| Model | Size | Status | Pass rate | Consistency | TTFT median | Cost / success | Recommended |
|---|---|---|---|---|---|---|---|
| gemma-4-26b-a4b | small | ok | 100.0% | 100.0% | – s | $0.00014 | yes |
| glm-5.3-flash | large | ok | 100.0% | 100.0% | 0.58 s | $0.00022 | yes |
| deepseek-v4-flash | large | ok | 98.3% | 95.0% | 0.48 s | $0.00025 |  |
| minimax-m2.5 | large | ok | 100.0% | 100.0% | 0.93 s | $0.00052 |  |
| qwen3.6-35b-a3b | small | ok | 100.0% | 100.0% | 0.76 s | $0.00076 |  |
| qwen3.5-27b | small | ok | 98.3% | 95.0% | 2.03 s | $0.00092 |  |
| qwen3.5-122b-a10b | mid | ok | 100.0% | 100.0% | 0.92 s | $0.00112 | yes |

## Documents (core: sets the tier; sorted by cost per successful task)

| Model | Size | Status | Pass rate | Consistency | TTFT median | Cost / success | Recommended |
|---|---|---|---|---|---|---|---|
| glm-5.3-flash | large | ok | 100.0% | 100.0% | 1.90 s | $0.00032 | yes |
| qwen3.6-35b-a3b | small | ok | 100.0% | 100.0% | 3.22 s | $0.00082 | yes |
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
