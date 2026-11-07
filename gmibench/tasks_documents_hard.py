"""Hard document tasks (stress set): degraded scans, European number/date formats,
long invoices, partial payments and faded receipts. Deterministic, like the core set.
"""

from __future__ import annotations

import datetime as dt
import io
import random
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

from .tasks_documents import DOC_MAX_TOKENS, ITEMS, PROMPT, _fmt_date, _make_items, _money, _render

SEED = 20261106


def _font_path() -> str:
    """DejaVu Sans ships with matplotlib and covers ü, ö, ä, é and €; Pillow's default font does not."""
    import matplotlib
    return str(Path(matplotlib.get_data_path()) / "fonts" / "ttf" / "DejaVuSans.ttf")

PROMPT_HARD = PROMPT.replace(
    "No commentary.",
    "- If the document shows a payment already received, total is the remaining balance due.\nNo commentary.")

ITEMS.setdefault("long", [
    ("Network switch 24-port", 180.0, 320.0), ("Cat6 patch cable", 3.0, 9.0), ("Rack shelf", 45.0, 90.0),
    ("Server rail kit", 60.0, 110.0), ("UPS battery", 120.0, 240.0), ("Label printer tape", 12.0, 22.0),
    ("Fiber transceiver", 35.0, 75.0), ("Cable ties (100)", 4.0, 8.0), ("KVM switch", 140.0, 260.0),
    ("Power strip 8-outlet", 25.0, 48.0), ("Installation labor (hr)", 90.0, 140.0), ("Wall plate", 2.0, 6.0),
    ("Keystone jack", 1.5, 4.0), ("Wireless access point", 110.0, 210.0), ("Surge protector", 30.0, 55.0),
    ("Site survey", 200.0, 400.0),
])

# (vendor, template, flavour)
PLAN: list[tuple[str, str, str]] = [
    ("Ironclad Fasteners Inc.", "invoice", "scan"),
    ("Westbrook Paper Mills", "purchase_order", "scan"),
    ("Juniper Ridge Landscaping", "work_order", "scan"),
    ("Halcyon Audio Visual LLC", "invoice", "scan"),
    ("Crescent Bay Seafood Co.", "invoice", "scan"),
    ("Müller & Söhne GmbH", "invoice", "euro"),
    ("Nordlicht Elektro GmbH", "purchase_order", "euro"),
    ("Atelier Dupont SARL", "invoice", "euro"),
    ("Bäckerei Schneider", "work_order", "euro"),
    ("Vantage Network Systems", "invoice", "long"),
    ("Ridgeline Data Cabling", "purchase_order", "long"),
    ("Beacon Facilities Group", "work_order", "long"),
    ("Clearwater Tech Supply", "invoice", "long"),
    ("Maple Street Print Shop", "invoice", "partial"),
    ("Sterling Event Rentals", "invoice", "partial"),
    ("Foxglove Interiors", "purchase_order", "partial"),
    ("Pinecrest HVAC Services", "work_order", "partial"),
    ("Corner Grind Cafe", "receipt", "faded"),
    ("Lantern Noodle House", "receipt", "faded"),
    ("Daily Harvest Market", "receipt", "faded"),
]


def _money_eu(x: float) -> str:
    return f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " €"


def _degrade(path: Path, rng: random.Random, flavour: str) -> None:
    """Make the clean render look like a phone scan or a faded thermal receipt."""
    img = Image.open(path).convert("L")
    if flavour in ("scan", "euro", "partial", "long"):
        angle = rng.uniform(1.2, 3.2) * rng.choice([-1, 1])
        img = img.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True, fillcolor=245)
    if flavour == "scan":
        w, h = img.size
        img = img.resize((int(w * 0.62), int(h * 0.62)), Image.Resampling.LANCZOS)
        img = img.filter(ImageFilter.GaussianBlur(0.9))
    if flavour == "faded":
        img = ImageEnhance.Contrast(img).enhance(0.38)
        img = ImageEnhance.Brightness(img).enhance(1.12)
        img = img.filter(ImageFilter.GaussianBlur(0.6))
    arr = np.asarray(img, dtype=np.float32)
    noise = np.random.default_rng(rng.randint(0, 2**31)).normal(0, 9 if flavour != "long" else 5, arr.shape)
    img = Image.fromarray(np.clip(arr + noise, 0, 255).astype(np.uint8))
    if flavour in ("scan", "faded"):
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=35)
        img = Image.open(io.BytesIO(buf.getvalue())).convert("L")
    img.save(path, optimize=True)


