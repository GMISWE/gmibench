"""Document task generation: 20 synthetic invoices and forms rendered to PNG with Pillow.

Generation is deterministic (fixed seed), so the same assets and ground truth come
out on every machine with the same Pillow version. The PNGs are committed anyway.
"""

from __future__ import annotations

import datetime as dt
import random
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

DOC_MAX_TOKENS = 4096
SEED = 20261105

VENDORS = [
    "Northwind Traders LLC", "Blue Harbor Coffee Co.", "Apex Office Supply Inc.", "Granite Peak Outfitters",
    "Lumen Electrical Services", "Brightside Printing Ltd.", "Cedar & Pine Furniture", "Quantum Lab Instruments",
    "Saffron Kitchen Catering", "Riverbend Auto Repair", "Polar Freight Logistics", "Meridian Software GmbH",
    "Silverline Plumbing", "Orchard Valley Produce", "Kestrel Cleaning Services", "Atlas Hardware Depot",
    "Harborview Dental Supply", "Copperleaf Florist", "Summit IT Consulting", "Tidewater Marine Parts",
]
BUYERS = ["Acme Robotics", "Juniper Health Clinic", "Fairmont School District", "Delta Analytics",
          "Oakridge Hotel", "Pioneer Labs"]
ITEMS = {
    "default": [("Consulting hours", 85.0, 150.0), ("Printer paper (case)", 32.0, 48.0),
                ("Toner cartridge", 64.0, 120.0), ("USB-C cable 2m", 9.0, 19.0),
                ("Desk lamp", 28.0, 55.0), ("Shipping box (pack of 25)", 18.0, 30.0),
                ("Ergonomic chair", 189.0, 349.0), ("Wireless mouse", 15.0, 35.0),
                ("Monitor stand", 39.0, 79.0), ("Cleaning supplies kit", 22.0, 45.0)],
    "receipt": [("Latte", 4.25, 5.75), ("Croissant", 3.0, 4.5), ("Bagel w/ cream cheese", 3.5, 5.0),
                ("Cold brew", 4.0, 5.5), ("Muffin", 2.75, 3.95), ("Sandwich", 7.5, 11.0),
                ("Bottled water", 1.5, 2.5)],
    "work": [("Labor (hours)", 75.0, 125.0), ("Replacement valve", 24.0, 60.0), ("Pipe fitting", 4.0, 12.0),
             ("Diagnostic fee", 49.0, 99.0), ("Filter cartridge", 18.0, 40.0), ("Sealant", 6.0, 14.0)],
}
DATE_FORMATS = ["%Y-%m-%d", "%B %-d, %Y", "%d %b %Y", "%Y/%m/%d", "%b. %-d, %Y"]
TEMPLATES = ["invoice"] * 8 + ["receipt"] * 4 + ["purchase_order"] * 4 + ["work_order"] * 4

PROMPT = (
    "Extract data from this document image. Return only a JSON object with exactly these keys:\n"
    '{"vendor": string, "date": "YYYY-MM-DD", "total": number, '
    '"line_items": [{"description": string, "quantity": number, "unit_price": number, "amount": number}]}\n'
    "- vendor: the business that issued the document or sells the goods (the seller or supplier, not the buyer).\n"
    "- date: the document date, converted to YYYY-MM-DD.\n"
    "- total: the final amount due, after tax, shipping and discounts, as a plain number without currency symbols.\n"
    "No commentary."
)


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    return ImageFont.load_default(size=size)


def _fmt_date(d: dt.date, fmt: str) -> str:
    # `%-d` is not portable to Windows; emulate it.
    return d.strftime(fmt.replace("%-d", str(d.day)))


def _money(x: float) -> str:
    return f"{x:,.2f}"


def _make_items(rng: random.Random, pool: str, n: int) -> list[dict[str, Any]]:
    picks = rng.sample(ITEMS[pool], n)
    out = []
    for desc, lo, hi in picks:
        qty = rng.randint(1, 4 if pool != "default" else 12)
        price = round(rng.uniform(lo, hi), 2)
        out.append({"description": desc, "quantity": qty, "unit_price": price, "amount": round(qty * price, 2)})
    return out


def _draw_items(d: ImageDraw.ImageDraw, items: list[dict[str, Any]], x0: int, y: int, width: int,
                header: tuple[str, str, str, str], font: Any, bold: Any, money: Any = _money) -> int:
    cols = [x0, x0 + int(width * 0.55), x0 + int(width * 0.68), x0 + int(width * 0.84)]
    d.rectangle([x0 - 8, y - 6, x0 + width, y + 26], fill="#e8e8e8")
    for c, h in zip(cols, header):
        d.text((c, y), h, fill="black", font=bold)
    y += 40
    for it in items:
        d.text((cols[0], y), it["description"], fill="black", font=font)
        d.text((cols[1], y), str(it["quantity"]), fill="black", font=font)
        d.text((cols[2], y), money(it["unit_price"]), fill="black", font=font)
        d.text((cols[3], y), money(it["amount"]), fill="black", font=font)
        y += 32
    d.line([x0 - 8, y, x0 + width, y], fill="#888", width=1)
    return y + 16


