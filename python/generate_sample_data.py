"""
Δημιουργία συνθετικού (εικονικού) dataset Real Estate CRM για εκπαιδευτική χρήση.
Παράγει δύο αρχεία στο ../data/:
  1. sample_crm_leads.csv       (150 πελάτες - έτοιμο για το Web App & quick analysis)
  2. sample_interactions.csv    (αναλυτικό ιστορικό inbound/outbound επικοινωνιών για SQL)
"""

from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path

RANDOM_SEED = 42
REFERENCE_DATE = date(2026, 11, 22)

FIRST_NAMES = [
    "Γιώργος", "Μαρία", "Νίκος", "Ελένη", "Κώστας", "Κατερίνα", "Δημήτρης",
    "Σοφία", "Παναγιώτης", "Άννα", "Βασίλης", "Χριστίνα", "Αλέξανδρος",
    "Δήμητρα", "Μιχάλης", "Ιωάννα", "Θανάσης", "Αγγελική", "Σπύρος", "Εύα",
    "Αντώνης", "Όλγα", "Χρήστος", "Μαρίνα", "Στέφανος", "Ναταλία", "Λευτέρης",
    "Βίκυ", "Πέτρος", "Δέσποινα",
]

LAST_NAMES = [
    "Παπαδόπουλος", "Γεωργίου", "Νικολάου", "Δημητρίου", "Κωνσταντίνου",
    "Οικονόμου", "Βασιλείου", "Αντωνίου", "Πετρίδης", "Αθανασίου",
    "Καραγιάννης", "Μακρής", "Σταματίου", "Θεοδωρίδης", "Χριστοδούλου",
    "Αλεξίου", "Παππάς", "Κυριακίδης", "Σαμαράς", "Τσιώλης",
    "Μανώλης", "Καλογερόπουλος", "Λαμπρόπουλος", "Ζαχαρίου", "Μιχαηλίδης",
]

AREAS = [
    "Γλυφάδα", "Κηφισιά", "Χαλάνδρι", "Αγία Παρασκευή", "Παλαιό Φάληρο",
    "Νέα Σμύρνη", "Μαρούσι", "Βούλα", "Παγκράτι", "Κολωνάκι",
    "Αμπελόκηποι", "Ζωγράφου", "Ηλιούπολη", "Άλιμος", "Περιστέρι",
]

PROPERTY_TYPES = ["Διαμέρισμα", "Μεζονέτα", "Μονοκατοικία", "Οικόπεδο", "Επενδυτικό"]
SOURCES = ["Spitogatos", "Xe.gr", "Website", "Instagram Ads", "Σύσταση", "Τηλέφωνο"]


