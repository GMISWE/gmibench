# Contributing

How to add tests, suites, kinds and models, and how to release a new version of the
standard. Run `python bench.py validate` and `pytest` before every commit; CI runs both.

## Words used here

| Word | Meaning |
|---|---|
| **Task** | One test item (one prompt, one checker). Has an `id` and a content `hash`. |
| **Suite** | A folder of tasks under `suites/<name>/` with its own version. |
| **Kind** | A task type (`coding`, `tool_use`, `documents`): how tasks are sent and checked. |
| **Standard** | A released file `standards/vX.Y.yaml`: which suites count, at which versions, and the tier rules. |
| **Role** | What a suite counts for in a standard: `core` (sets the tier), `stress` (separate score), or experimental (not listed: shown, never counts). |

## 1. Add or change tasks in an existing suite

1. Edit `suites/<name>/build.py`.
2. Rebuild the tasks:
   ```bash
   python bench.py generate --suite <name>
   ```
   It prints `CHANGED <old> -> <new>` when the suite's fingerprint changed.
3. Bump `version` in `suites/<name>/suite.yaml`:
   - **patch** (1.0.0 → 1.0.1): a fix that should not change who passes (a typo, a clearer prompt).
   - **minor** (1.0.0 → 1.1.0): tasks added.
   - **major** (1.0.0 → 2.0.0): tasks replaced or made harder; old scores are not comparable.
4. Run `python bench.py validate`. It fails if a reference answer does not pass its own
   checker, or if the tasks changed without a version bump.
5. Run the changed tasks: `python bench.py run --models all --suites <name>`. Only tasks whose
   hash changed are run again; all other results are kept.
6. Score it as work in progress: `python bench.py report --standard dev`.
7. When you are ready to publish, release a new standard (section 5).

Never edit `tasks.jsonl` by hand: `validate` catches it because the stored hashes stop
matching.

## 2. Add a new suite

1. Create the folder:
   ```
   suites/my_suite/
     __init__.py        (empty)
     suite.yaml
     build.py
   ```
2. `suite.yaml`:
   ```yaml
   title: My suite
   version: 0.1.0
   kind: coding            # coding | tool_use | documents (or a new kind, section 3)
   description: >
     One or two sentences on what it tests.
   # environment: env:MyEnv   # tool_use only: a class in suites/my_suite/env.py
   ```
3. `build.py` must define `build(suite_dir: Path) -> list[dict]`. Each task needs the
   fields its kind uses (copy a task from a suite of the same kind). Every task needs a
   reference answer (`reference_solution`, `reference_calls` + `reference_answer`, or
   `expected`), because `validate` checks that the reference passes.
4. `python bench.py generate --suite my_suite`, then `python bench.py validate`.
5. `python bench.py suites` now lists it as **experimental**. Run it and look at the results:
   ```bash
   python bench.py run --dry-run --suites my_suite      # offline check first
   python bench.py run --models all --suites my_suite
   python bench.py report --standard dev
   ```
6. To make it count, release a new standard with `--core my_suite` or `--stress my_suite`.

No other file needs to change: the runner, the fake client, the cost estimate, scoring and
reports all find suites by their folder.

### A new tool environment (`kind: tool_use`)

Put a class in `suites/my_suite/env.py` and point `environment: env:MyEnv` at it. It needs:

- `schemas`: the OpenAI tool definitions.
- `execute(name, arguments) -> str`: run one call on this run's state and return JSON.
- classmethod `check(task, calls, final_answer) -> (passed, details)`. For stateful tools,
  rebuild the state by replaying `calls` in a fresh instance (see `suites/tool_use_hard/env.py`).
  Put `"tool_calls_correct": <bool>` in `details` to feed the tool-call accuracy metric.

The environment must be deterministic: the same calls in the same order give the same state.

## 3. Add a new kind

Only for a new task shape (for example long-context retrieval or multi-turn chat with a
simulated user). Write a subclass of `Kind` in `gmibench/kinds/` and add it to `KINDS` in
`gmibench/kinds/__init__.py`. Implement `check` and `reference`; override `messages`,
`environment`, `fake_answer`, `fake_key` and `estimate` when the defaults do not fit. Add
tests for the checker in `tests/`.

## 4. Add a model

Add an entry to `models.yaml` (copy an existing one). Fill every field from GMI's
`GET /v1/models` (context, precision, prices) and the model's Hugging Face page (license,
parameters, weights URL); leave unknown fields `null`. Set `vision: true` only after a live
check that the endpoint accepts an image **and** the answer uses it. Then:

```bash
python bench.py run --models <name> --suites all
python bench.py report
```

Adding a model does not need a new standard.

## 5. Release a new standard

A standard version says which tasks and rules produced a score.

- **Minor** (1.0 → 1.1): a suite version changed, or a suite was added or removed as stress.
- **Major** (1.x → 2.0): the core suites or the tier rules changed (tiers are not comparable).

Steps:

1. Make sure `python bench.py validate` passes and all models have current results
   (`python bench.py run --models all --suites all` only runs what is missing or changed).
2. Write the standard:
   ```bash
   python bench.py release 1.1 --notes "Adds my_suite as stress; coding 1.1.0 adds 5 tasks"
   # options: --core a,b   --stress c   --drop d
   ```
   It pins every listed suite's current version and fingerprint and copies the protocol
   and tier rules from the latest standard. To change a tier rule, edit the new file now,
   before you commit it. Released files are never edited after that.
3. Add an entry at the top of `CHANGELOG.md`.
4. Rebuild the reports under the new standard: `python bench.py report`.
5. Commit, then tag:
   ```bash
   git tag standard-v1.1 && git push origin standard-v1.1
   ```

To reproduce an old standard's numbers, check out its tag (`git checkout standard-v1.0`) and
run `python bench.py report`.

## Where results come from

Each `run` writes `results/manifests/<id>.json` (git commit, standard, suite versions and
fingerprints, model prices, settings). Each raw record stores that `manifest_id`, the task
`hash` it ran, the suite version, and the prices at run time. Raw files are append-only: a
re-run adds a line, and the newest line for a `(task, run)` with the current task hash wins.
