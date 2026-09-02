"""Lightweight reader for the application-ready Fusion21 data files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parent
PROCESSED_DIR = ROOT / "data" / "processed"
RAW_DIR = ROOT / "data" / "raw"
GEOGRAPHY_RAW_DIR = RAW_DIR / "geography"
SYNTHETIC_RAW_DIR = RAW_DIR / "fusion21_synthetic"


def load_processed_data() -> dict[str, Any]:
    """Load packaged outputs without importing the full ETL pipeline."""

    paths = {
        "latest": PROCESSED_DIR / "metrics_latest.csv",
        "timeseries": PROCESSED_DIR / "metrics_timeseries.csv",
        "projects": PROCESSED_DIR / "fusion21_projects_synthetic.csv",
        "region_summary": PROCESSED_DIR / "fusion21_region_summary_synthetic.csv",
        "map_metrics": PROCESSED_DIR / "fusion21_map_metrics_synthetic.csv",
        "contracts": SYNTHETIC_RAW_DIR / "fusion21_contracts_synthetic.csv",
        "activities": SYNTHETIC_RAW_DIR
        / "fusion21_social_value_activities_synthetic.csv",
        "foundation": SYNTHETIC_RAW_DIR
        / "fusion21_foundation_payments_synthetic.csv",
        "lad_boundary": GEOGRAPHY_RAW_DIR / "lad_2019_boundaries.geojson",
        "region_boundary": GEOGRAPHY_RAW_DIR / "rgn_2019_boundaries.geojson",
    }
    missing = [str(path) for path in paths.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(
            "Application-ready data is incomplete: " + ", ".join(missing)
        )

    latest = pd.read_csv(paths["latest"])
    required_indicators = {
        "imd2019_need",
        "unemployment_rate_lfs",
        "social_need_composite",
    }
    if set(latest["indicator_id"]) != required_indicators:
        raise ValueError("Processed public metrics do not contain the expected indicators.")
    if not latest.groupby("indicator_id")["area_code"].nunique().eq(9).all():
        raise ValueError("Each public indicator must cover all nine English regions.")

    region_summary = pd.read_csv(paths["region_summary"])
    required_contribution_columns = {
        "activity_possible_count",
        "activity_score",
        "foundation_score",
        "contribution_score",
    }
    if not required_contribution_columns.issubset(region_summary.columns):
        raise ValueError("Processed contribution data uses an outdated schema.")

    return {
        "latest": latest,
        "timeseries": pd.read_csv(paths["timeseries"], parse_dates=["period_start"]),
        "boundaries": {
            "lad_2019": json.loads(paths["lad_boundary"].read_text(encoding="utf-8")),
            "rgn_2019": json.loads(
                paths["region_boundary"].read_text(encoding="utf-8")
            ),
        },
        "fusion21_synthetic": {
            "contracts": pd.read_csv(paths["contracts"]),
            "activities": pd.read_csv(paths["activities"]),
            "foundation": pd.read_csv(paths["foundation"]),
            "projects": pd.read_csv(paths["projects"]),
            "region_summary": region_summary,
            "map_metrics": pd.read_csv(paths["map_metrics"]),
        },
    }
