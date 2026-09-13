"""Explainable risk screening for synthetic concert-ticket resale listings."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path


REQUIRED_FIELDS = {
    "listing_id",
    "seller_account_age_days",
    "completed_sales",
    "complaint_rate",
    "price_ratio_to_face_value",
    "off_platform_payment",
    "transfer_proof",
    "vip_claimed",
    "vip_transfer_confirmed",
    "seller_rating",
    "refund_policy",
    "urgent_pressure",
}


@dataclass(frozen=True)
class RiskAssessment:
    """Result of screening one listing."""

    score: int
    level: str
    reasons: tuple[str, ...]


def parse_bool(value: str) -> bool:
    """Convert a common CSV boolean representation to bool."""
    normalized = value.strip().lower()
    if normalized in {"true", "1", "yes", "y"}:
        return True
    if normalized in {"false", "0", "no", "n"}:
        return False
    raise ValueError(f"invalid boolean value: {value!r}")


def _number(row: dict[str, str], field: str, lower: float,
            upper: float | None = None) -> float:
    """Read and validate one numeric field."""
    try:
        value = float(row[field])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be numeric") from exc
    if value < lower or (upper is not None and value > upper):
        bound = f"[{lower}, {upper}]" if upper is not None else f">= {lower}"
        raise ValueError(f"{field} must be {bound}")
    return value


def validate_listing(row: dict[str, str]) -> None:
    """Raise ValueError when a listing has missing or invalid data."""
    missing = REQUIRED_FIELDS.difference(row)
    if missing:
        raise ValueError(f"missing fields: {', '.join(sorted(missing))}")
    if not row["listing_id"].strip():
        raise ValueError("listing_id cannot be blank")

    _number(row, "seller_account_age_days", 0)
    _number(row, "completed_sales", 0)
    _number(row, "complaint_rate", 0, 1)
    _number(row, "price_ratio_to_face_value", 0)
    _number(row, "seller_rating", 0, 5)
    for field in (
        "off_platform_payment", "transfer_proof", "vip_claimed",
        "vip_transfer_confirmed", "refund_policy", "urgent_pressure"
    ):
        parse_bool(row[field])


def assess_listing(row: dict[str, str]) -> RiskAssessment:
    """Return an explainable rule-based risk assessment for one listing."""
    validate_listing(row)
    score = 0
    reasons: list[str] = []

    age = _number(row, "seller_account_age_days", 0)
    sales = _number(row, "completed_sales", 0)
    complaints = _number(row, "complaint_rate", 0, 1)
    price_ratio = _number(row, "price_ratio_to_face_value", 0)
    rating = _number(row, "seller_rating", 0, 5)
    off_platform = parse_bool(row["off_platform_payment"])
    transfer_proof = parse_bool(row["transfer_proof"])
    vip_claimed = parse_bool(row["vip_claimed"])
    vip_confirmed = parse_bool(row["vip_transfer_confirmed"])
    refund_policy = parse_bool(row["refund_policy"])
    urgent_pressure = parse_bool(row["urgent_pressure"])

    def add(points: int, reason: str) -> None:
        nonlocal score
        score += points
        reasons.append(reason)

    if off_platform:
        add(25, "seller requests off-platform payment")
    if complaints >= 0.20:
        add(22, "complaint rate is at least 20%")
    elif complaints >= 0.10:
        add(12, "complaint rate is between 10% and 20%")
    if price_ratio < 0.60:
        add(18, "price is below 60% of face value")
    elif price_ratio > 1.75:
        add(8, "price is above 175% of face value")
    if age < 30:
        add(15, "seller account is less than 30 days old")
    elif age < 90:
        add(8, "seller account is less than 90 days old")
    if sales < 3:
        add(8, "seller has fewer than three completed sales")
    if not transfer_proof:
        add(12, "no transfer proof was provided")
    if vip_claimed and not vip_confirmed:
        add(15, "VIP benefits are claimed but transfer is unconfirmed")
    if rating < 3.5:
        add(10, "seller rating is below 3.5")
    if not refund_policy:
        add(7, "no refund policy is offered")
    if urgent_pressure:
        add(8, "seller is applying urgency pressure")

    score = min(score, 100)
    level = "High" if score >= 50 else "Medium" if score >= 25 else "Low"
    return RiskAssessment(score, level, tuple(reasons))


def screen_file(input_path: str | Path, output_path: str | Path) -> dict[str, int]:
    """Screen a CSV file, write valid results, and return processing counts."""
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    counts = {"processed": 0, "rejected": 0, "low": 0, "medium": 0, "high": 0}

    with input_path.open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames is None:
            raise ValueError("input CSV requires a header")
        missing = REQUIRED_FIELDS.difference(reader.fieldnames)
        if missing:
            raise ValueError(f"missing CSV columns: {', '.join(sorted(missing))}")
        output_fields = list(reader.fieldnames) + ["risk_score", "risk_level", "risk_reasons"]
        with output_path.open("w", newline="", encoding="utf-8") as target:
            writer = csv.DictWriter(target, fieldnames=output_fields)
            writer.writeheader()
            for row in reader:
                try:
                    result = assess_listing(row)
                except ValueError:
                    counts["rejected"] += 1
                    continue
                output = dict(row)
                output.update({
                    "risk_score": result.score,
                    "risk_level": result.level,
                    "risk_reasons": "; ".join(result.reasons) or "no material risk signals",
                })
                writer.writerow(output)
                counts["processed"] += 1
                counts[result.level.lower()] += 1
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_csv")
    parser.add_argument("output_csv")
    args = parser.parse_args()
    counts = screen_file(args.input_csv, args.output_csv)
    print(", ".join(f"{key}={value}" for key, value in counts.items()))


if __name__ == "__main__":
    main()

