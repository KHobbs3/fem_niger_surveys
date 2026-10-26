"""Phone Pulse — Campaign Exposure: Treatment vs Comparison."""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from src.data_loader import (
    load_pp_exposure_profile, load_pp_exposure_fp_awareness, load_pp_exposure_fp_use,
    load_pp_exposure_attitudes, load_pp_exposure_partner_norms,
)

FEM_NAVY   = "#2E3F52"
FEM_ORANGE = "#C1693A"
TREATMENT_LABEL = "Heard campaign (Treatment)"
COMPARISON_LABEL = "Did not hear FP ads (Comparison)"
GROUP_COLORS = {TREATMENT_LABEL: FEM_NAVY, COMPARISON_LABEL: FEM_ORANGE}
GROUP_ORDER = [TREATMENT_LABEL, COMPARISON_LABEL]

_CHART = dict(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")


def _pending(csv_name: str) -> None:
    st.info(
        f"Data pending: run `export_pp_app_data.py`, upload `{csv_name}.csv` to "
        f"Drive with link sharing on, then paste its file ID into `data_loader.py`."
    )


def _grouped_hbar(df: pd.DataFrame, title: str, xmax: float = 100) -> go.Figure:
    fig = go.Figure()
    n_cats = df["category"].nunique()
    for grp in GROUP_ORDER:
        sub = df[df["group"] == grp].sort_values("pct")
        if sub.empty:
            continue
        fig.add_trace(go.Bar(
            x=sub["pct"], y=sub["category"], orientation="h",
            name=grp, marker_color=GROUP_COLORS[grp],
            text=sub["pct"].map(lambda v: f"{v:.0f}%"),
            textposition="outside",
        ))
    fig.update_layout(
        **_CHART,
        title=title, barmode="group",
        xaxis_title="% of respondents",
        xaxis_range=[0, xmax + 15],
        height=max(250, 35 * n_cats * len(GROUP_ORDER) + 100),
        margin=dict(l=10, r=30, t=78, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.15, xanchor="right", x=1),
    )
    return fig


def render() -> None:
    st.markdown("### Phone Pulse — Campaign Exposure: Treatment vs Comparison")
    st.caption(
        "**Treatment** = listens to a FEM partner radio station (assigned to cover their "
        "settlement) — i.e. they said they hear the campaign. This holds even if they "
        "personally report not recalling FP-specific ad content. "
        "**Comparison** = everyone else who passed QA — not assigned to/listening to a FEM "
        "partner station, whether or not they listen to radio at all."
    )
    st.markdown("---")

    profile = load_pp_exposure_profile()
    if profile is None:
        _pending("pp_exposure_profile")
        return

    n_row = profile[profile["variable"] == "_n"]
    n_treatment = int(n_row[n_row["group"] == TREATMENT_LABEL]["count"].iloc[0]) if not n_row.empty else 0
    n_comparison = int(n_row[n_row["group"] == COMPARISON_LABEL]["count"].iloc[0]) if not n_row.empty else 0

    c1, c2 = st.columns(2)
    c1.metric("Treatment (heard campaign)", n_treatment)
    c2.metric("Comparison (everyone else)", n_comparison)

    if 0 < n_comparison < 30:
        st.warning(
            f"⚠ The Comparison group has only **{n_comparison}** respondents. Percentages "
            "below can swing wildly on a handful of answers (e.g. 1 respondent = "
            f"{100/n_comparison:.0f} percentage points) — treat any gap as suggestive, "
            "not conclusive, until more comparison-arm data comes in from later waves."
        )
    st.markdown("---")

    unmet = profile[profile["variable"] == "unmet_need_proxy"]

    m1, _ = st.columns(2)
    with m1:
        st.markdown("**Unmet need for contraception**")
        for _, r in unmet.iterrows():
            st.metric(r["group"], f"{r['pct']:.1f}%" if pd.notna(r["pct"]) else "—",
                      help=f"{int(r['count'])} respondents")

    st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs(
        ["FP method awareness", "Current FP use", "Attitudes", "Social norms"]
    )

    with tab1:
        df = load_pp_exposure_fp_awareness()
        if df is None:
            _pending("pp_exposure_fp_awareness")
        elif df.empty:
            st.info("No data available.")
        else:
            st.plotly_chart(_grouped_hbar(df, "Contraceptive method awareness"),
                             use_container_width=True)

    with tab2:
        df = load_pp_exposure_fp_use()
        if df is None:
            _pending("pp_exposure_fp_use")
        elif df.empty:
            st.info("No data available.")
        else:
            st.plotly_chart(_grouped_hbar(df, "Currently using a FP method"),
                             use_container_width=True)

    with tab3:
        df = load_pp_exposure_attitudes()
        if df is None:
            _pending("pp_exposure_attitudes")
        elif df.empty:
            st.info("No data available.")
        else:
            fig = go.Figure()
            for grp in GROUP_ORDER:
                sub = df[df["group"] == grp].dropna(subset=["mean"])
                if sub.empty:
                    continue
                fig.add_trace(go.Bar(
                    x=sub["mean"], y=sub["label"], orientation="h",
                    name=grp, marker_color=GROUP_COLORS[grp],
                    text=sub["mean"].map(lambda v: f"{v:.2f}"),
                    textposition="outside",
                ))
            fig.update_layout(
                **_CHART,
                title="Mean self-attitude scores (0–4 scale)",
                barmode="group",
                xaxis_title="Mean agreement (0 = Strongly disagree, 4 = Strongly agree)",
                xaxis_range=[0, 5],
                height=400,
                margin=dict(l=10, r=30, t=78, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.15, xanchor="right", x=1),
            )
            fig.add_vline(x=2, line_dash="dot", line_color="#aaa")
            st.plotly_chart(fig, use_container_width=True)
            st.caption("Dashed line at 2 = neutral midpoint.")

    with tab4:
        df = load_pp_exposure_partner_norms()
        if df is None:
            _pending("pp_exposure_partner_norms")
        elif df.empty:
            st.info("No data available.")
        else:
            fig = go.Figure()
            for grp in GROUP_ORDER:
                sub = df[df["group"] == grp].dropna(subset=["mean"])
                if sub.empty:
                    continue
                fig.add_trace(go.Bar(
                    x=sub["mean"], y=sub["label"], orientation="h",
                    name=grp, marker_color=GROUP_COLORS[grp],
                    text=sub["mean"].map(lambda v: f"{v:.2f}"),
                    textposition="outside",
                ))
            fig.update_layout(
                **_CHART,
                title="Mean agreement with social norm statements (0–4 scale)",
                barmode="group",
                xaxis_title="Mean agreement (0 = Strongly disagree, 4 = Strongly agree)",
                xaxis_range=[0, 5],
                height=350,
                margin=dict(l=10, r=30, t=78, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.15, xanchor="right", x=1),
            )
            fig.add_vline(x=2, line_dash="dot", line_color="#aaa")
            st.plotly_chart(fig, use_container_width=True)
