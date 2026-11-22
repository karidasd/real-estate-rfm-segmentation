"""
Real Estate RFM Lead Segmentation (Python)
------------------------------------------
Διαβάζει το CSV των πελατών (sample_crm_leads.csv), εφαρμόζει τη λογική
κατηγοριοποίησης 5 segments, εμφανίζει KPI summary και εξάγει έτοιμες λίστες
CSV ανά segment (με UTF-8 BOM ώστε τα ελληνικά να ανοίγουν σωστά στο Excel)
για στοχευμένα email campaigns.

Χρήση:
    python python/segment_leads.py
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

SEGMENT_ORDER = [
    "Έτοιμος αγοραστής",
    "Νέος ενδιαφερόμενος",
    "Σε σκέψη",
    "Σε ψύξη",
    "Σε νάρκη",
]

SEGMENT_SLUGS = {
    "Έτοιμος αγοραστής": "01_etoimos_agorastis",
    "Νέος ενδιαφερόμενος": "02_neos_endiaferomenos",
    "Σε σκέψη": "03_se_skepsi",
    "Σε ψύξη": "04_se_psyxi",
    "Σε νάρκη": "05_se_narki",
}


def classify_lead(
    days_since_inbound: int,
    signals_count: int,
    has_visit: bool,
    budget: float,
) -> tuple[str, str, bool]:
    """
    Επιστρέφει (segment, reason, at_risk_60d).

    Κανόνες:
      - Έως 60 μέρες & (επίσκεψη Ή 4+ σήματα Ή 2-3 σήματα με budget >= 200.000) -> Έτοιμος αγοραστής
      - Έως 60 μέρες (αλλιώς) -> Νέος ενδιαφερόμενος
      - 61-180 μέρες -> Σε σκέψη
      - 181-365 μέρες -> Σε ψύξη
      - 365+ μέρες -> Σε νάρκη
    """
    if days_since_inbound <= 60:
        is_ready = (
            has_visit
            or signals_count >= 4
            or (2 <= signals_count <= 3 and budget >= 200_000)
        )
        if is_ready:
            reasons = []
            if has_visit:
                reasons.append("έκανε επίσκεψη")
            if signals_count >= 4:
                reasons.append(f"{signals_count} σήματα (4+)")
            if 2 <= signals_count <= 3 and budget >= 200_000:
                reasons.append(f"{signals_count} σήματα + budget {budget:,.0f}€")
            at_risk = days_since_inbound >= 45
            return "Έτοιμος αγοραστής", " & ".join(reasons), at_risk
        return "Νέος ενδιαφερόμενος", "πρόσφατη κίνηση (≤60 μέρες)", False

    if days_since_inbound <= 180:
        return "Σε σκέψη", "αδράνεια 61-180 μέρες", False

    if days_since_inbound <= 365:
        return "Σε ψύξη", "αδράνεια 181-365 μέρες", False

    return "Σε νάρκη", "αδράνεια 365+ μέρες", False


def run_segmentation() -> None:
    base_dir = Path(__file__).resolve().parent.parent
    input_path = base_dir / "data" / "sample_crm_leads.csv"
    output_dir = base_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    with input_path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    enriched_rows = []
    by_segment: dict[str, list[dict]] = defaultdict(list)

    for row in rows:
        days = int(row["days_since_inbound"])
        signals = int(row["signals_count"])
        has_visit = str(row["has_visit"]).strip().lower() in {"1", "true", "yes", "ναι"}
        budget = float(row["budget"])

        segment, reason, at_risk = classify_lead(days, signals, has_visit, budget)

        enriched = {
            **row,
            "segment": segment,
            "segment_reason": reason,
            "at_risk_60d_alert": "ΝΑΙ" if at_risk else "ΟΧΙ",
        }
        enriched_rows.append(enriched)
        by_segment[segment].append(enriched)

    # 1. Εξαγωγή συνολικού αρχείου
    all_output = output_dir / "all_segmented_leads.csv"
    fieldnames = list(enriched_rows[0].keys())
    with all_output.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(enriched_rows)

    # 2. Εξαγωγή ξεχωριστών λιστών ανά segment (για email campaigns)
    for seg in SEGMENT_ORDER:
        seg_rows = by_segment.get(seg, [])
        seg_path = output_dir / f"{SEGMENT_SLUGS[seg]}.csv"
        with seg_path.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(seg_rows)

    # 3. Εκτύπωση KPI Summary
    total = len(enriched_rows)
    print("\n=== REAL ESTATE RFM SEGMENTATION SUMMARY ===")
    print(f"Σύνολο πελατών: {total}\n")
    print(f"{'Segment':<22} | {'Πλήθος':>6} | {'%':>5} | {'Συνολικό Budget':>16} | {'Alert 45-60μ':>12}")
    print("-" * 74)
    for seg in SEGMENT_ORDER:
        seg_rows = by_segment.get(seg, [])
        count = len(seg_rows)
        pct = (count / total * 100) if total else 0
        total_budget = sum(float(r["budget"]) for r in seg_rows)
        alerts = sum(1 for r in seg_rows if r["at_risk_60d_alert"] == "ΝΑΙ")
        print(f"{seg:<22} | {count:>6} | {pct:>4.1f}% | {total_budget:>14,.0f} € | {alerts:>12}")

    print(f"\nΤα αρχεία για email campaigns αποθηκεύτηκαν στον φάκελο: {output_dir}\n")


if __name__ == "__main__":
    run_segmentation()
