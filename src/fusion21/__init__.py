"""Fusion21 social need mapping prototype.

这个文件现在把原来的 config.py、data_sources.py、data_cleaning.py
和 data_pipeline.py 合并到一起。这样代码文件更少，但仍然保留清晰分段。

This file now combines the old config.py, data_sources.py, data_cleaning.py
and data_pipeline.py. The project has fewer code files, while the sections
below still keep the workflow understandable.
"""

from __future__ import annotations

import json
from io import StringIO
from pathlib import Path
from random import Random
from typing import Any

import pandas as pd
import requests


# ---------------------------------------------------------------------------
# 1. 基础配置 / Basic configuration
# ---------------------------------------------------------------------------
# 中文：这里集中放项目路径、数据文件路径和官方数据网址。
# English: This section stores project paths, data file paths, and official
# source URLs.

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
SYNTHETIC_DIR = ROOT / "data" / "synthetic"

IMD_FILE_1_XLSX = RAW_DIR / "File_1_-_IMD2019_Index_of_Multiple_Deprivation.xlsx"
IMD_FILE_7_CSV = (
    RAW_DIR
    / "File_7_-_All_IoD2019_Scores_Ranks_Deciles_and_Population_Denominators.csv"
)

IMD_FILE_7_URL = (
    "https://assets.publishing.service.gov.uk/media/5dc407b440f0b6379a7acc8d/"
    "File_7_-_All_IoD2019_Scores__Ranks__Deciles_and_Population_Denominators_3.csv"
)

NOMIS_REGIONAL_LABOUR_MARKET_URL = (
    "https://www.nomisweb.co.uk/api/v01/dataset/NM_59_1.data.csv"
)

HEADERS = {
    "User-Agent": "Fusion21 social need mapping prototype; student research",
    "Accept": "application/json,text/csv,*/*",
}

ONS_LAD_2019_FEATURESERVER = (
    "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/"
    "Local_Authority_Districts_December_2019_GCB_UK_2022/FeatureServer/0/query"
)

ONS_REGION_2019_FEATURESERVER = (
    "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/"
    "Regions_December_2019_General_Clipped_Boundaries_EN_2022/FeatureServer/0/query"
)

ONS_LAD_TO_REGION_2019_FEATURESERVER = (
    "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/"
    "LAD19_RGN19_EN_LU_948748b0eaa54fe888a604b126f5e672/FeatureServer/0/query"
)

TARGET_GEOGRAPHY = "rgn_2019"

IMD_INDICATOR = "imd2019_need"
UNEMPLOYMENT_INDICATOR = "unemployment_rate_lfs"
COMPOSITE_NEED_INDICATOR = "social_need_composite"

ENGLISH_REGION_NAMES = {
    "E12000001": "North East",
    "E12000002": "North West",
    "E12000003": "Yorkshire and The Humber",
    "E12000004": "East Midlands",
    "E12000005": "West Midlands",
    "E12000006": "East of England",
    "E12000007": "London",
    "E12000008": "South East",
    "E12000009": "South West",
}

COMMON_METRIC_COLUMNS = [
    "indicator_id",
    "indicator_label",
    "area_code",
    "area_name",
    "value",
    "unit",
    "period",
    "source",
    "source_url",
    "geography",
    "feature_id_key",
    "indicator_group",
    "value_direction",
    "interpretation",
    "aggregation_method",
]

SYNTHETIC_ACTIVITY_COLUMNS = [
    (
        "Taken steps to reduce carbon emissions or incorporate renewable energy "
        "into your operations? (e.g. switching to electric vehicles)",
        "Decarbonisation",
    ),
    (
        "Taken steps to reduce waste e.g. supporting community-level recycling",
        "Waste reduction",
    ),
    (
        "Implemented measures to reduce water consumption? "
        "(e.g. rainwater harvesting)",
        "Water reduction",
    ),
    (
        "Protected local ecosystems? "
        "(e.g. by planting trees, creating green spaces)",
        "Local ecosystems",
    ),
    (
        "Actively engaged with local communities/schools/colleges to promote "
        "the benefits of renewable energy?",
        "Community engagement",
    ),
    (
        "Delivered training initiatives that upskills existing members of staff "
        "around sustainability/green skills?",
        "Green skills",
    ),
]

SYNTHETIC_REGION_PROFILES = [
    {
        "region_code": "E12000001",
        "region_name": "North East",
        "local_authority_code": "E08000021",
        "local_authority_name": "Newcastle upon Tyne",
        "delivery_postcode": "NE1 1AA",
        "latitude": 54.9783,
        "longitude": -1.6178,
        "contract_count": 3,
        "activity_probability": 0.38,
        "contract_value_range": (900_000, 3_600_000),
    },
    {
        "region_code": "E12000002",
        "region_name": "North West",
        "local_authority_code": "E08000003",
        "local_authority_name": "Manchester",
        "delivery_postcode": "M1 1AE",
        "latitude": 53.4808,
        "longitude": -2.2426,
        "contract_count": 6,
        "activity_probability": 0.65,
        "contract_value_range": (1_500_000, 6_800_000),
    },
    {
        "region_code": "E12000003",
        "region_name": "Yorkshire and The Humber",
        "local_authority_code": "E08000035",
        "local_authority_name": "Leeds",
        "delivery_postcode": "LS1 1UR",
        "latitude": 53.8008,
        "longitude": -1.5491,
        "contract_count": 3,
        "activity_probability": 0.42,
        "contract_value_range": (1_000_000, 4_200_000),
    },
    {
        "region_code": "E12000004",
        "region_name": "East Midlands",
        "local_authority_code": "E06000018",
        "local_authority_name": "Nottingham",
        "delivery_postcode": "NG1 1AA",
        "latitude": 52.9548,
        "longitude": -1.1581,
        "contract_count": 4,
        "activity_probability": 0.55,
        "contract_value_range": (1_100_000, 5_000_000),
    },
    {
        "region_code": "E12000005",
        "region_name": "West Midlands",
        "local_authority_code": "E08000025",
        "local_authority_name": "Birmingham",
        "delivery_postcode": "B1 1BB",
        "latitude": 52.4862,
        "longitude": -1.8904,
        "contract_count": 6,
        "activity_probability": 0.72,
        "contract_value_range": (1_500_000, 7_500_000),
    },
    {
        "region_code": "E12000006",
        "region_name": "East of England",
        "local_authority_code": "E07000008",
        "local_authority_name": "Cambridge",
        "delivery_postcode": "CB1 1BH",
        "latitude": 52.2053,
        "longitude": 0.1218,
        "contract_count": 5,
        "activity_probability": 0.60,
        "contract_value_range": (1_400_000, 6_400_000),
    },
    {
        "region_code": "E12000007",
        "region_name": "London",
        "local_authority_code": "E09000001",
        "local_authority_name": "City of London",
        "delivery_postcode": "EC1A 1BB",
        "latitude": 51.5074,
        "longitude": -0.1278,
        "contract_count": 7,
        "activity_probability": 0.68,
        "contract_value_range": (2_000_000, 9_500_000),
    },
    {
        "region_code": "E12000008",
        "region_name": "South East",
        "local_authority_code": "E07000209",
        "local_authority_name": "Guildford",
        "delivery_postcode": "GU1 1AA",
        "latitude": 51.2362,
        "longitude": -0.5704,
        "contract_count": 7,
        "activity_probability": 0.72,
        "contract_value_range": (1_800_000, 8_200_000),
    },
    {
        "region_code": "E12000009",
        "region_name": "South West",
        "local_authority_code": "E06000023",
        "local_authority_name": "Bristol, City of",
        "delivery_postcode": "BS1 1AA",
        "latitude": 51.4545,
        "longitude": -2.5879,
        "contract_count": 4,
        "activity_probability": 0.58,
        "contract_value_range": (1_100_000, 5_300_000),
    },
]


