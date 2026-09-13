"""Generate deterministic synthetic ticket-resale listings for demonstration."""

from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path


FIELDS = [
    "listing_id", "seller_account_age_days", "completed_sales",
    "complaint_rate", "price_ratio_to_face_value", "off_platform_payment",
    "transfer_proof", "vip_claimed", "vip_transfer_confirmed",
    "seller_rating", "refund_policy", "urgent_pressure", "label_is_risky",
]


def generate_row(index: int, rng: random.Random) -> dict[str, object]:
    """Create one synthetic listing with a noisy reference label."""
    suspicious = rng.random() < 0.30
    vip = rng.random() < 0.28
    if suspicious:
        row = {
            "seller_account_age_days": rng.randint(2, 120),
            "completed_sales": rng.randint(0, 8),
            "complaint_rate": round(rng.uniform(0.08, 0.38), 3),
            "price_ratio_to_face_value": round(rng.choice([
                rng.uniform(0.30, 0.70), rng.uniform(1.25, 2.20)
            ]), 2),
            "off_platform_payment": rng.random() < 0.65,
            "transfer_proof": rng.random() < 0.35,
            "seller_rating": round(rng.uniform(1.8, 4.1), 1),
            "refund_policy": rng.random() < 0.25,
            "urgent_pressure": rng.random() < 0.70,
        }
    else:
        row = {
            "seller_account_age_days": rng.randint(120, 2400),
            "completed_sales": rng.randint(5, 180),
            "complaint_rate": round(rng.uniform(0.00, 0.10), 3),
            "price_ratio_to_face_value": round(rng.uniform(0.75, 1.50), 2),
            "off_platform_payment": rng.random() < 0.06,
            "transfer_proof": rng.random() < 0.92,
            "seller_rating": round(rng.uniform(3.7, 5.0), 1),
            "refund_policy": rng.random() < 0.85,
            "urgent_pressure": rng.random() < 0.10,
        }
    row.update({
        "listing_id": f"L{index:04d}",
        "vip_claimed": vip,
        "vip_transfer_confirmed": vip and (rng.random() < (0.25 if suspicious else 0.90)),
        "label_is_risky": suspicious,
    })
    return row


def generate_file(path: str | Path, rows: int, seed: int = 20260913) -> None:
    """Write a reproducible synthetic CSV dataset."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    with path.open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(generate_row(i, rng) for i in range(1, rows + 1))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=int, default=250)
    parser.add_argument("--output", default="data/sample_listings.csv")
    args = parser.parse_args()
    if args.rows <= 0:
        raise ValueError("--rows must be positive")
    generate_file(args.output, args.rows)
    print(f"generated {args.rows} rows at {args.output}")


if __name__ == "__main__":
    main()

