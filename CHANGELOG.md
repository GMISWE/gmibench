# Changelog

Standards are versioned `vMAJOR.MINOR` (see `CONTRIBUTING.md`, section 5). Each entry lists
the suites it pins and what changed. Harness changes that do not change scores are listed
under "Harness".

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
- Tiers: Verified (all core suites complete, error rate < 2%), Production Ready (pass rate
  ≥ 70%, consistency ≥ 80%, median TTFT ≤ 1.5 s), Recommended (Production Ready and the
  lowest cost per successful task on a core suite within its size class).
- `tool_use_hard` is at 2.0.0 because v1 (3 simple tools) was replaced by the support-desk
  environment before release. The v1 tasks and results are in `results/archive/tool_use_hard_v1/`.
- Results in `results/` were recorded on 2026-11-05/06 (manifest `legacy-pre-v1.0`) for 10
  models; 3 were down on GMI and are "Not verified".

### Harness

- Suites are self-contained folders (`suites/<name>/`); kinds live in `gmibench/kinds/`.
- Every task has a content hash; every result records it. Changed tasks are re-run.
- Standards pin suite versions and fingerprints; `bench.py release` writes new ones.
- Every run writes a manifest; every result stores its prices and manifest ID.
- New commands: `suites`, `validate`, `release`, `generate --check`. `--tasks` is now
  `--suites` (the old flag still works).
- `thresholds.yaml` was split into `standards/v1.0.yaml` (rules) and `settings.yaml` (run knobs).
- CI (GitHub Actions) runs the tests, `validate`, `generate --check`, scoring, and a dry run.