def ensure_directories() -> None:
    """确保数据文件夹存在 / Make sure the data folders exist."""

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    SYNTHETIC_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# 2. 原始数据读取和下载 / Raw data loading and downloading
# ---------------------------------------------------------------------------
# 中文：这里负责读取或下载 public data，包括 IMD File 7、ONS 边界数据、
# local authority 到 English region 的 lookup。
# English: This section reads or downloads public data, including IMD File 7,
# ONS boundary data, and the LAD-to-region lookup.

LSOA_CODE = "LSOA code (2011)"
LAD_CODE = "Local Authority District code (2019)"
LAD_NAME = "Local Authority District name (2019)"
IMD_SCORE = "Index of Multiple Deprivation (IMD) Score"
IMD_RANK = "Index of Multiple Deprivation (IMD) Rank (where 1 is most deprived)"
IMD_DECILE = (
    "Index of Multiple Deprivation (IMD) Decile "
    "(where 1 is most deprived 10% of LSOAs)"
)
TOTAL_POPULATION = "Total population: mid 2015 (excluding prisoners)"


def _get_json(url: str, params: dict[str, Any], timeout: int = 60) -> dict[str, Any]:
    """从 API 获取 JSON / Fetch JSON data from an API."""

    response = requests.get(url, params=params, headers=HEADERS, timeout=timeout)
    response.raise_for_status()
    return response.json()


def _download_file(url: str, output_path: Path, force: bool = False) -> Path:
    """下载文件并缓存 / Download a file and cache it locally."""

    if output_path.exists() and not force:
        return output_path

    response = requests.get(url, headers=HEADERS, timeout=120)
    response.raise_for_status()
    output_path.write_bytes(response.content)
    return output_path


def _download_geojson(
    url: str,
    out_fields: str,
    output_path: Path,
    force: bool = False,
) -> dict[str, Any]:
    """下载或读取地图边界 GeoJSON / Download or load boundary GeoJSON."""

    if output_path.exists() and not force:
        return json.loads(output_path.read_text(encoding="utf-8"))

    geojson = _get_json(
        url,
        {
            "where": "1=1",
            "outFields": out_fields,
            "returnGeometry": "true",
            "outSR": "4326",
            "f": "geojson",
            "geometryPrecision": 4,
        },
        timeout=120,
    )
    output_path.write_text(json.dumps(geojson), encoding="utf-8")
    return geojson


def load_boundaries(force: bool = False) -> dict[str, dict[str, Any]]:
    """读取地图边界 / Load map boundaries for the app."""

    ensure_directories()
    return {
        "lad_2019": _download_geojson(
            ONS_LAD_2019_FEATURESERVER,
            "LAD19CD,LAD19NM,LONG,LAT",
            RAW_DIR / "lad_2019_boundaries.geojson",
            force=force,
        ),
        "rgn_2019": _download_geojson(
            ONS_REGION_2019_FEATURESERVER,
            "rgn19cd,rgn19nm,long,lat",
            RAW_DIR / "rgn_2019_boundaries.geojson",
            force=force,
        ),
    }


def fetch_lad_to_region_lookup(force: bool = False) -> pd.DataFrame:
    """读取 local authority 到 English region 的官方对应表.

    Load the official lookup table from local authorities to English regions.
    """

    ensure_directories()
    output_path = RAW_DIR / "lad19_to_rgn19_lookup.csv"
    if output_path.exists() and not force:
        return pd.read_csv(output_path)

    data = _get_json(
        ONS_LAD_TO_REGION_2019_FEATURESERVER,
        {
            "where": "1=1",
            "outFields": "LAD19CD,LAD19NM,RGN19CD,RGN19NM",
            "returnGeometry": "false",
            "f": "json",
        },
        timeout=120,
    )
    rows = [feature["attributes"] for feature in data["features"]]
    lookup = pd.DataFrame(rows).sort_values(["RGN19NM", "LAD19NM"])
    lookup.to_csv(output_path, index=False)
    return lookup


def fetch_unemployment_region_raw(force: bool = False) -> pd.DataFrame:
    """下载 ONS/Nomis 最新英地区失业率原始数据.

    Download the latest ONS/Nomis regional unemployment-rate extract.
    The API response also contains Scotland, Wales and Northern Ireland; the
    cleaning step keeps the nine English regions used by the current map.
    """

    ensure_directories()
    output_path = RAW_DIR / "nomis_regional_unemployment_latest_raw.csv"
    if output_path.exists() and not force:
        return pd.read_csv(output_path)

    params = {
        "geography": "TYPE480",
        "time": "latest",
        "sex": "7",
        "economic_activity": "3",
        "value_type": "0",
        "measures": "20207",
        "ExcludeMissingValues": "true",
        "select": (
            "date_name,date_code,geography_name,geography_code,sex_name,"
            "economic_activity_name,value_type_name,measures_name,obs_value,"
            "obs_status,obs_status_name"
        ),
    }
    response = requests.get(
        NOMIS_REGIONAL_LABOUR_MARKET_URL,
        params=params,
        headers=HEADERS,
        timeout=120,
    )
    response.raise_for_status()
    output_path.write_bytes(response.content)
    return pd.read_csv(StringIO(response.text))


