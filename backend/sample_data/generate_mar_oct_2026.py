"""Generate fake shop daily sales: 2026-03-01 → 2026-10-31."""

from __future__ import annotations

import math
import random
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

random.seed(20260301)

WD = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
BASE = {
    0: 95,  # Mon
    1: 112,  # Tue
    2: 120,  # Wed
    3: 115,  # Thu
    4: 158,  # Fri
    5: 175,  # Sat
    6: 82,  # Sun
}
MONTH_MULT = {
    3: 0.88,
    4: 0.95,
    5: 1.02,
    6: 1.08,
    7: 1.12,
    8: 1.10,
    9: 0.92,
    10: 1.00,
}

start = date(2026, 3, 1)
end = date(2026, 10, 31)

rows: list[tuple[str, float, date]] = []
d = start
while d <= end:
    if random.random() < 0.06:
        d += timedelta(days=1)
        continue

    base = BASE[d.weekday()] * MONTH_MULT[d.month]
    noise = random.gauss(0, 0.14)
    val = base * (1 + noise)

    roll = random.random()
    if roll < 0.04:
        val *= random.uniform(0.15, 0.45)
    elif roll < 0.07:
        val *= random.uniform(1.8, 3.2)

    wave = 1 + 0.04 * math.sin(d.toordinal() / 11.0)
    val *= wave
    val = max(12.0, round(val, 2))

    label = f"{d.month}/{d.day}/{d.year} ({WD[d.weekday()]})"
    rows.append((label, val, d))
    d += timedelta(days=1)

out_dir = Path(__file__).resolve().parent
csv_path = out_dir / "fake_shop_mar_oct_2026.csv"
xlsx_path = out_dir / "fake_shop_mar_oct_2026.xlsx"

with csv_path.open("w", encoding="utf-8", newline="") as f:
    f.write("Date,Total\n")
    for label, val, _ in rows:
        f.write(f"{label},{val}\n")

import pandas as pd

df = pd.DataFrame({"Date": [r[0] for r in rows], "Total": [r[1] for r in rows]})
df.to_excel(xlsx_path, index=False)

desk = Path.home() / "Desktop"
if desk.exists():
    for p in (csv_path, xlsx_path):
        (desk / p.name).write_bytes(p.read_bytes())

by_m: dict[int, list] = defaultdict(lambda: [0.0, 0])
for _, val, dd in rows:
    by_m[dd.month][0] += val
    by_m[dd.month][1] += 1

print(f"days={len(rows)}  range={rows[0][2]} -> {rows[-1][2]}")
print(f"total={sum(r[1] for r in rows):.2f}  mean={sum(r[1] for r in rows) / len(rows):.2f}")
print("monthly:")
for m in range(3, 11):
    s, n = by_m[m]
    print(f"  {m:02d}: days={n:3d}  sum={s:9.2f}  avg={s / n if n else 0:7.2f}")
print("csv:", csv_path)
print("xlsx:", xlsx_path)
