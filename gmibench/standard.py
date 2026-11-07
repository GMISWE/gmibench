"""Standards: versioned definitions of what counts for a tier.

A standard is one file, `standards/v<MAJOR>.<MINOR>.yaml`. It holds:

  suites:    which suites count, their role, and the exact version and fingerprint
             the results were made with
               core          sets the tier
               stress        separate "stress" score, never changes the tier
               (any suite not listed is "experimental": run and reported, nothing more)
  protocol:  runs per task, temperature, seed, timeouts that affect pass/fail
  tiers, size_classes, deployability: the tier rules

Scoring under a released standard refuses to run if a pinned suite has changed, so a
published "v1.0" result always means the same tasks and rules. To score work in
progress, use the `dev` standard (latest rules, no pins). To publish a change, release a
new standard (`python bench.py release 1.1`), write the CHANGELOG entry and tag the commit.
"""

from __future__ import annotations

import copy
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from .config import ROOT

if TYPE_CHECKING:
    from .suites import Suite

STANDARDS_DIR = ROOT / "standards"
ROLES = ("core", "stress", "experimental")
DEV = "dev"
_FILE_RE = re.compile(r"^v(\d+)\.(\d+)\.yaml$")


class StandardMismatch(Exception):
    """A released standard's pinned suites no longer match the suites on disk."""


@dataclass
class Standard:
    """A loaded standard. `data` is the parsed YAML (tiers, size_classes, ...)."""

    version: str
    data: dict[str, Any]
    path: Path | None = None
    roles: dict[str, str] = field(default_factory=dict)
    pins: dict[str, dict[str, str]] = field(default_factory=dict)

    @property
    def is_dev(self) -> bool:
        return self.version == DEV

    @property
    def label(self) -> str:
        if self.is_dev:
            return f"GMI Open Model Standard dev (unreleased; rules from v{self.data.get('based_on', '?')})"
        return f"GMI Open Model Standard v{self.version}"

    @property
    def protocol(self) -> dict[str, Any]:
        return dict(self.data.get("protocol") or {})

    def role(self, suite_name: str) -> str:
        return self.roles.get(suite_name, "experimental")

    def names(self, role: str, available: list[str]) -> list[str]:
        """Suite names with a role, in standard order (then name order for experimental)."""
        if role == "experimental":
            return sorted(n for n in available if n not in self.roles)
        return [n for n, r in self.roles.items() if r == role and n in available]

    def ordered(self, available: list[str]) -> list[str]:
        """All available suites: core first, then stress, then experimental."""
        return [n for r in ROLES for n in self.names(r, available)]

    def scoring_dict(self) -> dict[str, Any]:
        """The rules as a plain dict for `scoring` (tiers, size classes, deployability, roles)."""
        d = copy.deepcopy(self.data)
        d["roles"] = dict(self.roles)
        return d

    def check_pins(self, suites: dict[str, "Suite"]) -> list[str]:
        """Problems that stop this standard from scoring the suites on disk."""
        if self.is_dev:
            return []
        problems = []
        for name, pin in self.pins.items():
            s = suites.get(name)
            if s is None:
                problems.append(f"suite '{name}' is pinned by v{self.version} but missing from suites/")
                continue
            if s.version != pin["version"]:
                problems.append(f"{name}: suite.yaml says {s.version}, v{self.version} pins {pin['version']}")
            elif s.fingerprint() != pin["fingerprint"]:
                problems.append(f"{name}: tasks changed since v{self.version} (fingerprint {s.fingerprint()} "
                                f"!= {pin['fingerprint']}) but the suite version was not bumped")
        return problems


# --------------------------------------------------------------------------- loading


def released_versions(standards_dir: Path = STANDARDS_DIR) -> list[tuple[int, int]]:
    """Released versions, oldest first."""
    out = []
    for p in standards_dir.glob("v*.yaml"):
        m = _FILE_RE.match(p.name)
        if m:
            out.append((int(m.group(1)), int(m.group(2))))
    return sorted(out)


def _from_file(path: Path) -> Standard:
    data = yaml.safe_load(path.read_text()) or {}
    roles, pins = {}, {}
    for name, spec in (data.get("suites") or {}).items():
        role = spec.get("role", "core")
        if role not in ("core", "stress"):
            raise ValueError(f"{path}: suite {name} has role '{role}'; use core or stress "
                             "(leave a suite out to make it experimental)")
        roles[name] = role
        pins[name] = {"version": str(spec["version"]), "fingerprint": str(spec["fingerprint"])}
    return Standard(version=str(data["standard"]), data=data, path=path, roles=roles, pins=pins)


def load_standard(name: str = "latest", standards_dir: Path = STANDARDS_DIR) -> Standard:
    """Load `latest`, `dev` or a version such as `1.0`."""
    versions = released_versions(standards_dir)
    if not versions:
        raise SystemExit(f"No standards found in {standards_dir}. Create one with `python bench.py release 1.0`.")
    key = name.lower().lstrip("v")
    if key in ("latest", DEV):
        major, minor = versions[-1]
    else:
        try:
            major, minor = (int(x) for x in key.split("."))
        except ValueError:
            raise SystemExit(f"Bad standard '{name}'. Use latest, dev, or a version like 1.0.") from None
        if (major, minor) not in versions:
            have = ", ".join(f"{a}.{b}" for a, b in versions)
            raise SystemExit(f"Standard v{major}.{minor} not found. Released: {have}")
    std = _from_file(standards_dir / f"v{major}.{minor}.yaml")
    if key == DEV:
        data = copy.deepcopy(std.data)
        data["based_on"] = std.version
        std = Standard(version=DEV, data=data, path=None, roles=dict(std.roles), pins={})
    return std


# --------------------------------------------------------------------------- releasing


def release(version: str, suites: dict[str, "Suite"], roles: dict[str, str] | None = None,
            notes: str = "", standards_dir: Path = STANDARDS_DIR, base: Standard | None = None) -> Path:
    """Write `standards/v<version>.yaml` that pins the current suites.

    Rules (protocol, tiers, size classes, deployability) are copied from the latest
    standard unless this is the first one. `roles` sets the role of each pinned suite;
    by default the roles of the latest standard are kept and new suites stay experimental.
    """
    if not re.fullmatch(r"\d+\.\d+", version):
        raise SystemExit("Version must look like 1.1 (MAJOR.MINOR).")
    path = standards_dir / f"v{version}.yaml"
    if path.exists():
        raise SystemExit(f"{path} already exists. Released standards are never edited; release a new version.")
    if base is None and released_versions(standards_dir):
        base = load_standard("latest", standards_dir)
    if base is None:
        raise SystemExit("No earlier standard to copy rules from.")
    roles = dict(base.roles if roles is None else roles)
    data: dict[str, Any] = {"standard": version, "released": date.today().isoformat(),
                            "notes": notes or "TODO: describe what changed (also add it to CHANGELOG.md)."}
    data["suites"] = {n: {"role": roles[n], "version": suites[n].version, "fingerprint": suites[n].fingerprint()}
                      for n in roles if n in suites}
    for key in ("protocol", "tiers", "size_classes", "deployability"):
        data[key] = copy.deepcopy(base.data.get(key))
    standards_dir.mkdir(parents=True, exist_ok=True)
    path.write_text(_HEADER + yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=100))
    return path


_HEADER = """\
# GMI Open Model Standard. Released standards are never edited: release a new version instead.
# suites: role (core sets the tier, stress is a separate score), plus the pinned suite version
#         and fingerprint. Suites not listed here are experimental.
"""