def fetch_imd_lad_raw(force: bool = False) -> pd.DataFrame:
    """从 IMD File 7 生成 local authority 层级数据.

    Build local-authority IMD data from IMD File 7 using population weights.
    """

    ensure_directories()
    output_path = RAW_DIR / "imd_lad2019_weighted_from_file7.csv"

    if output_path.exists() and not force:
        return pd.read_csv(output_path)

    _download_file(IMD_FILE_7_URL, IMD_FILE_7_CSV, force=force)

    lsoa = pd.read_csv(
        IMD_FILE_7_CSV,
        usecols=[
            LSOA_CODE,
            LAD_CODE,
            LAD_NAME,
            IMD_SCORE,
            IMD_RANK,
            IMD_DECILE,
            TOTAL_POPULATION,
        ],
    ).rename(
        columns={
            LSOA_CODE: "lsoa_code",
            LAD_CODE: "LAD19CD",
            LAD_NAME: "LAD19NM",
            IMD_SCORE: "imd_score",
            IMD_RANK: "imd_rank",
            IMD_DECILE: "imd_decile",
            TOTAL_POPULATION: "population",
        }
    )

    numeric_columns = ["imd_score", "imd_rank", "imd_decile", "population"]
    for column in numeric_columns:
        lsoa[column] = pd.to_numeric(lsoa[column], errors="coerce")

    lsoa = lsoa.dropna(subset=["LAD19CD", "LAD19NM", "imd_rank", "population"])
    lsoa["weighted_rank"] = lsoa["imd_rank"] * lsoa["population"]
    lsoa["weighted_score"] = lsoa["imd_score"] * lsoa["population"]
    lsoa["most_deprived_10"] = lsoa["imd_decile"].le(1)
    lsoa["most_deprived_20"] = lsoa["imd_decile"].le(2)

    grouped = (
        lsoa.groupby(["LAD19CD", "LAD19NM"], as_index=False)
        .agg(
            weighted_rank_sum=("weighted_rank", "sum"),
            weighted_score_sum=("weighted_score", "sum"),
            population_total=("population", "sum"),
            unweighted_mean_imd_rank=("imd_rank", "mean"),
            median_imd_rank=("imd_rank", "median"),
            lsoa_count=("lsoa_code", "count"),
            most_deprived_10_lsoa_count=("most_deprived_10", "sum"),
            most_deprived_20_lsoa_count=("most_deprived_20", "sum"),
        )
    )

    grouped["mean_imd_rank"] = (
        grouped["weighted_rank_sum"] / grouped["population_total"]
    )
    grouped["mean_imd_score"] = (
        grouped["weighted_score_sum"] / grouped["population_total"]
    )
    grouped["most_deprived_10_lsoa_pct"] = (
        grouped["most_deprived_10_lsoa_count"] / grouped["lsoa_count"] * 100
    )
    grouped["most_deprived_20_lsoa_pct"] = (
        grouped["most_deprived_20_lsoa_count"] / grouped["lsoa_count"] * 100
    )

    output_columns = [
        "LAD19CD",
        "LAD19NM",
        "mean_imd_rank",
        "mean_imd_score",
        "unweighted_mean_imd_rank",
        "median_imd_rank",
        "population_total",
        "lsoa_count",
        "most_deprived_10_lsoa_count",
        "most_deprived_10_lsoa_pct",
        "most_deprived_20_lsoa_count",
        "most_deprived_20_lsoa_pct",
    ]
    result = grouped[output_columns].sort_values("LAD19NM")
    result.to_csv(output_path, index=False)
    return result


def fetch_imd_region_raw(force: bool = False) -> pd.DataFrame:
    """把 local authority 数据聚合成 English region.

    Aggregate local-authority IMD data into official English regions.
    """

    ensure_directories()
    output_path = RAW_DIR / "imd_rgn2019_weighted_from_lad.csv"
    if output_path.exists() and not force:
        return pd.read_csv(output_path)

    lad = fetch_imd_lad_raw(force=force)
    lookup = fetch_lad_to_region_lookup(force=force)
    merged = lad.merge(lookup, on=["LAD19CD", "LAD19NM"], how="left", validate="1:1")

    missing = merged[merged["RGN19CD"].isna()]
    if not missing.empty:
        missing_names = ", ".join(missing["LAD19NM"].head(10).tolist())
        raise ValueError(f"Missing region mapping for local authorities: {missing_names}")

    merged["weighted_rank"] = merged["mean_imd_rank"] * merged["population_total"]
    merged["weighted_score"] = merged["mean_imd_score"] * merged["population_total"]
    merged["unweighted_rank_total"] = (
        merged["unweighted_mean_imd_rank"] * merged["lsoa_count"]
    )
    merged["most_deprived_10_lsoa_total"] = merged["most_deprived_10_lsoa_count"]
    merged["most_deprived_20_lsoa_total"] = merged["most_deprived_20_lsoa_count"]

    grouped = (
        merged.groupby(["RGN19CD", "RGN19NM"], as_index=False)
        .agg(
            weighted_rank_sum=("weighted_rank", "sum"),
            weighted_score_sum=("weighted_score", "sum"),
            population_total=("population_total", "sum"),
            unweighted_rank_total=("unweighted_rank_total", "sum"),
            median_imd_rank=("median_imd_rank", "median"),
            lsoa_count=("lsoa_count", "sum"),
            local_authority_count=("LAD19CD", "count"),
            most_deprived_10_lsoa_count=("most_deprived_10_lsoa_total", "sum"),
            most_deprived_20_lsoa_count=("most_deprived_20_lsoa_total", "sum"),
        )
    )

    grouped["mean_imd_rank"] = (
        grouped["weighted_rank_sum"] / grouped["population_total"]
    )
    grouped["mean_imd_score"] = (
        grouped["weighted_score_sum"] / grouped["population_total"]
    )
    grouped["unweighted_mean_imd_rank"] = (
        grouped["unweighted_rank_total"] / grouped["lsoa_count"]
    )
    grouped["most_deprived_10_lsoa_pct"] = (
        grouped["most_deprived_10_lsoa_count"] / grouped["lsoa_count"] * 100
    )
    grouped["most_deprived_20_lsoa_pct"] = (
        grouped["most_deprived_20_lsoa_count"] / grouped["lsoa_count"] * 100
    )

    output_columns = [
        "RGN19CD",
        "RGN19NM",
        "mean_imd_rank",
        "mean_imd_score",
        "unweighted_mean_imd_rank",
        "median_imd_rank",
        "population_total",
        "lsoa_count",
        "local_authority_count",
        "most_deprived_10_lsoa_count",
        "most_deprived_10_lsoa_pct",
        "most_deprived_20_lsoa_count",
        "most_deprived_20_lsoa_pct",
    ]
    result = grouped[output_columns].sort_values("RGN19NM")
    result.to_csv(output_path, index=False)
    return result


