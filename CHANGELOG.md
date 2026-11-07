# Changelog

Standards are versioned `vMAJOR.MINOR` (see `CONTRIBUTING.md`, section 5). Each entry lists
the suites it pins and what changed. Harness changes that do not change scores are listed
under "Harness".

## Unreleased (results and harness; standard rules unchanged)

- Tier labels renamed so they describe what was met instead of reading as endorsements; the
  rules are the same: GMI Verified → **Completed**, GMI Production Ready → **Meets production
  bar**, GMI Recommended → **Best value in class**, Not verified → **Not rated**. A "best
  value" win with no other qualifying model in the size class is marked **uncontested**.
- Reports add: core suites run (2/3 or 3/3), a like-for-like pass rate over the core suites
  every model runs, truncated runs, and per-model platform notes (retried API errors,
  non-streamed fallbacks, unparsed tool-call text).
- Core suites re-measured on 2026-11-06 (Pacific) for gemma-4-26b-a4b, glm-5.3-flash,
  deepseek-v4-flash and qwen3.6-35b-a3b, whose first core runs overlapped a GMI service
  incident. New records supersede the old ones, which stay in `results/raw/`.
- `bench.py run --rerun` re-measures recorded runs in a new time window.
- `bench.py report` keeps the README results table in sync with the scores.
- README: scope and disclaimer, expanded limits, contact. Chart axis now starts at 0.
- Model metadata updated from the model cards (active parameters for Gemma, GLM, DeepSeek).
- Three planned models (Nemotron 3.5 Super-VL, Nemotron 3.5 Lightning, gpt-oss-120b) were not
  available during the test window and are not part of the cohort.

## Standard v1.0 (2026-11-06)

First release. Tag: `standard-v1.0`.

| Suite | Version | Role | Fingerprint |
|---|---|---|---|
| coding | 1.0.0 | core | `3cb7b868e334` |
| tool_use | 1.0.0 | core | `d51aef1642ae` |
| documents | 1.0.0 | core | `2e61c2a31027` |
| coding_hard | 1.0.0 | stress | `0cf6b422ac15` |
| tool_use_hard | 2.0.0 | stress | `437d1a7ee157` |
| documents_hard | 1.0.0 | stress | `5f15481c2d22` |

- Protocol: 3 runs per task, temperature 0, seed 1234, coding tests time out after 10 s.
- Tiers: Completed (all core suites complete, error rate < 2%), Meets production bar (pass
  rate ≥ 70%, consistency ≥ 80%, median TTFT ≤ 1.5 s), Best value in class (meets the bar and
  the lowest cost per successful task on a core suite within its size class). Labels as
  renamed after release; the rules are unchanged.
- `tool_use_hard` is at 2.0.0 because v1 (3 simple tools) was replaced by the support-desk
  environment before release. The v1 tasks and results are in `results/archive/tool_use_hard_v1/`.
- Results in `results/` were recorded on 2026-11-05/06 (Pacific; manifest `legacy-pre-v1.0`)
  for 7 models.

### Harness

- Suites are self-contained folders (`suites/<name>/`); kinds live in `gmibench/kinds/`.
- Every task has a content hash; every result records it. Changed tasks are re-run.
- Standards pin suite versions and fingerprints; `bench.py release` writes new ones.
- Every run writes a manifest; every result stores its prices and manifest ID.
- New commands: `suites`, `validate`, `release`, `generate --check`. `--tasks` is now
  `--suites` (the old flag still works).
- `thresholds.yaml` was split into `standards/v1.0.yaml` (rules) and `settings.yaml` (run knobs).
- CI (GitHub Actions) runs the tests, `validate`, `generate --check`, scoring, and a dry run.
