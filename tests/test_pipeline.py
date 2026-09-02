"""Regression checks for the Fusion21 ETL pipeline."""

from __future__ import annotations

import unittest

from data_loader import load_processed_data as load_app_data
from pipeline import load_processed_data, validate


class PipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = load_processed_data()

    def test_public_metrics_cover_three_indicators_and_nine_regions(self) -> None:
        latest = self.data["latest"]
        self.assertEqual(len(latest), 27)
        counts = latest.groupby("indicator_id")["area_code"].nunique()
        self.assertTrue(counts.eq(9).all())

    def test_contract_value_is_not_a_contribution_component(self) -> None:
        summary = self.data["fusion21_synthetic"]["region_summary"]
        self.assertNotIn("procurement_score", summary.columns)
        expected = (summary["activity_score"] + summary["foundation_score"]) / 2
        difference = (summary["contribution_score"] - expected).abs()
        self.assertTrue(difference.le(0.11).all())

    def test_all_regions_are_available_to_the_map(self) -> None:
        summary = self.data["fusion21_synthetic"]["region_summary"]
        self.assertEqual(len(summary), 9)
        self.assertEqual(summary["area_code"].nunique(), 9)

    def test_pipeline_validator_accepts_current_outputs(self) -> None:
        transformed = {
            "latest": self.data["latest"],
            "fusion21_synthetic": self.data["fusion21_synthetic"],
        }
        validate(transformed)

    def test_lightweight_app_loader_reads_current_outputs(self) -> None:
        app_data = load_app_data()
        self.assertEqual(len(app_data["latest"]), 27)
        self.assertEqual(
            len(app_data["fusion21_synthetic"]["region_summary"]), 9
        )


if __name__ == "__main__":
    unittest.main()