# ---------------------------------------------------------------------------
# 3. 数据清洗和指标格式 / Data cleaning and indicator formatting
# ---------------------------------------------------------------------------
# 中文：这里把 raw aggregation 结果整理成 app 统一读取的字段格式。
# English: This section formats raw aggregated data into the common indicator
# structure used by the app.

def clean_unemployment_region(raw: pd.DataFrame) -> pd.DataFrame:
    """把 ONS/Nomis 地区失业率整理成统一地图格式.

    Format ONS/Nomis regional unemployment rates into the common map schema.
    """

    required = {
        "DATE_NAME",
        "DATE_CODE",
        "GEOGRAPHY_NAME",
        "GEOGRAPHY_CODE",
        "OBS_VALUE",
        "OBS_STATUS_NAME",
    }
    missing = required.difference(raw.columns)
    if missing:
        raise ValueError(
            "Nomis unemployment data is missing columns: "
            + ", ".join(sorted(missing))
        )

    df = raw.loc[
        raw["GEOGRAPHY_CODE"].astype(str).str.fullmatch(r"E1200000[1-9]", na=False)
    ].copy()
    df = df.rename(
        columns={
            "DATE_NAME": "period",
            "DATE_CODE": "period_code",
            "GEOGRAPHY_NAME": "area_name",
            "GEOGRAPHY_CODE": "area_code",
            "OBS_VALUE": "value",
            "OBS_STATUS_NAME": "observation_status",
        }
    )
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["area_code", "area_name", "value"])
    df["area_name"] = df["area_code"].map(ENGLISH_REGION_NAMES).fillna(
        df["area_name"]
    )

    if len(df) != 9 or df["area_code"].nunique() != 9:
        raise ValueError(
            "Expected one unemployment-rate row for each of the 9 English regions; "
            f"received {len(df)} rows and {df['area_code'].nunique()} unique codes."
        )

    df["indicator_id"] = UNEMPLOYMENT_INDICATOR
    df["indicator_label"] = "ONS regional unemployment rate"
    df["unit"] = "% of economically active people aged 16+"
    df["source"] = "Office for National Statistics Labour Force Survey via Nomis"
    df["source_url"] = NOMIS_REGIONAL_LABOUR_MARKET_URL
    df["geography"] = TARGET_GEOGRAPHY
    df["feature_id_key"] = "properties.rgn19cd"
    df["indicator_group"] = "social_need"
    df["value_direction"] = "higher_is_higher_need"
    df["interpretation"] = (
        "Higher values mean a larger share of economically active people are "
        "unemployed. This is a labour-market need indicator, not a measure of "
        "Fusion21 impact."
    )
    df["aggregation_method"] = (
        "Latest seasonally adjusted three-month regional Labour Force Survey "
        "estimate. The unemployment-rate denominator is employment plus unemployment."
    )
    df["period_start"] = pd.to_datetime(
        df["period_code"].astype(str) + "-01",
        errors="coerce",
    )
    df["value"] = df["value"].round(1)

    output_columns = COMMON_METRIC_COLUMNS + [
        "period_code",
        "period_start",
        "observation_status",
    ]
    return df[output_columns].sort_values(["indicator_id", "area_name"])


def clean_imd_lad(raw: pd.DataFrame) -> pd.DataFrame:
    """整理 local authority IMD 数据 / Format local-authority IMD data."""

    return _clean_imd_geography(
        raw=raw,
        code_column="LAD19CD",
        name_column="LAD19NM",
        geography="lad_2019",
        feature_id_key="properties.lad19cd",
        interpretation_geography="local authority",
    )


def clean_imd_region(raw: pd.DataFrame) -> pd.DataFrame:
    """整理 English region IMD 数据 / Format English-region IMD data."""

    return _clean_imd_geography(
        raw=raw,
        code_column="RGN19CD",
        name_column="RGN19NM",
        geography="rgn_2019",
        feature_id_key="properties.rgn19cd",
        interpretation_geography="English region",
    )


def _clean_imd_geography(
    raw: pd.DataFrame,
    code_column: str,
    name_column: str,
    geography: str,
    feature_id_key: str,
    interpretation_geography: str,
) -> pd.DataFrame:
    """把某个地理层级的 IMD 数据整理成统一格式.

    Format IMD data for one geography level into one common structure.
    """

    df = raw.rename(
        columns={
            code_column: "area_code",
            name_column: "area_name",
        }
    ).copy()

    # 中文：IMD rank 越小代表越 deprived。为了地图更直观，这里反转成
    # “数值越高 = social need 越强”的 0-100 relative index。
    # English: IMD rank is reversed: a lower rank means stronger deprivation.
    # For the map, this is converted into a 0-100 index where higher means
    # stronger relative social need.
    min_rank = df["mean_imd_rank"].min()
    max_rank = df["mean_imd_rank"].max()
    df["need_score"] = (max_rank - df["mean_imd_rank"]) / (max_rank - min_rank) * 100

    rounded_columns = [
        "need_score",
        "mean_imd_rank",
        "mean_imd_score",
        "unweighted_mean_imd_rank",
        "median_imd_rank",
        "most_deprived_10_lsoa_pct",
        "most_deprived_20_lsoa_pct",
    ]
    for column in rounded_columns:
        if column in df.columns:
            df[column] = df[column].round(1)

    if "population_total" in df.columns:
        df["population_total"] = df["population_total"].round(0).astype("Int64")

    df["indicator_id"] = IMD_INDICATOR
    df["indicator_label"] = "IMD 2019 population-weighted relative need index"
    df["value"] = df["need_score"]
    df["unit"] = "0-100 relative index"
    df["period"] = "2019"
    df["source"] = (
        "English Indices of Deprivation 2019 File 7: ranks, deciles, scores "
        "and population denominators"
    )
    df["source_url"] = IMD_FILE_7_URL
    df["geography"] = geography
    df["feature_id_key"] = feature_id_key
    df["indicator_group"] = "social_need"
    df["value_direction"] = "higher_is_higher_need"
    df["aggregation_method"] = (
        "Population-weighted average IMD rank using total population mid-2015 "
        "excluding prisoners"
    )
    df["interpretation"] = (
        "Higher index values mean stronger relative deprivation within the "
        "selected geography level. The index is derived from the "
        "population-weighted average IMD rank of LSOAs in each 2019 "
        f"{interpretation_geography}; 100 is the highest relative need in "
        "the current map, not an absolute deprivation score."
    )

    preferred_columns = [
        "indicator_id",
        "indicator_label",
        "area_code",
        "area_name",
        "value",
        "unit",
        "period",
        "source",
        "source_url",
        "geography",
        "feature_id_key",
        "indicator_group",
        "value_direction",
        "interpretation",
        "aggregation_method",
        "mean_imd_rank",
        "mean_imd_score",
        "unweighted_mean_imd_rank",
        "median_imd_rank",
        "population_total",
        "lsoa_count",
        "local_authority_count",
        "most_deprived_10_lsoa_count",
        "most_deprived_10_lsoa_pct",
        "most_deprived_20_lsoa_count",
        "most_deprived_20_lsoa_pct",
        "need_score",
    ]
    output_columns = [column for column in preferred_columns if column in df.columns]
    return df[output_columns].sort_values(["indicator_id", "area_name"])