def build_document_hard_tasks(assets_dir: Path) -> list[dict[str, Any]]:
    """Render the 20 hard document PNGs and return tasks with ground truth."""
    assets_dir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    tasks: list[dict[str, Any]] = []
    for i, (vendor, kind, flavour) in enumerate(PLAN, start=1):
        if flavour == "euro":
            date = dt.date(2026, rng.randint(1, 10), rng.randint(13, 28))
            fmt = "%d.%m.%Y"
        else:
            date = dt.date(2026, 1, 1) + dt.timedelta(days=rng.randint(0, 300))
            fmt = rng.choice(["%B %-d, %Y", "%d %b %Y", "%Y-%m-%d", "%b. %-d, %Y"])
        pool = {"receipt": "receipt", "work_order": "work"}.get(kind, "default")
        if flavour == "long":
            pool, n_items = "long", rng.randint(9, 14)
        else:
            n_items = rng.randint(2, 4) if kind == "receipt" else rng.randint(3, 6)
        items = _make_items(rng, pool, n_items)
        subtotal = round(sum(it["amount"] for it in items), 2)
        discount = round(subtotal * 0.05, 2) if kind == "work_order" else 0.0
        tax_rate = 19 if flavour == "euro" else rng.choice([5, 6.5, 7.25, 8, 8.875, 10])
        tax = round((subtotal - discount) * tax_rate / 100, 2)
        shipping = round(rng.uniform(8, 45), 2) if kind in ("invoice", "purchase_order") and rng.random() < 0.6 else 0.0
        gross = round(subtotal - discount + tax + shipping, 2)
        paid = round(gross * rng.choice([0.25, 0.3, 0.5]), 2) if flavour == "partial" else 0.0
        total = round(gross - paid, 2)
        gt = {"vendor": vendor, "date": date.isoformat(), "total": total, "line_items": items}
        extras = {
            "address": f"{rng.randint(10, 999)} {rng.choice(['Industriestr.', 'Rue de la Paix', 'Bay St', 'Market St'])}, "
                       f"{rng.choice(['München', 'Lyon', 'Seattle, WA', 'Boston, MA'])}",
            "phone": f"+{rng.randint(1, 49)} {rng.randint(100, 999)} {rng.randint(1000000, 9999999)}",
            "number": f"{rng.randint(10000, 99999)}",
            "date_str": _fmt_date(date, fmt),
            "due_str": _fmt_date(date + dt.timedelta(days=30), fmt),
            "time": f"{rng.randint(7, 21):02d}:{rng.randint(0, 59):02d}",
            "buyer": rng.choice(["Acme Robotics", "Juniper Health Clinic", "Delta Analytics", "Pioneer Labs"]),
            "tech": rng.choice(["J. Alvarez", "M. Chen", "S. Okafor", "R. Patel"]),
            "subtotal": subtotal, "discount": discount, "tax_rate": tax_rate, "tax": tax, "shipping": shipping,
            "cash": float(int(total // 10 + 1) * 10), "gross": gross, "paid": paid,
            "note": "All amounts in EUR." if flavour == "euro" else rng.choice(
                ["Payment terms: Net 30.", "Thank you for your business.", "Late fee 1.5% per month."]),
        }
        name = f"hdoc-{i:02d}.png"
        _render(kind, gt, extras, assets_dir / name, money=_money_eu if flavour == "euro" else _money,
                font_path=_font_path())
        _degrade(assets_dir / name, rng, flavour)
        tasks.append({
            "id": f"hdoc-{i:02d}",
            "category": f"{kind}/{flavour}",
            "prompt": PROMPT_HARD,
            "image": f"assets/{name}",
            "checker": "document_extraction",
            "max_tokens": DOC_MAX_TOKENS,
            "expected": gt,
        })
    return tasks
