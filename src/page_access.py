"""
page_access.py  —  improved version
Changes vs original:
  • Transport modes: section now correctly filters split=="mode" rows and
    falls back gracefully if data is missing.
  • Accessibility section: clearer, friendlier chart titles and inline
    explanations; the "travel gap" metric renamed to avoid the confusing
    double-negative ("further than willing → access gap").
  • Composite section: plain-English description added above the chart.
  • Section captions rewritten throughout for clarity.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from src.fem_colours import FEM_ORANGE, FEM_BROWN, FEM_TAUPE, FEM_STEEL, FEM_NAVY
from src.data_loader import (
    load_access_stockouts,
    load_access_stockout_responses,
    load_access_travel,
    load_access_affordability,
    load_access_composite,
)

FEM_PALETTE = [FEM_ORANGE, FEM_BROWN, FEM_TAUPE, FEM_STEEL, FEM_NAVY]

SPLIT_MAP = {
    "User group": "use",
    "Gender":     "gender",
    "Age group":  "age_group",
}

_MISSING = (
    "Pre-aggregated data not found. "
    "Run `python pipeline/run_pipeline.py --pages access` to generate it."
)


# ── Generic chart helpers ─────────────────────────────────────────────────────

def _hbar(series, title, pct=True, caption=None, key=None):
    if series is None or series.empty:
        if caption:
            st.caption(f"_{caption}_")
        return
    colors = (FEM_PALETTE * (len(series) // len(FEM_PALETTE) + 1))[:len(series)]
    text = [f"{v*100:.1f}%" if pct else f"{v:.1f}" for v in series.values]
    fig = go.Figure(go.Bar(
        y=series.index.astype(str),
        x=series.values,
        orientation="h",
        marker_color=colors,
        text=text,
        textposition="outside",
        cliponaxis=False,
    ))
    fig.update_layout(
        title=title,
        xaxis=dict(
            tickformat=".0%" if pct else "",
            showgrid=False,
            range=[0, series.max() * 1.35] if len(series) else [0, 1],
        ),
        yaxis=dict(showgrid=False, autorange="reversed"),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=80, t=36, b=10),
        height=max(200, len(series) * 44 + 80),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True, key=key)
    if caption:
        st.caption(caption)


def _get_metric(df_long, metric, split_col):
    if df_long is None or df_long.empty:
        return pd.Series(dtype=float)
    sub = df_long[(df_long["metric"] == metric) & (df_long["split"] == split_col)]
    return sub.set_index("group")["value"].dropna()


def _get_scalar(df_long, metric):
    if df_long is None or df_long.empty:
        return np.nan
    sub = df_long[
        (df_long["metric"] == metric) &
        (df_long["split"] == "all") &
        (df_long["group"] == "all")
    ]
    return sub["value"].iloc[0] if not sub.empty else np.nan


# ── Section renderers ─────────────────────────────────────────────────────────

def render_availability(df_stockouts, df_responses, split_col):
    st.subheader("1. Availability — are contraceptives in stock?")
    st.caption(
        "A stockout happens when someone visits a facility but the "
        "contraceptive they need is unavailable. "
        "Users/past users and non-users/future users were asked separate questions."
    )
    if df_stockouts is None:
        st.warning(_MISSING)
        return

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Current & past users**")
        _hbar(
            _get_metric(df_stockouts, "stockout_users", split_col),
            "Experienced a stockout",
            caption="Share of current/past users who found their method out-of-stock.",
            key="avail_users",
        )
        if df_responses is not None:
            sub = df_responses[df_responses["group"] == "users"]
            if not sub.empty:
                with st.expander("How did users respond to stockouts?"):
                    st.dataframe(
                        sub[["response", "count"]].reset_index(drop=True),
                        use_container_width=True,
                        hide_index=True,
                    )

    with col2:
        st.markdown("**Non-users & future users**")
        _hbar(
            _get_metric(df_stockouts, "sought_contraceptives", split_col),
            "Sought contraceptives",
            caption="Share who actively tried to access contraceptives.",
            key="avail_sought",
        )
        _hbar(
            _get_metric(df_stockouts, "stockout_nonusers_sought", split_col),
            "Stockout rate (among those who sought)",
            caption="Of those who sought contraceptives, share who found them out-of-stock.",
            key="avail_nonusers",
        )
        if df_responses is not None:
            sub = df_responses[df_responses["group"] == "nonusers"]
            if not sub.empty:
                with st.expander("How did non-users respond to stockouts?"):
                    st.dataframe(
                        sub[["response", "count"]].reset_index(drop=True),
                        use_container_width=True,
                        hide_index=True,
                    )


def render_accessibility(df_travel, split_col):
    st.subheader("2. Accessibility — how far do people travel?")
    st.caption(
        "This section compares actual travel time to a facility against the maximum "
        "time respondents say they are *willing* to travel. "
        "When actual travel time exceeds willingness, it signals a distance barrier."
    )
    if df_travel is None:
        st.warning(_MISSING)
        return

    col1, col2 = st.columns(2)
    with col1:
        _hbar(
            _get_metric(df_travel, "mean_travel_users", split_col),
            "Average journey time — current/past users (minutes)",
            pct=False,
            caption="Mean one-way travel time to the facility where they obtain contraceptives.",
            key="travel_users",
        )
    with col2:
        _hbar(
            _get_metric(df_travel, "mean_travel_nonusers", split_col),
            "Average journey time — non-users (minutes)",
            pct=False,
            caption="Mean one-way travel time non-users would need to reach the nearest facility.",
            key="travel_nonusers",
        )

    st.markdown("**Distance access gap — travel time vs. willingness to travel**")
    st.caption(
        "For each group, the maximum time they say they're willing to travel next to "
        "their travel time (actual for current/past users, expected for non-users). "
        "Where travel time exceeds willingness, distance is a barrier. "
        "Non-users = everyone not a current/past user."
    )
    wtt = _get_metric(df_travel, "mean_wtt_by_group", "use_binary")
    travel = _get_metric(df_travel, "mean_travel_by_group", "use_binary")
    if wtt.empty or travel.empty:
        st.warning(
            "Willingness-to-travel comparison not available — `access_travel.csv` "
            "predates it. Run `python pipeline/run_pipeline.py --pages access` and "
            "re-upload `access_travel.csv` to Drive."
        )
    else:
        groups = [g for g in ["Current/past users", "Non-users"] if g in wtt.index or g in travel.index]
        fig = go.Figure([
            go.Bar(
                name=name, y=groups, x=[series.get(g) for g in groups],
                orientation="h", marker_color=color,
                text=[f"{series.get(g):.1f}" if pd.notna(series.get(g)) else "" for g in groups],
                textposition="outside", cliponaxis=False,
            )
            for name, series, color in [
                ("Willing to travel", wtt, FEM_TAUPE),
                ("Travel time", travel, FEM_ORANGE),
            ]
        ])
        fig.update_layout(
            barmode="group",
            xaxis=dict(title="Minutes (one way)", showgrid=False,
                       range=[0, max(wtt.max(), travel.max()) * 1.25]),
            yaxis=dict(showgrid=False, autorange="reversed"),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=10, r=40, t=20, b=10),
            height=260,
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )
        st.plotly_chart(fig, use_container_width=True, key="travel_vs_wtt")

    with st.expander("How do people get to facilities? (transport modes)"):
        c1, c2 = st.columns(2)
        found_any = False
        for label, cobj, key in [("users", c1, "tm_u"), ("nonusers", c2, "tm_nu")]:
            metric_name = f"transport_mode_{label}"
            # Try both "mode" and "split==none" as possible split keys
            sub = df_travel[
                (df_travel["metric"] == metric_name) &
                (df_travel["split"].isin(["mode", "none", split_col]))
            ]
            if sub.empty:
                # Fallback: any row with this metric
                sub = df_travel[df_travel["metric"] == metric_name]
            if not sub.empty:
                found_any = True
                s = sub.set_index("group")["value"].dropna()
                with cobj:
                    _hbar(s, f"Transport modes — {label}", key=key)
        if not found_any:
            st.info("Transport mode data not available in the aggregated dataset.")


def render_affordability(df_afford, split_col):
    st.subheader("3. Affordability — what do contraceptives cost?")
    st.caption(
        "For current/past users: actual out-of-pocket cost per contraceptive visit. "
        "For non-users/future users: expected cost of a visit (what they think it would cost)."
    )
    if df_afford is None:
        st.warning(_MISSING)
        return

    col1, col2 = st.columns(2)
    with col1:
        _hbar(
            _get_metric(df_afford, "mean_cost_users", split_col),
            "Average cost paid — current/past users (CFA francs)",
            pct=False,
            caption="Mean cost per contraceptive visit reported by current and past users.",
            key="cost_users",
        )
    with col2:
        _hbar(
            _get_metric(df_afford, "mean_cost_nonusers", split_col),
            "Expected visit cost — non-users (CFA francs)",
            pct=False,
            caption="Mean expected cost that non-users/future users anticipate paying.",
            key="cost_nonusers",
        )

    overall_cost = _get_scalar(df_afford, "cost_barrier_overall")
    if not np.isnan(overall_cost):
        st.metric(
            "Share of current/past users who paid anything",
            f"{overall_cost*100:.1f}%",
            help="Proportion of users for whom contraceptives are not free.",
        )


def render_composite(df_composite):
    st.subheader("4. Composite supply indicator")
    st.caption(
        "This chart brings together all three supply-side barriers — availability, "
        "accessibility, and affordability — into a single view. "
        "Each bar shows the share of respondents facing that particular barrier. "
        "A respondent 'faces' a barrier if they experienced a stockout, travel further "
        "than they are willing to, or paid for contraceptives."
    )
    if df_composite is None:
        st.warning(_MISSING)
        return

    overall = (
        df_composite[df_composite["use_group"] == "all"]
        .set_index("barrier")["rate"]
        .dropna()
    )
    if overall.empty:
        st.info("No composite data available.")
        return

    fig = go.Figure(go.Bar(
        x=overall.index,
        y=overall.values,
        marker_color=FEM_PALETTE[:len(overall)],
        text=[f"{v*100:.1f}%" for v in overall.values],
        textposition="outside",
    ))
    fig.update_layout(
        title="Share of respondents facing each supply barrier (all users)",
        yaxis=dict(
            tickformat=".0%",
            title="Proportion of respondents",
            showgrid=False,
            range=[0, overall.max() * 1.3] if not overall.empty else [0, 1],
        ),
        xaxis=dict(showgrid=False, title="Supply barrier"),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=40, b=60),
        height=340,
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True, key="composite")

    with st.expander("Barrier rates by user group"):
        breakdown = df_composite[df_composite["use_group"] != "all"].dropna(subset=["rate"])
        if not breakdown.empty:
            fig2 = px.bar(
                breakdown,
                x="barrier",
                y="rate",
                color="use_group",
                barmode="group",
                text=breakdown["rate"].apply(lambda v: f"{v*100:.1f}%"),
                color_discrete_sequence=FEM_PALETTE,
                labels={"barrier": "Supply barrier", "rate": "Proportion",
                        "use_group": "User group"},
            )
            fig2.update_layout(
                yaxis=dict(tickformat=".0%", title="Proportion", showgrid=False),
                xaxis=dict(showgrid=False),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                height=340,
                legend_title="User group",
            )
            st.plotly_chart(fig2, use_container_width=True, key="composite_grp")


# ── Main render ───────────────────────────────────────────────────────────────

def render():
    st.title("Access & Supply Barriers")
    st.caption(
        "This page analyses whether contraceptives are **available** when people "
        "seek them, **physically accessible** (travel distance), and **affordable**. "
        "Use the split selector below to break down all charts by user group, "
        "gender, or age group."
    )

    df_stockouts = load_access_stockouts()
    df_responses = load_access_stockout_responses()
    df_travel    = load_access_travel()
    df_afford    = load_access_affordability()
    df_composite = load_access_composite()

    split_by  = st.radio("Split all charts by", list(SPLIT_MAP.keys()), horizontal=True)
    split_col = SPLIT_MAP[split_by]

    st.divider()
    render_availability(df_stockouts, df_responses, split_col)
    st.divider()
    render_accessibility(df_travel, split_col)
    st.divider()
    render_affordability(df_afford, split_col)
    st.divider()
    render_composite(df_composite)