def build_composite_social_need(
    imd_region: pd.DataFrame,
    unemployment_region: pd.DataFrame,
    deprivation_weight: float = 0.5,
    unemployment_weight: float = 0.5,
) -> pd.DataFrame:
    """Combine two standardised indicators into an exploratory social-need score.

    Both components are expressed on a 0-100 scale where a higher value means
    higher relative need. The default weights are deliberately equal and are
    stored with every output row so the method remains visible and reproducible.
    """

    if not abs(deprivation_weight + unemployment_weight - 1.0) < 1e-9:
        raise ValueError("Composite social-need weights must add up to 1.0.")

    imd = imd_region[["area_code", "area_name", "value"]].rename(
        columns={"value": "deprivation_score"}
    )
    unemployment = unemployment_region[
        ["area_code", "value", "period", "period_start"]
    ].rename(
        columns={
            "value": "unemployment_rate",
            "period": "unemployment_period",
        }
    )
    composite = imd.merge(
        unemployment,
        on="area_code",
        how="inner",
        validate="1:1",
    )

    if len(composite) != 9:
        raise ValueError(
            "Expected 9 matched English regions when building the composite "
            f"social-need score; received {len(composite)}."
        )

    rate_min = composite["unemployment_rate"].min()
    rate_max = composite["unemployment_rate"].max()
    if rate_max == rate_min:
        raise ValueError("Cannot standardise unemployment rates with no variation.")

    composite["unemployment_score"] = (
        (composite["unemployment_rate"] - rate_min) / (rate_max - rate_min) * 100
    )
    composite["deprivation_weight"] = deprivation_weight
    composite["unemployment_weight"] = unemployment_weight
    composite["value"] = (
        composite["deprivation_score"] * deprivation_weight
        + composite["unemployment_score"] * unemployment_weight
    )

    composite["indicator_id"] = COMPOSITE_NEED_INDICATOR
    composite["indicator_label"] = "Composite social need score"
    composite["unit"] = "0-100 relative index"
    composite["period"] = (
        "IMD 2019 + " + composite["unemployment_period"].astype(str)
    )
    composite["source"] = (
        "English Indices of Deprivation 2019 and Office for National "
        "Statistics Labour Force Survey via Nomis"
    )
    composite["source_url"] = IMD_FILE_7_URL + " | " + NOMIS_REGIONAL_LABOUR_MARKET_URL
    composite["geography"] = TARGET_GEOGRAPHY
    composite["feature_id_key"] = "properties.rgn19cd"
    composite["indicator_group"] = "social_need_composite"
    composite["value_direction"] = "higher_is_higher_need"
    composite["interpretation"] = (
        "Higher values indicate stronger relative social need across the nine "
        "English regions. This is an exploratory comparison score, not an "
        "official deprivation statistic or a measure of Fusion21 impact."
    )
    composite["aggregation_method"] = (
        "Equal-weight composite: 50% IMD population-weighted relative need "
        "index plus 50% min-max standardised regional unemployment rate. "
        "Both components use a 0-100 scale where higher means higher need."
    )

    rounded_columns = [
        "deprivation_score",
        "unemployment_rate",
        "unemployment_score",
        "value",
    ]
    composite[rounded_columns] = composite[rounded_columns].round(1)

    output_columns = COMMON_METRIC_COLUMNS + [
        "period_start",
        "deprivation_score",
        "unemployment_rate",
        "unemployment_score",
        "deprivation_weight",
        "unemployment_weight",
    ]
    return composite[output_columns].sort_values(["indicator_id", "area_name"])


# ---------------------------------------------------------------------------
# 4. 数据管线和 app 数据读取 / Data pipeline and app data loading
# ---------------------------------------------------------------------------
# 中文：这里把“读取原始数据 -> 清洗 -> 输出 processed data -> app 读取”
# 串成一个完整流程。
# English: This section connects raw data loading, cleaning, processed output,
# and app-facing data loading into one workflow.

def _is_region_latest(latest: pd.DataFrame) -> bool:
    """检查 processed data 是否包含当前地图需要的全部指标.

    Check whether processed data contains the current region-level indicators.
    """

    required_indicators = {
        IMD_INDICATOR,
        UNEMPLOYMENT_INDICATOR,
        COMPOSITE_NEED_INDICATOR,
    }
    return (
        not latest.empty
        and set(COMMON_METRIC_COLUMNS).issubset(latest.columns)
        and latest["geography"].eq(TARGET_GEOGRAPHY).all()
        and required_indicators.issubset(set(latest["indicator_id"]))
        and latest.groupby("indicator_id")["area_code"].nunique().ge(9).all()
    )