def _render(kind: str, gt: dict[str, Any], extras: dict[str, Any], path: Path, money: Any = _money,
            font_path: str | None = None) -> None:
    def fnt(size: int) -> Any:
        return ImageFont.truetype(font_path, size) if font_path else _font(size)

    f, fb, fh, fs = fnt(20), fnt(21), fnt(34), fnt(16)
    if kind == "receipt":
        img = Image.new("RGB", (620, 300 + 34 * len(gt["line_items"]) + 260), "white")
        d = ImageDraw.Draw(img)
        y = 30
        for line, font in [(gt["vendor"], fnt(28)), (extras["address"], fs), (f"Tel {extras['phone']}", fs)]:
            w = d.textlength(line, font=font)
            d.text(((620 - w) / 2, y), line, fill="black", font=font)
            y += 40 if font is not fs else 26
        y += 10
        d.text((40, y), f"Date: {extras['date_str']}   {extras['time']}", fill="black", font=f); y += 30
        d.text((40, y), f"Receipt #{extras['number']}", fill="black", font=f); y += 40
        for it in gt["line_items"]:
            left = f"{it['quantity']} x {it['description']} @ {money(it['unit_price'])}"
            d.text((40, y), left, fill="black", font=f)
            d.text((480, y), money(it["amount"]), fill="black", font=f)
            y += 34
        d.line([40, y, 580, y], fill="black"); y += 14
        rows = [("Subtotal", extras["subtotal"]), (f"Tax {extras['tax_rate']}%", extras["tax"]),
                ("TOTAL", gt["total"]), ("Cash", extras["cash"]), ("Change", round(extras["cash"] - gt["total"], 2))]
        for label, val in rows:
            font = fb if label == "TOTAL" else f
            d.text((300, y), label, fill="black", font=font)
            d.text((480, y), money(val), fill="black", font=font)
            y += 32
        d.text((180, y + 20), "Thank you for visiting!", fill="black", font=fs)
        img.save(path, optimize=True)
        return

    img = Image.new("RGB", (1000, 760 + 32 * len(gt["line_items"])), "white")
    d = ImageDraw.Draw(img)
    title = {"invoice": "INVOICE", "purchase_order": "PURCHASE ORDER", "work_order": "WORK ORDER"}[kind]
    if kind == "invoice":
        d.text((50, 40), gt["vendor"], fill="black", font=fh)
        d.text((50, 85), extras["address"], fill="#333", font=fs)
        d.text((50, 107), f"Phone {extras['phone']}", fill="#333", font=fs)
        d.text((720, 40), title, fill="#1b3a6b", font=fh)
        d.text((720, 95), f"Invoice # {extras['number']}", fill="black", font=f)
        d.text((720, 122), f"Date: {extras['date_str']}", fill="black", font=f)
        d.text((720, 149), f"Due: {extras['due_str']}", fill="black", font=f)
        d.text((50, 170), "Bill To:", fill="black", font=fb)
        d.text((50, 197), extras["buyer"], fill="black", font=f)
        y = 260
    elif kind == "purchase_order":
        d.text((50, 40), title, fill="#5a1b1b", font=fh)
        d.text((50, 85), f"Issued by: {extras['buyer']}", fill="black", font=f)
        d.rectangle([50, 125, 480, 225], outline="black")
        d.text((62, 133), "Supplier:", fill="black", font=fb)
        d.text((62, 162), gt["vendor"], fill="black", font=f)
        d.text((62, 190), extras["address"], fill="#333", font=fs)
        d.rectangle([520, 125, 950, 225], outline="black")
        d.text((532, 133), f"PO Number: {extras['number']}", fill="black", font=f)
        d.text((532, 162), f"PO Date: {extras['date_str']}", fill="black", font=f)
        d.text((532, 190), f"Deliver by: {extras['due_str']}", fill="black", font=f)
        y = 260
    else:
        d.text((50, 40), title, fill="#1b5a2a", font=fh)
        d.text((620, 45), f"WO-{extras['number']}", fill="black", font=f)
        d.text((50, 95), "Service provider:", fill="black", font=fb)
        d.text((260, 95), gt["vendor"], fill="black", font=f)
        d.text((50, 125), "Customer:", fill="black", font=fb)
        d.text((260, 125), extras["buyer"], fill="black", font=f)
        d.text((50, 155), "Date of service:", fill="black", font=fb)
        d.text((260, 155), extras["date_str"], fill="black", font=f)
        d.text((50, 185), "Technician:", fill="black", font=fb)
        d.text((260, 185), extras["tech"], fill="black", font=f)
        y = 240
    y = _draw_items(d, gt["line_items"], 58, y, 880, ("Description", "Qty", "Unit Price", "Amount"), f, fb, money)
    rows: list[tuple[str, float]] = [("Subtotal", extras["subtotal"])]
    if extras["discount"]:
        rows.append(("Discount", -extras["discount"]))
    rows.append((f"Tax ({extras['tax_rate']}%)", extras["tax"]))
    if extras["shipping"]:
        rows.append(("Shipping", extras["shipping"]))
    total_label = {"invoice": "TOTAL DUE", "purchase_order": "GRAND TOTAL", "work_order": "AMOUNT DUE"}[kind]
    if extras.get("paid"):
        rows.append(("Total", extras["gross"]))
        rows.append(("Payment received", -extras["paid"]))
        total_label = "BALANCE DUE"
    rows.append((total_label, gt["total"]))
    for label, val in rows:
        font = fb if label == total_label else f
        d.text((600, y), label, fill="black", font=font)
        d.text((820, y), money(val), fill="black", font=font)
        y += 32
    d.text((50, y + 30), extras["note"], fill="#555", font=fs)
    img.save(path, optimize=True)


