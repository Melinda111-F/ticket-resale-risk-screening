"""Unit tests for the ticket resale risk engine."""

import csv
import tempfile
import unittest
from pathlib import Path

from ticket_risk import assess_listing, parse_bool, screen_file


def safe_listing() -> dict[str, str]:
    return {
        "listing_id": "L0001",
        "seller_account_age_days": "800",
        "completed_sales": "75",
        "complaint_rate": "0.01",
        "price_ratio_to_face_value": "1.1",
        "off_platform_payment": "false",
        "transfer_proof": "true",
        "vip_claimed": "false",
        "vip_transfer_confirmed": "false",
        "seller_rating": "4.8",
        "refund_policy": "true",
        "urgent_pressure": "false",
        "label_is_risky": "false",
    }


class TestRiskAssessment(unittest.TestCase):
    def test_safe_listing_is_low_risk(self) -> None:
        result = assess_listing(safe_listing())
        self.assertEqual((result.score, result.level), (0, "Low"))

    def test_multiple_warning_signals_are_high_risk(self) -> None:
        row = safe_listing()
        row.update({
            "off_platform_payment": "true",
            "complaint_rate": "0.25",
            "transfer_proof": "false",
            "urgent_pressure": "true",
        })
        result = assess_listing(row)
        self.assertEqual(result.level, "High")
        self.assertGreaterEqual(len(result.reasons), 4)

    def test_unconfirmed_vip_claim_adds_risk(self) -> None:
        row = safe_listing()
        row.update({"vip_claimed": "true", "vip_transfer_confirmed": "false"})
        result = assess_listing(row)
        self.assertEqual(result.score, 15)

    def test_score_is_capped_at_100(self) -> None:
        row = safe_listing()
        row.update({
            "seller_account_age_days": "1", "completed_sales": "0",
            "complaint_rate": "0.5", "price_ratio_to_face_value": "0.2",
            "off_platform_payment": "true", "transfer_proof": "false",
            "vip_claimed": "true", "vip_transfer_confirmed": "false",
            "seller_rating": "1", "refund_policy": "false",
            "urgent_pressure": "true",
        })
        self.assertEqual(assess_listing(row).score, 100)

    def test_invalid_rate_is_rejected(self) -> None:
        row = safe_listing()
        row["complaint_rate"] = "1.2"
        with self.assertRaises(ValueError):
            assess_listing(row)

    def test_invalid_boolean_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            parse_bool("sometimes")

    def test_file_pipeline_counts_rejected_rows(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "input.csv"
            target = Path(directory) / "output.csv"
            good = safe_listing()
            bad = safe_listing()
            bad.update({"listing_id": "L0002", "seller_rating": "unknown"})
            with source.open("w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=good.keys())
                writer.writeheader()
                writer.writerows([good, bad])
            counts = screen_file(source, target)
            self.assertEqual(counts["processed"], 1)
            self.assertEqual(counts["rejected"], 1)


if __name__ == "__main__":
    unittest.main()