def build_synthetic_fusion21_data(seed: int = 2107) -> dict[str, pd.DataFrame]:
    """Create linked demonstration tables for prototype testing.

    The generated values are fictional and must not be used to assess Fusion21.
    A fixed seed makes the files reproducible across pipeline runs.
    """

    ensure_directories()
    rng = Random(seed)
    frameworks = [
        "Decarbonisation",
        "Construction Works",
        "Facilities Management",
        "Public Buildings",
    ]
    foundation_budgets = [
        "Employment and Skills",
        "Community Wellbeing",
        "Environmental Sustainability",
        "Financial Inclusion",
    ]

    contract_rows: list[dict[str, Any]] = []
    activity_rows: list[dict[str, Any]] = []
    foundation_rows: list[dict[str, Any]] = []
    contract_number = 1
    case_number = 1

    for region_index, profile in enumerate(SYNTHETIC_REGION_PROFILES, start=1):
        low_value, high_value = profile["contract_value_range"]
        for region_contract_index in range(profile["contract_count"]):
            contract_id = f"F21-SYN-{contract_number:04d}"
            member = (
                f"Demo Member {region_index:02d}-"
                f"{(region_contract_index % 2) + 1}"
            )
            supplier = f"Demo Supplier {((contract_number - 1) % 12) + 1:02d}"
            contract_value = round(rng.uniform(low_value, high_value) / 1_000) * 1_000
            start_month = ((contract_number * 2) % 12) + 1
            start_day = ((contract_number * 3) % 24) + 1
            start_date = pd.Timestamp(2024, start_month, start_day)
            latitude = profile["latitude"] + rng.uniform(-0.075, 0.075)
            longitude = profile["longitude"] + rng.uniform(-0.10, 0.10)

            contract_rows.append(
                {
                    "ID Number": contract_id,
                    "Member": member,
                    "Supplier": supplier,
                    "Fusion21 Framework": frameworks[
                        (contract_number - 1) % len(frameworks)
                    ],
                    "Lot": f"Lot {((contract_number - 1) % 4) + 1}",
                    "Start Date": start_date.date().isoformat(),
                    "Contract Value FY2024/25": float(contract_value),
                    "Delivery Postcode": profile["delivery_postcode"],
                    "Local Authority Code": profile["local_authority_code"],
                    "Local Authority Name": profile["local_authority_name"],
                    "ONS Region Code": profile["region_code"],
                    "Region Name": profile["region_name"],
                    "Latitude": round(latitude, 6),
                    "Longitude": round(longitude, 6),
                    "Synthetic Data": True,
                }
            )

            activity_row: dict[str, Any] = {
                "Fusion21 Contract ID": contract_id,
                "Fusion21 Member": member,
                "Supplier Name": supplier,
                "Synthetic Data": True,
            }
            for column, _short_label in SYNTHETIC_ACTIVITY_COLUMNS:
                probability = profile["activity_probability"] + rng.uniform(-0.08, 0.08)
                activity_row[column] = "Yes" if rng.random() < probability else "No"
            activity_rows.append(activity_row)

            if rng.random() < 0.68:
                payment_count = 2 if rng.random() < 0.22 else 1
                for payment_index in range(payment_count):
                    budget_name = foundation_budgets[
                        (contract_number + payment_index) % len(foundation_budgets)
                    ]
                    programme_budget = round(
                        rng.uniform(180_000, 900_000) / 1_000
                    ) * 1_000
                    amount = round(
                        min(
                            programme_budget * rng.uniform(0.08, 0.34),
                            contract_value * 0.045,
                        )
                        / 500
                    ) * 500
                    paid_month = ((start_month + payment_index + 2) % 12) + 1
                    paid_year = 2024 if paid_month >= start_month else 2025
                    foundation_rows.append(
                        {
                            "Fusion21 Contract ID": contract_id,
                            "Fusion21 Member": member,
                            "Month Paid": f"{paid_year}-{paid_month:02d}",
                            "Associated Foundation Budget": budget_name,
                            "Programme Budget": float(programme_budget),
                            "Associated Foundation Case": f"F21F-SYN-{case_number:04d}",
                            "Amount": float(amount),
                            "ONS Region Code": profile["region_code"],
                            "Region Name": profile["region_name"],
                            "Synthetic Data": True,
                        }
                    )
                    case_number += 1

            contract_number += 1

    contracts = pd.DataFrame(contract_rows)
    activities = pd.DataFrame(activity_rows)
    foundation = pd.DataFrame(foundation_rows)

    if not contracts["ID Number"].is_unique:
        raise ValueError("Synthetic contract IDs must be unique.")
    if set(activities["Fusion21 Contract ID"]) != set(contracts["ID Number"]):
        raise ValueError("Every synthetic contract must have one activity record.")
    if not set(foundation["Fusion21 Contract ID"]).issubset(
        set(contracts["ID Number"])
    ):
        raise ValueError("Synthetic Foundation records contain unknown contracts.")
    if contracts["ONS Region Code"].nunique() != 9:
        raise ValueError("Synthetic contracts must cover all nine English regions.")

    activity_columns = [column for column, _label in SYNTHETIC_ACTIVITY_COLUMNS]
    activity_labels = dict(SYNTHETIC_ACTIVITY_COLUMNS)
    activity_work = activities.copy()
    activity_work["Recorded Activity Count"] = (
        activity_work[activity_columns].eq("Yes").sum(axis=1)
    )

    def primary_activity(row: pd.Series) -> str:
        for column in activity_columns:
            if row[column] == "Yes":
                return activity_labels[column]
        return "No recorded activity"

    activity_work["Primary Activity"] = activity_work.apply(
        primary_activity,
        axis=1,
    )
    foundation_by_contract = (
        foundation.groupby("Fusion21 Contract ID", as_index=False)["Amount"]
        .sum()
        .rename(columns={"Amount": "Foundation Investment"})
    )

    projects = (
        contracts.merge(
            activity_work[
                [
                    "Fusion21 Contract ID",
                    "Recorded Activity Count",
                    "Primary Activity",
                ]
            ],
            left_on="ID Number",
            right_on="Fusion21 Contract ID",
            how="left",
            validate="1:1",
        )
        .merge(
            foundation_by_contract,
            on="Fusion21 Contract ID",
            how="left",
            validate="1:1",
        )
    )
    projects["Foundation Investment"] = projects["Foundation Investment"].fillna(0.0)
    projects = projects.rename(
        columns={
            "ID Number": "contract_id",
            "Member": "member",
            "Supplier": "supplier",
            "Fusion21 Framework": "framework",
            "Lot": "lot",
            "Start Date": "start_date",
            "Contract Value FY2024/25": "contract_value",
            "Delivery Postcode": "delivery_postcode",
            "Local Authority Code": "local_authority_code",
            "Local Authority Name": "local_authority_name",
            "ONS Region Code": "area_code",
            "Region Name": "area_name",
            "Latitude": "latitude",
            "Longitude": "longitude",
            "Recorded Activity Count": "activity_count",
            "Primary Activity": "primary_activity",
            "Foundation Investment": "foundation_investment",
            "Synthetic Data": "synthetic_data",
        }
    )
    projects["period"] = projects["start_date"].str[:4]

    contract_summary = (
        projects.groupby(["area_code", "area_name"], as_index=False)
        .agg(
            project_count=("contract_id", "nunique"),
            contract_value=("contract_value", "sum"),
            foundation_investment=("foundation_investment", "sum"),
            recorded_activity_count=("activity_count", "sum"),
            projects_with_foundation_investment=(
                "foundation_investment",
                lambda values: int((values > 0).sum()),
            ),
        )
    )
    contract_summary["activities_per_project"] = (
        contract_summary["recorded_activity_count"]
        / contract_summary["project_count"]
    ).round(2)

    activity_region = activities.merge(
        contracts[["ID Number", "ONS Region Code"]],
        left_on="Fusion21 Contract ID",
        right_on="ID Number",
        how="left",
        validate="1:1",
    )
    activity_region[activity_columns] = activity_region[activity_columns].eq("Yes")
    activity_counts = (
        activity_region.groupby("ONS Region Code", as_index=False)[activity_columns]
        .sum()
        .rename(columns={"ONS Region Code": "area_code"})
    )
    activity_count_rename = {
        column: f"{short_label.lower().replace(' ', '_')}_count"
        for column, short_label in SYNTHETIC_ACTIVITY_COLUMNS
    }
    activity_counts = activity_counts.rename(columns=activity_count_rename)
    region_summary = contract_summary.merge(
        activity_counts,
        on="area_code",
        how="left",
        validate="1:1",
    )

    # 中文：活动得分直接使用 Yes 数量除以全部可记录活动项，不做 Min-Max。
    # English: Activity Score is the Yes proportion, not a Min-Max score.
    activity_field_count = len(activity_columns)
    region_summary["activity_possible_count"] = (
        region_summary["project_count"] * activity_field_count
    )
    region_summary["activity_score"] = (
        region_summary["recorded_activity_count"]
        / region_summary["activity_possible_count"]
        * 100
    )

    # 中文：金额指标单位很大，先按九个地区的相对位置转换到 0-100。
    # English: Convert the two monetary indicators to a common 0-100 scale.
    def min_max_score(values: pd.Series) -> pd.Series:
        minimum = float(values.min())
        maximum = float(values.max())
        if maximum == minimum:
            return pd.Series(50.0, index=values.index)
        return (values - minimum) / (maximum - minimum) * 100

    region_summary["procurement_score"] = min_max_score(
        region_summary["contract_value"]
    )
    region_summary["foundation_score"] = min_max_score(
        region_summary["foundation_investment"]
    )

    # 中文：原型阶段三个组成得分等权平均。
    # English: The prototype uses an equal-weight mean of the three components.
    component_columns = [
        "procurement_score",
        "activity_score",
        "foundation_score",
    ]
    region_summary["contribution_score"] = region_summary[
        component_columns
    ].mean(axis=1)
    score_columns = component_columns + ["contribution_score"]
    region_summary[score_columns] = region_summary[score_columns].round(1)
    region_summary["synthetic_data"] = True

    metric_specs = [
        (
            "fusion21_contract_value_synthetic",
            "Synthetic contract value",
            "contract_value",
            "GBP",
            "Sum of synthetic contract values by ONS English region.",
        ),
        (
            "fusion21_foundation_investment_synthetic",
            "Synthetic Foundation investment",
            "foundation_investment",
            "GBP",
            "Sum of synthetic Foundation payment amounts by ONS English region.",
        ),
        (
            "fusion21_project_count_synthetic",
            "Synthetic project count",
            "project_count",
            "projects",
            "Count of distinct synthetic contracts by ONS English region.",
        ),
        (
            "fusion21_activity_count_synthetic",
            "Synthetic recorded activity count",
            "recorded_activity_count",
            "recorded Yes activities",
            "Sum of Yes responses across the six synthetic activity fields.",
        ),
        (
            "fusion21_procurement_score_synthetic",
            "Synthetic Procurement Score",
            "procurement_score",
            "score (0-100)",
            "Min-Max standardisation of regional synthetic contract-value totals.",
        ),
        (
            "fusion21_activity_score_synthetic",
            "Synthetic Activity Score",
            "activity_score",
            "score (0-100)",
            "Yes responses divided by all possible regional activity responses.",
        ),
        (
            "fusion21_foundation_score_synthetic",
            "Synthetic Foundation Score",
            "foundation_score",
            "score (0-100)",
            "Min-Max standardisation of regional synthetic Foundation payments.",
        ),
        (
            "fusion21_contribution_score_synthetic",
            "Synthetic Fusion21 Contribution Score",
            "contribution_score",
            "score (0-100)",
            "Equal-weight mean of Procurement, Activity and Foundation Scores.",
        ),
    ]
    metric_frames: list[pd.DataFrame] = []
    for (
        indicator_id,
        indicator_label,
        value_column,
        unit,
        aggregation_method,
    ) in metric_specs:
        metric = region_summary[["area_code", "area_name", value_column]].rename(
            columns={value_column: "value"}
        )
        metric["indicator_id"] = indicator_id
        metric["indicator_label"] = indicator_label
        metric["unit"] = unit
        metric["period"] = "Synthetic FY2024/25"
        metric["source"] = "AI-assisted synthetic demonstration data"
        metric["source_url"] = ""
        metric["geography"] = TARGET_GEOGRAPHY
        metric["feature_id_key"] = "properties.rgn19cd"
        metric["indicator_group"] = "fusion21_synthetic"
        metric["value_direction"] = "higher_is_more_recorded_activity_or_investment"
        metric["interpretation"] = (
            "Fictional value for prototype testing only; it does not describe "
            "Fusion21 performance."
        )
        metric["aggregation_method"] = aggregation_method
        metric["synthetic_data"] = True
        metric_frames.append(metric)
    map_metrics = pd.concat(metric_frames, ignore_index=True)[
        COMMON_METRIC_COLUMNS + ["synthetic_data"]
    ]

    contracts.to_csv(
        SYNTHETIC_DIR / "fusion21_contracts_synthetic.csv",
        index=False,
    )
    activities.to_csv(
        SYNTHETIC_DIR / "fusion21_social_value_activities_synthetic.csv",
        index=False,
    )
    foundation.to_csv(
        SYNTHETIC_DIR / "fusion21_foundation_payments_synthetic.csv",
        index=False,
    )
    projects.to_csv(
        PROCESSED_DIR / "fusion21_projects_synthetic.csv",
        index=False,
    )
    region_summary.to_csv(
        PROCESSED_DIR / "fusion21_region_summary_synthetic.csv",
        index=False,
    )
    map_metrics.to_csv(
        PROCESSED_DIR / "fusion21_map_metrics_synthetic.csv",
        index=False,
    )

    return {
        "contracts": contracts,
        "activities": activities,
        "foundation": foundation,
        "projects": projects,
        "region_summary": region_summary,
        "map_metrics": map_metrics,
    }


