from __future__ import annotations

from pathlib import Path
import re
import sys

import pandas as pd
import plotly.express as px
import streamlit as st


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from fusion21 import build_all_data, load_processed_data


IMD_INDICATOR = "imd2019_need"
UNEMPLOYMENT_INDICATOR = "unemployment_rate_lfs"
COMPOSITE_NEED_INDICATOR = "social_need_composite"

INDICATOR_NAMES = {
    COMPOSITE_NEED_INDICATOR: "Composite social need score",
    IMD_INDICATOR: "Population-weighted deprivation",
    UNEMPLOYMENT_INDICATOR: "Regional unemployment rate",
}

INDICATOR_SHORT_NAMES = {
    COMPOSITE_NEED_INDICATOR: "Social need score",
    IMD_INDICATOR: "Relative need index",
    UNEMPLOYMENT_INDICATOR: "Unemployment rate",
}

st.set_page_config(
    page_title="Fusion21 Social Need Explorer",
    page_icon="F21",
    layout="wide",
)

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1.5rem;
        max-width: 1280px;
    }
    .app-kicker {
        color: #087e8b;
        font-size: 0.78rem;
        font-weight: 750;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        margin-bottom: 0.35rem;
    }
    .app-title {
        color: #172234;
        font-size: 2.15rem;
        font-weight: 760;
        line-height: 1.12;
        margin-bottom: 0.45rem;
    }
    .app-copy {
        color: #596574;
        font-size: 1rem;
        line-height: 1.55;
        max-width: 960px;
    }
    .section-heading {
        color: #172234;
        font-size: 1.25rem;
        font-weight: 730;
        margin: 0.2rem 0 0.25rem 0;
    }
    .section-copy {
        color: #657180;
        font-size: 0.94rem;
        line-height: 1.5;
    }
    [data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #dfe5ec;
        border-radius: 7px;
        padding: 12px 14px;
        min-height: 102px;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.75rem;
    }
    .summary-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 16px;
        margin: 0 0 18px 0;
    }
    .summary-card {
        background: #ffffff;
        border: 1px solid #dfe5ec;
        border-radius: 7px;
        padding: 14px;
        min-height: 102px;
    }
    .summary-label {
        color: #52606f;
        font-size: 0.78rem;
        margin-bottom: 10px;
    }
    .summary-value {
        color: #172234;
        font-size: 1.65rem;
        line-height: 1.15;
        overflow-wrap: anywhere;
    }
    .map-legend {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 8px 14px;
        background: #ffffff;
        border: 1px solid #dfe5ec;
        border-radius: 7px;
        padding: 11px 13px;
        margin: 4px 0 10px 0;
    }
    .map-legend-title {
        grid-column: 1 / -1;
        color: #52606f;
        font-size: 0.78rem;
        font-weight: 650;
    }
    .map-legend-item {
        display: flex;
        align-items: center;
        gap: 8px;
        color: #3f4b57;
        font-size: 0.82rem;
        line-height: 1.3;
    }
    .map-legend-swatch {
        width: 13px;
        height: 13px;
        border-radius: 2px;
        flex: 0 0 13px;
    }
    .detail-box {
        background: #ffffff;
        border: 1px solid #dfe5ec;
        border-radius: 7px;
        padding: 14px 16px;
        margin-bottom: 10px;
    }
    .detail-label {
        color: #6a7684;
        font-size: 0.78rem;
        font-weight: 650;
        margin-bottom: 4px;
    }
    .detail-value {
        color: #172234;
        font-size: 1.45rem;
        font-weight: 750;
        line-height: 1.2;
    }
    .method-note {
        background: #f3f8f8;
        border-left: 4px solid #087e8b;
        border-radius: 6px;
        padding: 13px 15px;
        color: #3f4b57;
        line-height: 1.5;
    }
    .warning-note {
        background: #fff6ef;
        border-left: 4px solid #e66b3d;
        border-radius: 6px;
        padding: 13px 15px;
        color: #3f4b57;
        line-height: 1.5;
    }
    .source-note {
        color: #6a7684;
        font-size: 0.82rem;
        line-height: 1.45;
    }
    @media (max-width: 800px) {
        .summary-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
        .summary-card { min-height: 92px; padding: 12px; }
        .summary-value { font-size: 1.35rem; }
        .map-legend { grid-template-columns: 1fr; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def get_data(force: bool = False) -> dict:
    if force:
        return build_all_data(force=True)
    return load_processed_data()


def format_value(indicator_id: str, value: float) -> str:
    if indicator_id == UNEMPLOYMENT_INDICATOR:
        return f"{value:.1f}%"
    return f"{value:.1f}"


def format_reference_period(indicator_id: str, period: object) -> str:
    period_text = str(period)
    if indicator_id == COMPOSITE_NEED_INDICATOR:
        years = list(dict.fromkeys(re.findall(r"\b(?:19|20)\d{2}\b", period_text)))
        return " + ".join(years)
    return period_text


def format_money(value: float) -> str:
    if abs(value) >= 1_000_000:
        return f"£{value / 1_000_000:,.1f}m"
    if abs(value) >= 1_000:
        return f"£{value / 1_000:,.0f}k"
    return f"£{value:,.0f}"


def minmax_index(values: pd.Series) -> pd.Series:
    minimum = float(values.min())
    maximum = float(values.max())
    if maximum == minimum:
        return pd.Series(50.0, index=values.index)
    return (values - minimum) / (maximum - minimum) * 100


def comparison_group(row: pd.Series, imd_median: float, unemployment_median: float) -> str:
    high_imd = row["imd_need"] >= imd_median
    high_unemployment = row["unemployment_rate"] >= unemployment_median
    if high_imd and high_unemployment:
        return "Higher on both"
    if high_imd:
        return "Higher deprivation only"
    if high_unemployment:
        return "Higher unemployment only"
    return "Lower on both"


def need_activity_group(
    row: pd.Series,
    need_median: float,
    measure_median: float,
) -> str:
    high_need = row["social_need_score"] >= need_median
    high_measure = row["selected_measure"] >= measure_median
    if high_need and not high_measure:
        return "High need / lower contribution"
    if high_need and high_measure:
        return "High need / higher contribution"
    if not high_need and high_measure:
        return "Lower need / higher contribution"
    return "Lower need / lower contribution"


refresh = False
with st.sidebar:
    st.title("Fusion21 prototype")
    st.caption("Public social-need evidence for the nine English regions.")
    refresh = st.button("Refresh public data", width="stretch")
    if refresh:
        st.cache_data.clear()

try:
    data = get_data(force=refresh)
except Exception as exc:
    st.error(
        "The application could not load the processed data. Run pipeline.py first "
        "or check the files in data/processed/."
    )
    st.exception(exc)
    st.stop()
latest: pd.DataFrame = data["latest"].copy()
boundaries = data["boundaries"]
fusion21_synthetic = data["fusion21_synthetic"]
synthetic_projects: pd.DataFrame = fusion21_synthetic["projects"].copy()
synthetic_region_summary: pd.DataFrame = fusion21_synthetic[
    "region_summary"
].copy()

base_indicators = {IMD_INDICATOR, UNEMPLOYMENT_INDICATOR}
required_indicators = base_indicators | {COMPOSITE_NEED_INDICATOR}
if (
    "rgn_2019" not in boundaries
    or latest.empty
    or not required_indicators.issubset(set(latest["indicator_id"]))
):
    st.cache_data.clear()
    data = build_all_data(force=False)
    latest = data["latest"].copy()
    boundaries = data["boundaries"]

with st.sidebar:
    indicator_options = [
        indicator
        for indicator in [
            COMPOSITE_NEED_INDICATOR,
            IMD_INDICATOR,
            UNEMPLOYMENT_INDICATOR,
        ]
        if indicator in set(latest["indicator_id"])
    ]
    selected_indicator = st.selectbox(
        "Map indicator",
        indicator_options,
        format_func=lambda indicator: INDICATOR_NAMES[indicator],
    )
    area_options = sorted(latest["area_name"].dropna().unique())
    default_area = "North West" if "North West" in area_options else area_options[0]
    selected_area_name = st.selectbox(
        "Selected region",
        area_options,
        index=area_options.index(default_area),
    )

indicator_data = latest[latest["indicator_id"] == selected_indicator].copy()
selected_area = indicator_data[
    indicator_data["area_name"] == selected_area_name
].iloc[0]
top_area = indicator_data.sort_values("value", ascending=False).iloc[0]
median_value = float(indicator_data["value"].median())

st.markdown(
    """
    <div class="app-kicker">Fusion21 MSc project</div>
    <div class="app-title">Social need across English regions</div>
    <div class="app-copy">
    This prototype combines two public sources in one reusable pipeline:
    population-weighted deprivation and the latest ONS regional unemployment rate.
    It also provides a transparent equal-weight composite social need score while
    preserving both source indicators for comparison.
    </div>
    """,
    unsafe_allow_html=True,
)

st.divider()

st.markdown(
    f"""
    <div class="summary-grid">
        <div class="summary-card">
            <div class="summary-label">Regions</div>
            <div class="summary-value">{indicator_data['area_code'].nunique()}</div>
        </div>
        <div class="summary-card">
            <div class="summary-label">{selected_area_name}</div>
            <div class="summary-value">{format_value(selected_indicator, float(selected_area['value']))}</div>
        </div>
        <div class="summary-card">
            <div class="summary-label">Highest-value region</div>
            <div class="summary-value">{top_area['area_name']}</div>
        </div>
        <div class="summary-card">
            <div class="summary-label">Reference period</div>
            <div class="summary-value">{format_reference_period(selected_indicator, selected_area['period'])}</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

map_tab, alignment_tab, compare_tab, fusion21_tab = st.tabs(
    [
        "Social need map",
        "Need vs contribution",
        "Compare need indicators",
        "Fusion21 synthetic data",
    ]
)

with map_tab:
    st.markdown(
        f'<div class="section-heading">{INDICATOR_NAMES[selected_indicator]}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-copy">Use the sidebar to switch the public indicator. '
        "The map remains fixed on England so the regional pattern can be compared "
        "consistently.</div>",
        unsafe_allow_html=True,
    )

    geojson = boundaries["rgn_2019"]
    map_df = indicator_data.dropna(subset=["value"]).copy()
    hover_data: dict[str, object] = {
        "area_code": True,
        "value": ":,.1f",
    }
    imd_hover_fields = {
        "mean_imd_rank": ":,.1f",
        "population_total": ":,",
        "most_deprived_10_lsoa_pct": ":,.1f",
        "local_authority_count": True,
    }
    for column, display_format in imd_hover_fields.items():
        if column in map_df.columns and map_df[column].notna().any():
            hover_data[column] = display_format

    composite_hover_fields = {
        "deprivation_score": ":,.1f",
        "unemployment_rate": ":,.1f",
        "unemployment_score": ":,.1f",
    }
    for column, display_format in composite_hover_fields.items():
        if column in map_df.columns and map_df[column].notna().any():
            hover_data[column] = display_format

    colour_scale = (
        "Tealgrn"
        if selected_indicator == UNEMPLOYMENT_INDICATOR
        else "YlOrRd"
    )
    fig = px.choropleth(
        map_df,
        geojson=geojson,
        locations="area_code",
        featureidkey="properties.rgn19cd",
        color="value",
        color_continuous_scale=colour_scale,
        hover_name="area_name",
        hover_data=hover_data,
        projection="mercator",
        labels={
            "value": INDICATOR_SHORT_NAMES[selected_indicator],
            "mean_imd_rank": "Population-weighted mean IMD rank",
            "population_total": "Population",
            "most_deprived_10_lsoa_pct": "% LSOAs in most deprived 10%",
            "local_authority_count": "Local authorities",
            "deprivation_score": "Deprivation component (0-100)",
            "unemployment_rate": "Unemployment rate (%)",
            "unemployment_score": "Unemployment component (0-100)",
        },
    )
    fig.update_layout(
        margin={"r": 0, "t": 4, "l": 0, "b": 0},
        height=610,
        coloraxis_colorbar={
            "title": INDICATOR_SHORT_NAMES[selected_indicator],
            "thickness": 14,
            "len": 0.7,
        },
    )
    fig.update_geos(
        fitbounds="locations",
        resolution=50,
        showframe=False,
        showcoastlines=True,
        coastlinecolor="#aab4bc",
        showland=True,
        landcolor="#f7f8f9",
        showocean=True,
        oceancolor="#d7dfe3",
        bgcolor="#d7dfe3",
    )
    fig.update_traces(marker_line_width=0.3, marker_line_color="#697582")

    map_column, detail_column = st.columns([2.15, 1])
    with map_column:
        st.plotly_chart(
            fig,
            width="stretch",
            config={
                "displayModeBar": False,
                "doubleClick": False,
                "scrollZoom": False,
                "staticPlot": True,
            },
        )

    with detail_column:
        st.subheader("Selected region")
        st.markdown(
            f"""
            <div class="detail-box">
                <div class="detail-label">Region</div>
                <div class="detail-value">{selected_area_name}</div>
            </div>
            <div class="detail-box">
                <div class="detail-label">{INDICATOR_SHORT_NAMES[selected_indicator]}</div>
                <div class="detail-value">{format_value(selected_indicator, float(selected_area['value']))}</div>
            </div>
            <div class="detail-box">
                <div class="detail-label">Reference period</div>
                <div class="detail-value">{selected_area['period']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if selected_indicator == COMPOSITE_NEED_INDICATOR:
            st.markdown(
                f"""
                <div class="detail-box">
                    <div class="detail-label">Deprivation component</div>
                    <div class="detail-value">{selected_area['deprivation_score']:,.1f}</div>
                </div>
                <div class="detail-box">
                    <div class="detail-label">Unemployment component</div>
                    <div class="detail-value">{selected_area['unemployment_score']:,.1f}</div>
                </div>
                <div class="detail-box">
                    <div class="detail-label">Observed unemployment rate</div>
                    <div class="detail-value">{selected_area['unemployment_rate']:,.1f}%</div>
                </div>
                <div class="method-note">
                <strong>Formula:</strong> 50% deprivation score + 50% standardised
                unemployment score. All component scores run from 0 to 100.
                </div>
                """,
                unsafe_allow_html=True,
            )
        elif selected_indicator == IMD_INDICATOR:
            st.markdown(
                f"""
                <div class="detail-box">
                    <div class="detail-label">Weighted mean IMD rank</div>
                    <div class="detail-value">{selected_area['mean_imd_rank']:,.1f}</div>
                </div>
                <div class="detail-box">
                    <div class="detail-label">Population denominator</div>
                    <div class="detail-value">{int(selected_area['population_total']):,}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div class="method-note">
                The unemployment rate uses employment plus unemployment as its
                denominator. It is not the percentage of the whole population.
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.subheader("Highest-value regions")
        ranking_columns = ["area_name", "value"]
        if selected_indicator == COMPOSITE_NEED_INDICATOR:
            ranking_columns.extend(["deprivation_score", "unemployment_score"])
        ranking = indicator_data[ranking_columns].sort_values("value", ascending=False)
        ranking_config: dict[str, object] = {
            "area_name": "Region",
            "value": st.column_config.NumberColumn(
                INDICATOR_SHORT_NAMES[selected_indicator], format="%.1f"
            ),
        }
        if selected_indicator == COMPOSITE_NEED_INDICATOR:
            ranking_config.update(
                {
                    "deprivation_score": st.column_config.NumberColumn(
                        "Deprivation", format="%.1f"
                    ),
                    "unemployment_score": st.column_config.NumberColumn(
                        "Unemployment", format="%.1f"
                    ),
                }
            )
        st.dataframe(
            ranking,
            width="stretch",
            hide_index=True,
            column_config=ranking_config,
        )

    st.markdown(
        f"""
        <div class="source-note">
        <strong>Source:</strong> {selected_area['source']}<br>
        <strong>Method:</strong> {selected_area['aggregation_method']}<br>
        <strong>Interpretation:</strong> {selected_area['interpretation']}
        </div>
        """,
        unsafe_allow_html=True,
    )

with alignment_tab:
    st.markdown(
        '<div class="section-heading">Where social need and recorded contribution do not align</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="section-copy">
        This view places the public Social Need Score beside one synthetic Fusion21
        contribution measure. The four map categories are defined by the median of
        each measure. The red category is the main review group: regions with higher
        public need but lower recorded contribution in the demonstration data.
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="warning-note">
        <strong>Demonstration only:</strong> all Fusion21 records on this page are
        synthetic. The view tests the method and interface; it does not evaluate
        Fusion21's real performance or prove social impact.
        </div>
        """,
        unsafe_allow_html=True,
    )

    alignment_measure_labels = {
        "contribution_score": "Composite Contribution Score",
        "procurement_score": "Procurement Score",
        "activity_score": "Activity Score",
        "foundation_score": "Foundation Score",
    }
    selected_alignment_measure = st.selectbox(
        "Fusion21 contribution measure",
        list(alignment_measure_labels),
        format_func=lambda column: alignment_measure_labels[column],
        key="alignment_measure_selector",
    )

    social_need_latest = latest[
        latest["indicator_id"] == COMPOSITE_NEED_INDICATOR
    ][["area_code", "area_name", "value"]].rename(
        columns={"value": "social_need_score"}
    )
    alignment = social_need_latest.merge(
        synthetic_region_summary[
            [
                "area_code",
                "contribution_score",
                "procurement_score",
                "activity_score",
                "foundation_score",
                "contract_value",
                "recorded_activity_count",
                "activity_possible_count",
                "foundation_investment",
            ]
        ],
        on="area_code",
        how="inner",
        validate="one_to_one",
    )
    alignment["selected_measure"] = alignment[selected_alignment_measure]
    need_median = float(alignment["social_need_score"].median())
    measure_median = float(alignment["selected_measure"].median())
    alignment["alignment_group"] = alignment.apply(
        need_activity_group,
        axis=1,
        need_median=need_median,
        measure_median=measure_median,
    )
    alignment_group_order = [
        "High need / lower contribution",
        "High need / higher contribution",
        "Lower need / higher contribution",
        "Lower need / lower contribution",
    ]
    alignment_group_colours = {
        "High need / lower contribution": "#c84343",
        "High need / higher contribution": "#e58a2b",
        "Lower need / higher contribution": "#087e8b",
        "Lower need / lower contribution": "#9aa5b1",
    }

    alignment_map = px.choropleth(
        alignment,
        geojson=boundaries["rgn_2019"],
        locations="area_code",
        featureidkey="properties.rgn19cd",
        color="alignment_group",
        color_discrete_map=alignment_group_colours,
        category_orders={"alignment_group": alignment_group_order},
        hover_name="area_name",
        hover_data={
            "area_code": True,
            "social_need_score": ":.1f",
            "selected_measure": ":.1f",
            "alignment_group": False,
        },
        projection="mercator",
        labels={
            "social_need_score": "Social Need Score",
            "selected_measure": alignment_measure_labels[selected_alignment_measure],
            "alignment_group": "Need-contribution pattern",
        },
    )
    alignment_map.update_layout(
        height=610,
        margin={"r": 0, "t": 4, "l": 0, "b": 0},
        showlegend=False,
    )
    alignment_map.update_geos(
        fitbounds="locations",
        resolution=50,
        showframe=False,
        showcoastlines=True,
        coastlinecolor="#aab4bc",
        showland=True,
        landcolor="#f7f8f9",
        showocean=True,
        oceancolor="#d7dfe3",
        bgcolor="#d7dfe3",
    )
    alignment_map.update_traces(marker_line_width=0.3, marker_line_color="#697582")

    selected_alignment = alignment[
        alignment["area_name"] == selected_area_name
    ].iloc[0]
    alignment_map_column, alignment_detail_column = st.columns([2.15, 1])
    with alignment_map_column:
        st.plotly_chart(
            alignment_map,
            width="stretch",
            config={
                "displayModeBar": False,
                "doubleClick": False,
                "scrollZoom": False,
                "staticPlot": True,
            },
        )
        st.markdown(
            """
            <div class="map-legend">
                <div class="map-legend-title">Need-contribution pattern</div>
                <div class="map-legend-item"><span class="map-legend-swatch" style="background:#c84343"></span>High need / lower contribution</div>
                <div class="map-legend-item"><span class="map-legend-swatch" style="background:#e58a2b"></span>High need / higher contribution</div>
                <div class="map-legend-item"><span class="map-legend-swatch" style="background:#087e8b"></span>Lower need / higher contribution</div>
                <div class="map-legend-item"><span class="map-legend-swatch" style="background:#9aa5b1"></span>Lower need / lower contribution</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with alignment_detail_column:
        st.subheader(selected_area_name)
        st.metric(
            "Social Need Score",
            f"{selected_alignment['social_need_score']:.1f}",
        )
        st.metric(
            alignment_measure_labels[selected_alignment_measure],
            f"{selected_alignment['selected_measure']:.1f}",
        )
        st.markdown(
            f"""
            <div class="detail-box">
                <div class="detail-label">Need-contribution pattern</div>
                <div class="detail-value" style="font-size:1.05rem">{selected_alignment['alignment_group']}</div>
            </div>
            <div class="method-note">
            <strong>Classification:</strong> higher/lower is determined against the
            median across the nine English regions. This is a screening method, not
            a causal impact assessment.
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div class="section-heading">Check the relationship, not only the categories</div>',
        unsafe_allow_html=True,
    )
    alignment_scatter = px.scatter(
        alignment,
        x="social_need_score",
        y="selected_measure",
        text="area_name",
        color="alignment_group",
        color_discrete_map=alignment_group_colours,
        category_orders={"alignment_group": alignment_group_order},
        hover_name="area_name",
        hover_data={
            "area_code": True,
            "social_need_score": ":.1f",
            "selected_measure": ":.1f",
            "alignment_group": False,
        },
        labels={
            "social_need_score": "Composite Social Need Score",
            "selected_measure": alignment_measure_labels[selected_alignment_measure],
            "alignment_group": "Need-contribution pattern",
        },
    )
    alignment_scatter.add_vline(
        x=need_median,
        line_dash="dash",
        line_color="#8b96a3",
    )
    alignment_scatter.add_hline(
        y=measure_median,
        line_dash="dash",
        line_color="#8b96a3",
    )
    alignment_scatter.update_traces(marker={"size": 14}, textposition="top center")
    alignment_scatter.update_layout(
        height=520,
        margin={"r": 20, "t": 25, "l": 20, "b": 10},
        showlegend=False,
    )
    st.plotly_chart(
        alignment_scatter,
        width="stretch",
        config={"displayModeBar": False},
    )

    st.markdown(
        '<div class="section-heading">Regional screening order</div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Regions are grouped by need-contribution pattern. Within each group, "
        "regions with the higher Social Need Score appear first."
    )
    priority_table = alignment[
        [
            "area_name",
            "social_need_score",
            "selected_measure",
            "alignment_group",
        ]
    ].copy()
    pattern_priority = {
        "High need / lower contribution": 1,
        "High need / higher contribution": 2,
        "Lower need / lower contribution": 3,
        "Lower need / higher contribution": 4,
    }
    priority_table["pattern_priority"] = priority_table["alignment_group"].map(
        pattern_priority
    )
    priority_table = priority_table.sort_values(
        ["pattern_priority", "social_need_score"],
        ascending=[True, False],
    ).drop(columns="pattern_priority")
    st.dataframe(
        priority_table,
        width="stretch",
        hide_index=True,
        column_config={
            "area_name": "Region",
            "social_need_score": st.column_config.NumberColumn(
                "Social Need Score", format="%.1f"
            ),
            "selected_measure": st.column_config.NumberColumn(
                alignment_measure_labels[selected_alignment_measure], format="%.1f"
            ),
            "alignment_group": "Pattern",
        },
    )

with fusion21_tab:
    st.markdown(
        '<div class="section-heading">Fusion21 regional contribution scores</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="warning-note">
        <strong>Synthetic demonstration data:</strong> these records were generated
        to test the pipeline before anonymised Fusion21 data is available. They show
        how procurement, recorded activities and Foundation investment can be
        processed, but they are not evidence of real social impact.
        </div>
        """,
        unsafe_allow_html=True,
    )

    fusion21_score_labels = {
        "contribution_score": "Composite Contribution Score",
        "procurement_score": "Procurement Score",
        "activity_score": "Activity Score",
        "foundation_score": "Foundation Score",
    }
    selected_fusion21_score = st.selectbox(
        "Fusion21 indicator",
        list(fusion21_score_labels),
        format_func=lambda column: fusion21_score_labels[column],
        key="fusion21_score_selector",
    )

    fusion21_map_data = synthetic_region_summary[
        ["area_code", "area_name", selected_fusion21_score]
    ].rename(columns={selected_fusion21_score: "value"})
    fusion21_figure = px.choropleth(
        fusion21_map_data,
        geojson=boundaries["rgn_2019"],
        locations="area_code",
        featureidkey="properties.rgn19cd",
        color="value",
        range_color=(0, 100),
        color_continuous_scale="Viridis",
        hover_name="area_name",
        hover_data={"area_code": True, "value": ":.1f"},
        projection="mercator",
        labels={"value": fusion21_score_labels[selected_fusion21_score]},
    )
    fusion21_figure.update_layout(
        height=610,
        margin={"r": 0, "t": 4, "l": 0, "b": 0},
        coloraxis_colorbar={
            "title": fusion21_score_labels[selected_fusion21_score],
            "thickness": 14,
            "len": 0.7,
        },
    )
    fusion21_figure.update_geos(
        fitbounds="locations",
        resolution=50,
        showframe=False,
        showcoastlines=True,
        coastlinecolor="#aab4bc",
        showland=True,
        landcolor="#f7f8f9",
        showocean=True,
        oceancolor="#d7dfe3",
        bgcolor="#d7dfe3",
    )
    fusion21_figure.update_traces(
        marker_line_width=0.3,
        marker_line_color="#697582",
    )

    fusion21_map_column, fusion21_detail_column = st.columns([2.15, 1])
    with fusion21_map_column:
        st.plotly_chart(
            fusion21_figure,
            width="stretch",
            config={
                "displayModeBar": False,
                "doubleClick": False,
                "scrollZoom": False,
                "staticPlot": True,
            },
        )

    selected_fusion21_region = synthetic_region_summary[
        synthetic_region_summary["area_name"] == selected_area_name
    ].iloc[0]
    with fusion21_detail_column:
        st.subheader(selected_area_name)
        st.metric(
            "Composite Contribution Score",
            f"{selected_fusion21_region['contribution_score']:.1f}",
        )
        st.metric(
            "Procurement Score",
            f"{selected_fusion21_region['procurement_score']:.1f}",
        )
        st.metric(
            "Activity Score",
            f"{selected_fusion21_region['activity_score']:.1f}%",
        )
        st.metric(
            "Foundation Score",
            f"{selected_fusion21_region['foundation_score']:.1f}",
        )
        st.markdown(
            f"""
            <div class="detail-box">
                <div class="detail-label">Recorded contract value</div>
                <div class="detail-value">{format_money(float(selected_fusion21_region['contract_value']))}</div>
            </div>
            <div class="detail-box">
                <div class="detail-label">Recorded Foundation investment</div>
                <div class="detail-value">{format_money(float(selected_fusion21_region['foundation_investment']))}</div>
            </div>
            <div class="detail-box">
                <div class="detail-label">Recorded activities</div>
                <div class="detail-value">{int(selected_fusion21_region['recorded_activity_count'])} / {int(selected_fusion21_region['activity_possible_count'])}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    activity_columns = {
        "decarbonisation_count": "Decarbonisation / renewable energy",
        "waste_reduction_count": "Waste reduction",
        "water_reduction_count": "Water reduction",
        "local_ecosystems_count": "Local ecosystems",
        "community_engagement_count": "Community engagement",
        "green_skills_count": "Green skills training",
    }
    activity_breakdown = pd.DataFrame(
        {
            "Activity": list(activity_columns.values()),
            "Recorded Yes": [
                int(selected_fusion21_region[column]) for column in activity_columns
            ],
        }
    ).sort_values("Recorded Yes")
    activity_figure = px.bar(
        activity_breakdown,
        x="Recorded Yes",
        y="Activity",
        orientation="h",
        text="Recorded Yes",
        color_discrete_sequence=["#087e8b"],
    )
    activity_figure.update_traces(textposition="outside", cliponaxis=False)
    activity_figure.update_layout(
        height=360,
        margin={"r": 25, "t": 20, "l": 10, "b": 10},
        xaxis_title="Number of projects with a recorded Yes",
        yaxis_title=None,
        showlegend=False,
    )
    st.markdown(
        f'<div class="section-heading">Recorded activity types in {selected_area_name}</div>',
        unsafe_allow_html=True,
    )
    st.plotly_chart(
        activity_figure,
        width="stretch",
        config={"displayModeBar": False},
    )

    fusion21_ranking = synthetic_region_summary[
        [
            "area_name",
            "contract_value",
            "recorded_activity_count",
            "activity_possible_count",
            "foundation_investment",
            "procurement_score",
            "activity_score",
            "foundation_score",
            "contribution_score",
        ]
    ].sort_values("contribution_score", ascending=False)
    st.dataframe(
        fusion21_ranking,
        width="stretch",
        hide_index=True,
        column_config={
            "area_name": "Region",
            "contract_value": st.column_config.NumberColumn(
                "Contract Value", format="£%.0f"
            ),
            "recorded_activity_count": "Activity Yes",
            "activity_possible_count": "Activity Total",
            "foundation_investment": st.column_config.NumberColumn(
                "Foundation Amount", format="£%.0f"
            ),
            "procurement_score": st.column_config.NumberColumn(
                "Procurement Score", format="%.1f"
            ),
            "activity_score": st.column_config.NumberColumn(
                "Activity Score", format="%.1f%%"
            ),
            "foundation_score": st.column_config.NumberColumn(
                "Foundation Score", format="%.1f"
            ),
            "contribution_score": st.column_config.NumberColumn(
                "Composite Score", format="%.1f"
            ),
        },
    )
    st.markdown(
        """
        <div class="method-note">
        <strong>Score calculation</strong><br>
        Procurement Score = regional contract value converted to a 0-100 Min-Max
        scale.<br>
        Activity Score = recorded Yes answers ÷ all six possible activity answers
        across projects × 100.<br>
        Foundation Score = regional Foundation investment converted to a 0-100
        Min-Max scale.<br>
        Composite Contribution Score = equal average of the three scores.
        </div>
        """,
        unsafe_allow_html=True,
    )

    selected_projects = synthetic_projects[
        synthetic_projects["area_name"] == selected_area_name
    ][
        [
            "contract_id",
            "framework",
            "start_date",
            "contract_value",
            "activity_count",
            "primary_activity",
            "foundation_investment",
        ]
    ].sort_values("contract_value", ascending=False)
    with st.expander(f"View synthetic project records for {selected_area_name}"):
        st.dataframe(
            selected_projects,
            width="stretch",
            hide_index=True,
            column_config={
                "contract_id": "Contract ID",
                "framework": "Framework",
                "start_date": "Start date",
                "contract_value": st.column_config.NumberColumn(
                    "Contract value", format="£%.0f"
                ),
                "activity_count": "Activity Yes",
                "primary_activity": "Primary activity",
                "foundation_investment": st.column_config.NumberColumn(
                    "Foundation investment", format="£%.0f"
                ),
            },
        )

with compare_tab:
    st.markdown(
        '<div class="section-heading">Deprivation compared with unemployment</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="section-copy">
        The scatter plot keeps both measures separate. Regions further right have
        stronger relative deprivation; regions higher on the chart have a higher
        unemployment rate. Median lines provide a simple reference without forcing
        nine regions into unstable quintile groups.
        </div>
        """,
        unsafe_allow_html=True,
    )

    comparison = (
        latest[latest["indicator_id"].isin(required_indicators)]
        .pivot_table(
            index=["area_code", "area_name"],
            columns="indicator_id",
            values="value",
            aggfunc="first",
        )
        .reset_index()
        .rename(
            columns={
                IMD_INDICATOR: "imd_need",
                UNEMPLOYMENT_INDICATOR: "unemployment_rate",
                COMPOSITE_NEED_INDICATOR: "composite_need",
            }
        )
        .dropna(subset=["imd_need", "unemployment_rate"])
    )
    imd_median = float(comparison["imd_need"].median())
    unemployment_median = float(comparison["unemployment_rate"].median())
    comparison["comparison_group"] = comparison.apply(
        comparison_group,
        axis=1,
        imd_median=imd_median,
        unemployment_median=unemployment_median,
    )

    group_colours = {
        "Higher on both": "#c84343",
        "Higher deprivation only": "#e66b3d",
        "Higher unemployment only": "#087e8b",
        "Lower on both": "#8592a3",
    }
    scatter = px.scatter(
        comparison,
        x="imd_need",
        y="unemployment_rate",
        text="area_name",
        color="comparison_group",
        color_discrete_map=group_colours,
        hover_name="area_name",
        hover_data={
            "area_code": True,
            "imd_need": ":.1f",
            "unemployment_rate": ":.1f",
            "composite_need": ":.1f",
            "comparison_group": False,
        },
        labels={
            "imd_need": "Population-weighted relative deprivation index",
            "unemployment_rate": "Unemployment rate (%)",
            "composite_need": "Composite social need score",
            "comparison_group": "Pattern",
        },
    )
    scatter.add_vline(x=imd_median, line_dash="dash", line_color="#8b96a3")
    scatter.add_hline(
        y=unemployment_median,
        line_dash="dash",
        line_color="#8b96a3",
    )
    scatter.update_traces(marker={"size": 13}, textposition="top center")
    scatter.update_layout(
        height=570,
        margin={"r": 20, "t": 35, "l": 20, "b": 10},
        legend_title_text="Regional pattern",
    )

    chart_column, interpretation_column = st.columns([2.2, 1])
    with chart_column:
        st.plotly_chart(
            scatter,
            width="stretch",
            config={"displayModeBar": False},
        )

    with interpretation_column:
        st.subheader("How to use this view")
        st.markdown(
            """
            <div class="method-note">
            <strong>Start with regions higher on both measures.</strong><br>
            These regions show stronger need across two different public indicators
            and can be reviewed first when Fusion21 activity data becomes available.
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div class="warning-note">
            <strong>The composite is an exploratory score.</strong><br>
            The two measures are first put on the same 0-100 scale and then combined
            with equal weights. IMD already contains an Employment Deprivation Domain,
            so this scatter plot remains important for checking possible overlap.
            </div>
            """,
            unsafe_allow_html=True,
        )
        selected_comparison = comparison[
            comparison["area_name"] == selected_area_name
        ].iloc[0]
        st.markdown(
            f"""
            <div class="detail-box">
                <div class="detail-label">{selected_area_name}</div>
                <div class="detail-value">{selected_comparison['comparison_group']}</div>
            </div>
            <div class="detail-box">
                <div class="detail-label">Composite social need score</div>
                <div class="detail-value">{selected_comparison['composite_need']:.1f}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    comparison_table = comparison[
        [
            "area_name",
            "imd_need",
            "unemployment_rate",
            "composite_need",
            "comparison_group",
        ]
    ].sort_values("composite_need", ascending=False)
    st.dataframe(
        comparison_table,
        width="stretch",
        hide_index=True,
        column_config={
            "area_name": "Region",
            "imd_need": st.column_config.NumberColumn(
                "Relative deprivation index", format="%.1f"
            ),
            "unemployment_rate": st.column_config.NumberColumn(
                "Unemployment rate", format="%.1f%%"
            ),
            "composite_need": st.column_config.NumberColumn(
                "Composite social need", format="%.1f"
            ),
            "comparison_group": "Pattern",
        },
    )