def generate_dataset() -> None:
    rng = random.Random(RANDOM_SEED)
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    leads_rows = []
    interactions_rows = []
    interaction_id = 1001

    # Κατανομή προφίλ για ρεαλιστική εικόνα CRM (σύνολο 150 πελάτες)
    profiles = (
        ["ready_visit"] * 18
        + ["ready_signals"] * 12
        + ["ready_budget"] * 12
        + ["ready_at_risk"] * 10   # 46–59 μέρες (alert πριν πέσουν «Σε σκέψη»)
        + ["new_lead"] * 28
        + ["thinking"] * 30
        + ["cold"] * 22
        + ["dormant"] * 18
    )
    rng.shuffle(profiles)

    for idx, profile in enumerate(profiles, start=1):
        lead_id = f"LD-{idx:04d}"
        full_name = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"
        email = f"client{idx:03d}@example-realestate.gr"
        area = rng.choice(AREAS)
        prop_type = rng.choice(PROPERTY_TYPES)
        source = rng.choice(SOURCES)

        if profile == "ready_visit":
            days_since_inbound = rng.randint(1, 44)
            signals = rng.randint(1, 5)
            has_visit = 1
            budget = rng.choice([140000, 180000, 220000, 280000, 350000, 450000])
        elif profile == "ready_signals":
            days_since_inbound = rng.randint(2, 44)
            signals = rng.randint(4, 8)
            has_visit = 0
            budget = rng.choice([120000, 150000, 180000, 210000, 260000])
        elif profile == "ready_budget":
            days_since_inbound = rng.randint(3, 44)
            signals = rng.randint(2, 3)
            has_visit = 0
            budget = rng.choice([200000, 240000, 300000, 380000, 520000])
        elif profile == "ready_at_risk":
            days_since_inbound = rng.randint(46, 59)
            has_visit = rng.choice([0, 1])
            signals = rng.randint(4, 6) if not has_visit else rng.randint(2, 4)
            budget = rng.choice([190000, 220000, 270000, 340000])
        elif profile == "new_lead":
            days_since_inbound = rng.randint(1, 58)
            has_visit = 0
            signals = rng.randint(1, 3)
            # Για να μην πληροί το κριτήριο «Έτοιμος» με 2-3 σήματα + budget >= 200k
            if signals >= 2:
                budget = rng.choice([95000, 120000, 145000, 175000, 190000])
            else:
                budget = rng.choice([110000, 160000, 210000, 290000])
        elif profile == "thinking":
            days_since_inbound = rng.randint(61, 179)
            signals = rng.randint(1, 5)
            has_visit = rng.choice([0, 0, 1])
            budget = rng.choice([130000, 170000, 220000, 280000, 360000])
        elif profile == "cold":
            days_since_inbound = rng.randint(181, 364)
            signals = rng.randint(1, 4)
            has_visit = rng.choice([0, 0, 0, 1])
            budget = rng.choice([120000, 165000, 210000, 260000])
        else:  # dormant
            days_since_inbound = rng.randint(366, 620)
            signals = rng.randint(1, 3)
            has_visit = rng.choice([0, 0, 0, 1])
            budget = rng.choice([110000, 150000, 200000, 250000])

        last_inbound_date = REFERENCE_DATE - timedelta(days=days_since_inbound)

        leads_rows.append(
            {
                "lead_id": lead_id,
                "full_name": full_name,
                "email": email,
                "area": area,
                "property_type": prop_type,
                "source": source,
                "budget": budget,
                "signals_count": signals,
                "has_visit": has_visit,
                "last_inbound_date": last_inbound_date.isoformat(),
                "days_since_inbound": days_since_inbound,
            }
        )

        # Δημιουργία ιστορικού επικοινωνιών (inbound + outbound follow-ups)
        # Έτσι φαίνεται στην SQL γιατί το WHERE direction = 'inbound' είναι κρίσιμο!
        for s in range(signals):
            offset = 0 if s == 0 else rng.randint(1, 45)
            event_date = last_inbound_date - timedelta(days=offset)
            event_type = "property_visit" if (has_visit and s == 0) else rng.choice(
                ["inquiry_form", "inbound_call", "whatsapp_message", "email_reply"]
            )
            interactions_rows.append(
                {
                    "interaction_id": f"INT-{interaction_id}",
                    "lead_id": lead_id,
                    "event_date": event_date.isoformat(),
                    "direction": "inbound",
                    "event_type": event_type,
                }
            )
            interaction_id += 1

        # Προσθήκη outbound follow-ups από το γραφείο (ακόμα και πρόσφατα σε ανενεργούς!)
        outbound_count = rng.randint(1, 3)
        for _ in range(outbound_count):
            outbound_days_ago = rng.randint(1, max(2, min(days_since_inbound, 90)))
            out_date = REFERENCE_DATE - timedelta(days=outbound_days_ago)
            interactions_rows.append(
                {
                    "interaction_id": f"INT-{interaction_id}",
                    "lead_id": lead_id,
                    "event_date": out_date.isoformat(),
                    "direction": "outbound",
                    "event_type": rng.choice(["agent_call", "newsletter_sent", "followup_email"]),
                }
            )
            interaction_id += 1

    leads_path = data_dir / "sample_crm_leads.csv"
    with leads_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(leads_rows[0].keys()))
        writer.writeheader()
        writer.writerows(leads_rows)

    interactions_path = data_dir / "sample_interactions.csv"
    with interactions_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(interactions_rows[0].keys()))
        writer.writeheader()
        writer.writerows(interactions_rows)

    print(f"Created {len(leads_rows)} leads -> {leads_path}")
    print(f"Created {len(interactions_rows)} interactions -> {interactions_path}")


if __name__ == "__main__":
    generate_dataset()