def build_all_data(force: bool = False) -> dict[str, Any]:
    """重新构建 app 需要的所有 processed data.

    Rebuild all processed data required by the Streamlit app.
    """

    ensure_directories()
    boundaries = load_boundaries(force=force)

    # 中文：LAD 文件保留为方法检查证据；app 默认展示 English region。
    # English: The LAD file is kept for method checking; the app shows English
    # regions by default.
    imd_lad = clean_imd_lad(fetch_imd_lad_raw(force=force))
    imd_region = clean_imd_region(fetch_imd_region_raw(force=force))
    unemployment_region = clean_unemployment_region(
        fetch_unemployment_region_raw(force=force)
    )
    composite_need = build_composite_social_need(imd_region, unemployment_region)
    fusion21_synthetic = build_synthetic_fusion21_data()

    imd_lad.to_csv(PROCESSED_DIR / "imd_lad2019.csv", index=False)
    imd_region.to_csv(PROCESSED_DIR / "imd_rgn2019.csv", index=False)
    unemployment_region.to_csv(
        PROCESSED_DIR / "unemployment_rgn_latest.csv",
        index=False,
    )
    composite_need.to_csv(
        PROCESSED_DIR / "social_need_composite_latest.csv",
        index=False,
    )

    latest = pd.concat(
        [imd_region, unemployment_region, composite_need],
        ignore_index=True,
        sort=False,
    ).sort_values(["indicator_id", "area_name"])

    imd_timeseries = imd_region[COMMON_METRIC_COLUMNS].assign(
        period_start=pd.Timestamp("2019-01-01")
    )
    unemployment_timeseries = unemployment_region[
        COMMON_METRIC_COLUMNS + ["period_start"]
    ]
    composite_timeseries = composite_need[COMMON_METRIC_COLUMNS + ["period_start"]]
    timeseries = pd.concat(
        [imd_timeseries, unemployment_timeseries, composite_timeseries],
        ignore_index=True,
        sort=False,
    ).sort_values(["indicator_id", "period_start", "area_name"])

    latest.to_csv(PROCESSED_DIR / "metrics_latest.csv", index=False)
    timeseries.to_csv(PROCESSED_DIR / "metrics_timeseries.csv", index=False)

    return {
        "latest": latest,
        "timeseries": timeseries,
        "boundaries": boundaries,
        "fusion21_synthetic": fusion21_synthetic,
    }


