from __future__ import annotations

import re

import pandas as pd
import plotly.express as px
import streamlit as st


from data_loader import load_processed_data


IMD_INDICATOR = "imd2019_need"
UNEMPLOYMENT_INDICATOR = "unemployment_rate_lfs"
COMPOSITE_NEED_INDICATOR = "social_need_composite"

INDICATOR_NAMES = {
    COMPOSITE_NEED_INDICATOR: "Raw social need index",
    IMD_INDICATOR: "Population-weighted mean IMD score",
    UNEMPLOYMENT_INDICATOR: "Regional unemployment rate",
}

INDICATOR_SHORT_NAMES = {
    COMPOSITE_NEED_INDICATOR: "Raw need index",
    IMD_INDICATOR: "Mean IMD score",
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
        from pipeline import build_all_data

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


def add_relative_tertile(
    frame: pd.DataFrame, value_column: str, output_column: str
) -> pd.DataFrame:
    """Assign low, medium and high bands by regional rank."""
    result = frame.copy()
    ordered = result.sort_values(
        [value_column, "area_name"], ascending=[True, True], kind="mergesort"
    )
    positions = pd.Series(range(len(ordered)), index=ordered.index)
    ordered[output_column] = pd.qcut(
        positions, q=3, labels=["Low", "Medium", "High"]
    ).astype(str)
    result[output_column] = ordered[output_column]
    return result


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
    It retains both observed inputs and provides a simple raw social need index for
    regional comparison without converting the nine regions to a 0-100 scale.
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

map_tab, alignment_tab, fusion21_tab = st.tabs(
    [
        "Social need map",
        "Need vs contribution",
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
        "mean_imd_score": ":,.1f",
        "unemployment_rate": ":,.1f",
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
            "mean_imd_score": "Population-weighted mean IMD score",
            "unemployment_rate": "Unemployment rate (%)",
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
                    <div class="detail-label">Population-weighted mean IMD score</div>
                    <div class="detail-value">{selected_area['mean_imd_score']:,.1f}</div>
                </div>
                <div class="detail-box">
                    <div class="detail-label">Regional unemployment rate</div>
                    <div class="detail-value">{selected_area['unemployment_rate']:,.1f}%</div>
                </div>
                <div class="method-note">
                <strong>Formula:</strong> (population-weighted mean IMD score +
                unemployment rate) / 2. The inputs are not standardised. Because
                their numerical ranges differ, this is a simple exploratory index,
                not a percentage or a claim of equal influence.
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
            ranking_columns.extend(["mean_imd_score", "unemployment_rate"])
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
                    "mean_imd_score": st.column_config.NumberColumn(
                        "Mean IMD score", format="%.1f"
                    ),
                    "unemployment_rate": st.column_config.NumberColumn(
                        "Unemployment rate", format="%.1f%%"
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
        '<div class="section-heading">Compare composite social need and contribution</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="section-copy">
        The two maps use the same English-region boundaries. The left map shows the
        Composite Social Need Score and the right map shows the Composite Social
        Contribution Score, allowing the spatial patterns to be compared directly.
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="warning-note">
        <strong>Demonstration only:</strong> all Fusion21 contribution records are
        synthetic. The comparison tests the method and interface; it does not
        evaluate Fusion21's real performance or prove social impact.
        </div>
        """,
        unsafe_allow_html=True,
    )

    social_need_latest = latest[
        latest["indicator_id"] == COMPOSITE_NEED_INDICATOR
    ][["area_code", "area_name", "value"]].rename(
        columns={"value": "composite_need_score"}
    )
    alignment = social_need_latest.merge(
        synthetic_region_summary[
            [
                "area_code",
                "contribution_score",
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
    alignment = add_relative_tertile(
        alignment, "composite_need_score", "need_band"
    )
    alignment = add_relative_tertile(
        alignment, "contribution_score", "contribution_band"
    )
    alignment["priority_review"] = (
        (alignment["need_band"] == "High")
        & (alignment["contribution_band"] == "Low")
    )
    alignment["comparison_pattern"] = "Other regional pattern"
    alignment.loc[
        (alignment["need_band"] == "High")
        & (alignment["contribution_band"] == "High"),
        "comparison_pattern",
    ] = "High need / high contribution"
    alignment.loc[
        (alignment["need_band"] == "High")
        & (alignment["contribution_band"] == "Medium"),
        "comparison_pattern",
    ] = "High need / medium contribution"
    alignment.loc[
        alignment["priority_review"], "comparison_pattern"
    ] = "Priority review: high need / low contribution"
    alignment["screening_result"] = alignment["priority_review"].map(
        {True: "Priority review", False: "Not priority review"}
    )
    selected_alignment = alignment[
        alignment["area_name"] == selected_area_name
    ].iloc[0]
    st.markdown(
        f'<div class="section-heading">Selected region: {selected_area_name}</div>',
        unsafe_allow_html=True,
    )
    selected_need_column, selected_contribution_column, selected_status_column = (
        st.columns(3)
    )
    with selected_need_column:
        st.metric(
            "Composite Social Need Score",
            f"{selected_alignment['composite_need_score']:.1f}",
        )
    with selected_contribution_column:
        st.metric(
            "Composite Social Contribution Score",
            f"{selected_alignment['contribution_score']:.1f}",
        )
    with selected_status_column:
        st.metric("Priority screening", selected_alignment["screening_result"])
        st.caption(
            f"Need: {selected_alignment['need_band']} · "
            f"Contribution: {selected_alignment['contribution_band']}"
        )

    need_map = px.choropleth(
        alignment,
        geojson=boundaries["rgn_2019"],
        locations="area_code",
        featureidkey="properties.rgn19cd",
        color="composite_need_score",
        range_color=(
            float(alignment["composite_need_score"].min()),
            float(alignment["composite_need_score"].max()),
        ),
        color_continuous_scale=[
            [0.0, "#fff4e6"],
            [0.5, "#f28e4b"],
            [1.0, "#b42338"],
        ],
        hover_name="area_name",
        hover_data={"area_code": True, "composite_need_score": ":.1f"},
        projection="mercator",
        labels={"composite_need_score": "Composite Social Need Score"},
    )
    contribution_map = px.choropleth(
        alignment,
        geojson=boundaries["rgn_2019"],
        locations="area_code",
        featureidkey="properties.rgn19cd",
        color="contribution_score",
        range_color=(0, 100),
        color_continuous_scale=[
            [0.0, "#e8f3f3"],
            [0.5, "#55a6a9"],
            [1.0, "#006b73"],
        ],
        hover_name="area_name",
        hover_data={"area_code": True, "contribution_score": ":.1f"},
        projection="mercator",
        labels={"contribution_score": "Composite Social Contribution Score"},
    )
    for figure, title in (
        (need_map, "Social need"),
        (contribution_map, "Social contribution"),
    ):
        figure.update_layout(
            height=500,
            margin={"r": 0, "t": 42, "l": 0, "b": 74},
            title={"text": title, "x": 0.02, "xanchor": "left"},
            coloraxis_colorbar={
                "orientation": "h",
                "thickness": 10,
                "len": 0.82,
                "x": 0.5,
                "xanchor": "center",
                "y": -0.08,
                "yanchor": "top",
            },
        )
        figure.update_geos(
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
        figure.update_traces(marker_line_width=0.35, marker_line_color="#697582")

    need_map_column, contribution_map_column = st.columns(2)
    chart_config = {
        "displayModeBar": False,
        "doubleClick": False,
        "scrollZoom": False,
        "staticPlot": True,
    }
    with need_map_column:
        st.plotly_chart(need_map, width="stretch", config=chart_config)
    with contribution_map_column:
        st.plotly_chart(contribution_map, width="stretch", config=chart_config)

    st.markdown(
        """
        <div class="method-note">
        <strong>How to read the maps:</strong> compare where darker areas appear in
        each map, then use the table below for the exact scores. The colour scales
        are separate because the two composite scores use different project scales;
        the scores are not subtracted and the difference is not an impact measure.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-heading">High-need, low-contribution priority map</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="section-copy">
        This screening layer applies the retained bivariate method. The three regions
        with the highest need scores form the High need band, and the three regions
        with the lowest contribution scores form the Low contribution band. Their
        overlap is highlighted for priority review.
        </div>
        """,
        unsafe_allow_html=True,
    )
    priority_map = px.choropleth(
        alignment,
        geojson=boundaries["rgn_2019"],
        locations="area_code",
        featureidkey="properties.rgn19cd",
        color="comparison_pattern",
        category_orders={
            "comparison_pattern": [
                "Priority review: high need / low contribution",
                "High need / medium contribution",
                "High need / high contribution",
                "Other regional pattern",
            ]
        },
        color_discrete_map={
            "Priority review: high need / low contribution": "#b42338",
            "High need / medium contribution": "#f28e4b",
            "High need / high contribution": "#087e8b",
            "Other regional pattern": "#d7dde2",
        },
        hover_name="area_name",
        hover_data={
            "area_code": True,
            "composite_need_score": ":.1f",
            "need_band": True,
            "contribution_score": ":.1f",
            "contribution_band": True,
            "comparison_pattern": False,
        },
        projection="mercator",
        labels={
            "comparison_pattern": "Screening result",
            "composite_need_score": "Need score",
            "need_band": "Need band",
            "contribution_score": "Contribution score",
            "contribution_band": "Contribution band",
        },
    )
    priority_map.update_geos(
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
    priority_map.update_traces(marker_line_width=0.45, marker_line_color="#697582")
    priority_map.update_layout(
        height=570,
        margin={"r": 0, "t": 8, "l": 0, "b": 90},
        legend={
            "orientation": "h",
            "y": -0.08,
            "yanchor": "top",
            "x": 0.5,
            "xanchor": "center",
            "title": None,
        },
    )
    st.plotly_chart(priority_map, width="stretch", config=chart_config)
    priority_count = int(alignment["priority_review"].sum())
    st.markdown(
        f"""
        <div class="warning-note">
        <strong>Screening result:</strong> {priority_count} of the nine regions are
        currently marked for priority review. This is a relative comparison using
        synthetic contribution data; it is a prompt for discussion, not evidence of
        poor performance or a causal impact gap.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-heading">Exact regional values</div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "The table is ordered by Composite Social Need Score so the exact values "
        "behind both maps can be checked."
    )
    comparison_table = alignment[
        [
            "area_name",
            "composite_need_score",
            "need_band",
            "contribution_score",
            "contribution_band",
            "screening_result",
        ]
    ].sort_values("composite_need_score", ascending=False)
    st.dataframe(
        comparison_table,
        width="stretch",
        hide_index=True,
        column_config={
            "area_name": "Region",
            "composite_need_score": st.column_config.NumberColumn(
                "Composite Social Need Score", format="%.1f"
            ),
            "contribution_score": st.column_config.NumberColumn(
                "Composite Social Contribution Score", format="%.1f"
            ),
            "need_band": "Need band",
            "contribution_band": "Contribution band",
            "screening_result": "Screening result",
        },
    )

with fusion21_tab:
    st.markdown(
        '<div class="section-heading">Fusion21 regional data and social contribution scores</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="warning-note">
        <strong>Synthetic demonstration data:</strong> these records were generated
        to test the pipeline before anonymised Fusion21 data is available. They show
        how procurement footprint, recorded activities and Foundation investment can
        be processed. Contract value is shown separately and is not treated as social
        contribution; none of the synthetic records is evidence of real social impact.
        </div>
        """,
        unsafe_allow_html=True,
    )

    fusion21_score_labels = {
        "contribution_score": "Composite Social Contribution Score",
        "contract_value": "Procurement footprint (contract value)",
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
    fusion21_map_range = (
        (0, float(fusion21_map_data["value"].max()))
        if selected_fusion21_score == "contract_value"
        else (0, 100)
    )
    fusion21_value_format = (
        ":,.0f" if selected_fusion21_score == "contract_value" else ":.1f"
    )
    fusion21_figure = px.choropleth(
        fusion21_map_data,
        geojson=boundaries["rgn_2019"],
        locations="area_code",
        featureidkey="properties.rgn19cd",
        color="value",
        range_color=fusion21_map_range,
        color_continuous_scale="Viridis",
        hover_name="area_name",
        hover_data={"area_code": True, "value": fusion21_value_format},
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
    if selected_fusion21_score == "contract_value":
        fusion21_figure.update_coloraxes(colorbar_tickprefix="£")
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
            "Composite Social Contribution Score",
            f"{selected_fusion21_region['contribution_score']:.1f}",
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
            "activity_score": st.column_config.NumberColumn(
                "Activity Score", format="%.1f%%"
            ),
            "foundation_score": st.column_config.NumberColumn(
                "Foundation Score", format="%.1f"
            ),
            "contribution_score": st.column_config.NumberColumn(
                "Composite Social Contribution Score", format="%.1f"
            ),
        },
    )
    st.markdown(
        """
        <div class="method-note">
        <strong>Score calculation</strong><br>
        Procurement footprint = total regional contract value. It is shown separately
        and is not included in the Social Contribution Score.<br>
        Activity Score = recorded Yes answers ÷ all six possible activity answers
        across projects × 100.<br>
        Foundation Score = regional Foundation investment converted to a 0-100
        Min-Max scale.<br>
        Composite Social Contribution Score = (Activity Score + Foundation Score) ÷ 2.
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