def build_document_tasks(assets_dir: Path) -> list[dict[str, Any]]:
    """Render the 20 document PNGs into `assets_dir` and return the tasks with ground truth."""
    assets_dir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    tasks: list[dict[str, Any]] = []
    for i, kind in enumerate(TEMPLATES, start=1):
        vendor = VENDORS[i - 1]
        date = dt.date(2026, 1, 1) + dt.timedelta(days=rng.randint(0, 300))
        fmt = DATE_FORMATS[(i - 1) % len(DATE_FORMATS)]
        pool = {"receipt": "receipt", "work_order": "work"}.get(kind, "default")
        items = _make_items(rng, pool, rng.randint(2, 5) if kind != "receipt" else rng.randint(2, 4))
        subtotal = round(sum(it["amount"] for it in items), 2)
        discount = round(subtotal * 0.1, 2) if kind == "work_order" and rng.random() < 0.6 else 0.0
        tax_rate = rng.choice([0, 5, 6.5, 7.25, 8, 8.875, 10])
        tax = round((subtotal - discount) * tax_rate / 100, 2)
        shipping = round(rng.uniform(5, 40), 2) if kind in ("invoice", "purchase_order") and rng.random() < 0.5 else 0.0
        total = round(subtotal - discount + tax + shipping, 2)
        cash = float(int(total // 10 + 1) * 10 + (10 if rng.random() < 0.5 else 0))
        gt = {"vendor": vendor, "date": date.isoformat(), "total": total, "line_items": items}
        extras = {
            "address": f"{rng.randint(10, 9999)} {rng.choice(['Main St', 'Oak Ave', 'Harbor Rd', 'Industrial Pkwy', 'Elm St'])}, "
                       f"{rng.choice(['Springfield, IL', 'Portland, OR', 'Austin, TX', 'Denver, CO', 'Raleigh, NC'])}",
            "phone": f"({rng.randint(200, 989)}) 555-{rng.randint(1000, 9999)}",
            "number": f"{rng.randint(10000, 99999)}",
            "date_str": _fmt_date(date, fmt),
            "due_str": _fmt_date(date + dt.timedelta(days=30), fmt),
            "time": f"{rng.randint(7, 19):02d}:{rng.randint(0, 59):02d}",
            "buyer": rng.choice(BUYERS),
            "tech": rng.choice(["J. Alvarez", "M. Chen", "S. Okafor", "R. Patel"]),
            "subtotal": subtotal, "discount": discount, "tax_rate": tax_rate, "tax": tax,
            "shipping": shipping, "cash": cash,
            "note": rng.choice(["Payment terms: Net 30.", "Thank you for your business.",
                                "Please include the reference number with payment.", "All prices in USD."]),
        }
        name = f"doc-{i:02d}.png"
        _render(kind, gt, extras, assets_dir / name)
        tasks.append({
            "id": f"doc-{i:02d}",
            "category": kind,
            "prompt": PROMPT,
            "image": f"assets/{name}",
            "checker": "document_extraction",
            "max_tokens": DOC_MAX_TOKENS,
            "expected": gt,
        })
    return tasks


def build(suite_dir: Path) -> list[dict[str, Any]]:
    """Suite entry point. Renders the PNGs into `<suite_dir>/assets`."""
    return build_document_tasks(suite_dir / "assets")