def load_processed_data() -> dict[str, Any]:
    """给 app 快速读取 processed data.

    Load processed data for the app. If processed data is missing or outdated,
    rebuild it automatically.
    """

    latest_path = PROCESSED_DIR / "metrics_latest.csv"
    timeseries_path = PROCESSED_DIR / "metrics_timeseries.csv"
    unemployment_path = PROCESSED_DIR / "unemployment_rgn_latest.csv"
    composite_path = PROCESSED_DIR / "social_need_composite_latest.csv"
    synthetic_projects_path = PROCESSED_DIR / "fusion21_projects_synthetic.csv"
    synthetic_region_path = PROCESSED_DIR / "fusion21_region_summary_synthetic.csv"
    synthetic_metrics_path = PROCESSED_DIR / "fusion21_map_metrics_synthetic.csv"
    synthetic_contracts_path = SYNTHETIC_DIR / "fusion21_contracts_synthetic.csv"
    synthetic_activities_path = (
        SYNTHETIC_DIR / "fusion21_social_value_activities_synthetic.csv"
    )
    synthetic_foundation_path = (
        SYNTHETIC_DIR / "fusion21_foundation_payments_synthetic.csv"
    )
    boundary_2019 = RAW_DIR / "lad_2019_boundaries.geojson"
    region_boundary_2019 = RAW_DIR / "rgn_2019_boundaries.geojson"
    expected = [
        latest_path,
        timeseries_path,
        unemployment_path,
        composite_path,
        synthetic_projects_path,
        synthetic_region_path,
        synthetic_metrics_path,
        synthetic_contracts_path,
        synthetic_activities_path,
        synthetic_foundation_path,
        boundary_2019,
        region_boundary_2019,
    ]

    if not all(path.exists() for path in expected):
        return build_all_data(force=False)

    latest = pd.read_csv(latest_path)
    if not _is_region_latest(latest):
        return build_all_data(force=False)

    synthetic_region = pd.read_csv(synthetic_region_path)
    required_contribution_columns = {
        "activity_possible_count",
        "procurement_score",
        "activity_score",
        "foundation_score",
        "contribution_score",
    }
    if not required_contribution_columns.issubset(synthetic_region.columns):
        return build_all_data(force=False)

    return {
        "latest": latest,
        "timeseries": pd.read_csv(timeseries_path, parse_dates=["period_start"]),
        "boundaries": {
            "lad_2019": json.loads(boundary_2019.read_text(encoding="utf-8")),
            "rgn_2019": json.loads(region_boundary_2019.read_text(encoding="utf-8")),
        },
        "fusion21_synthetic": {
            "contracts": pd.read_csv(
                synthetic_contracts_path
            ),
            "activities": pd.read_csv(
                synthetic_activities_path
            ),
            "foundation": pd.read_csv(
                synthetic_foundation_path
            ),
            "projects": pd.read_csv(synthetic_projects_path),
            "region_summary": synthetic_region,
            "map_metrics": pd.read_csv(synthetic_metrics_path),
        },
    }
