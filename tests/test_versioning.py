"""Versioning and tracking: task hashes, standards, releases, manifests, new suites."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import bench
from conftest import make_rec
from gmibench import scoring
from gmibench.runner import pending_jobs
from gmibench.standard import Standard, load_standard, release
from gmibench.suites import discover, task_hash


def test_changed_task_is_rerun_and_old_result_ignored(tmp_path, model):
    task = {"id": "t1", "hash": "new"}
    old = make_rec("t1", 0, True)
    old["task_hash"] = "old"
    assert pending_jobs([task], {("t1", 0): old}, 1, retry_errors=False) == [(task, 0)]

    raw = tmp_path / "raw" / model.slug
    raw.mkdir(parents=True)
    current = dict(make_rec("t1", 1, False), task_hash="new")
    (raw / "coding.jsonl").write_text(json.dumps(old) + "\n" + json.dumps(current) + "\n")
    loaded = scoring.load_raw(tmp_path, model, {"coding": [task]})
    assert [r["run"] for r in loaded["coding"]] == [1]


def test_task_hash_covers_content_and_image(tmp_path):
    (tmp_path / "a.png").write_bytes(b"one")
    t = {"id": "x", "prompt": "p", "image": "a.png"}
    h1 = task_hash(t, tmp_path)
    assert task_hash(dict(t, prompt="q"), tmp_path) != h1
    (tmp_path / "a.png").write_bytes(b"two")
    assert task_hash(t, tmp_path) != h1
    assert task_hash(dict(t, hash="ignored"), tmp_path) == task_hash(t, tmp_path)


def test_released_standard_matches_suites_on_disk():
    std = load_standard("latest")
    assert std.check_pins(discover()) == []
    assert std.role("coding") == "core" and std.role("coding_hard") == "stress"
    assert std.role("some_new_suite") == "experimental"


def test_pin_mismatch_is_caught_but_dev_allows_it():
    found = discover()
    std = load_standard("1.0")
    bad = Standard(version="9.9", data=std.data, roles=std.roles,
                   pins={**std.pins, "coding": {"version": "1.0.0", "fingerprint": "deadbeef0000"}})
    problems = bad.check_pins(found)
    assert len(problems) == 1 and "not bumped" in problems[0]
    assert load_standard("dev").check_pins(found) == []
    assert load_standard("dev").label.startswith("GMI Open Model Standard dev")


def test_release_pins_suites_and_never_overwrites(tmp_path):
    found = discover()
    base = load_standard("1.0")
    path = release("1.1", found, {"coding": "core", "tool_use_hard": "stress"}, notes="test",
                   standards_dir=tmp_path, base=base)
    rel = load_standard("1.1", standards_dir=tmp_path)
    assert rel.pins["coding"]["fingerprint"] == found["coding"].fingerprint()
    assert rel.role("tool_use_hard") == "stress" and rel.role("documents") == "experimental"
    assert rel.data["tiers"] == base.data["tiers"]
    with pytest.raises(SystemExit):
        release("1.1", found, None, standards_dir=tmp_path, base=base)
    assert path.exists()


def test_run_cost_uses_price_saved_with_the_run(model):
    rec = dict(make_rec("t", 0, True, prompt_tokens=1_000_000, completion_tokens=0), price_in_per_m=0.5)
    assert scoring.run_cost(rec, model) == pytest.approx(0.5)   # saved price, not models.yaml's 1.0
    assert scoring.run_cost(make_rec("t", 0, True, prompt_tokens=1_000_000, completion_tokens=0),
                            model) == pytest.approx(1.0)


def test_dry_run_writes_manifest_and_stamps_records(tmp_path):
    rc = bench.main(["run", "--dry-run", "--results-dir", str(tmp_path), "--models", "gemma-4-26b-a4b",
                     "--suites", "coding", "--runs", "1"])
    assert rc == 0
    manifests = list((tmp_path / "manifests").glob("*.json"))
    assert len(manifests) == 1
    man = json.loads(manifests[0].read_text())
    assert man["suites"]["coding"]["fingerprint"] == discover()["coding"].fingerprint()
    assert man["summary"]["gemma-4-26b-a4b"]["done"] == 20
    recs = [json.loads(x) for x in (tmp_path / "raw" / "gemma-4-26b-a4b" / "coding.jsonl").read_text().splitlines()]
    assert all(r["manifest_id"] == man["manifest_id"] and r["task_hash"] and r["suite_version"] for r in recs)


def test_new_suite_folder_is_discovered(tmp_path):
    """A suite is just a folder: suite.yaml + tasks.jsonl is enough to load and validate it."""
    from gmibench.kinds import kind_of

    d = tmp_path / "tiny"
    d.mkdir()
    (d / "suite.yaml").write_text("title: Tiny\nversion: 0.1.0\nkind: coding\n")
    task = {"id": "tiny-01", "prompt": "Write add(a, b).", "entry_point": "add", "max_tokens": 256,
            "tests": "assert add(2, 3) == 5", "reference_solution": "def add(a, b):\n    return a + b\n"}
    task["hash"] = task_hash(task, d)
    (d / "tasks.jsonl").write_text(json.dumps(task) + "\n")
    suite = discover(tmp_path)["tiny"]
    assert suite.title == "Tiny" and len(suite.load_tasks()) == 1
    assert kind_of(suite).validate(suite.load_tasks()[0], suite) == []


def test_validate_and_generate_check_pass():
    assert bench.main(["validate"]) == 0
    assert bench.main(["generate", "--check", "--suite", "coding,tool_use,tool_use_hard"]) == 0
