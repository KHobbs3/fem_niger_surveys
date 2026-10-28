import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from src.fem_colours import FEM_ORANGE, FEM_BROWN, FEM_TAUPE, FEM_STEEL, FEM_NAVY
from src.data_loader import (
    load_personality_life_goals,
    load_personality_goals_achievable,
    load_personality_role_models,
    load_personality_likeable_traits,
    load_personality_forming_beliefs,
    load_personality_decision_confident,
    load_personality_wellbeing,
)

FEM_PALETTE = [FEM_ORANGE, FEM_BROWN, FEM_TAUPE, FEM_STEEL, FEM_NAVY]

SPLIT_MAP = {
    "User group": "use",
    "Gender":     "gender",
    "Age group":  "age_group",
}

LIKERT_ORDER  = ["Toujours - tout le temps / Always - all the time", 
                "Souvent - la plupart des jours / Often – most days", 
                "Parfois - quelques jours / Sometimes – some days", 
                "Rarement / Rarely", 
                "Presque jamais / Almost never", 
                "Jamais - pas du tout / Never – not at all"]
LIKERT_COLORS = [FEM_ORANGE, FEM_BROWN, FEM_TAUPE, "#a0a0a0", FEM_STEEL, FEM_NAVY]

_MISSING = (
    "Pre-aggregated data not found. "
    "Run `python pipeline/run_pipeline.py --pages personality` to generate it."
)


# ── Chart helpers ─────────────────────────────────────────────────────────────

def _hbar(series, title, top_n=12, key=None):
    series = series.head(top_n)
    if series is None or series.empty:
        return
    colors = (FEM_PALETTE * (len(series) // len(FEM_PALETTE) + 1))[:len(series)]
    fig = go.Figure(go.Bar(
        y=series.index.astype(str),
        x=series.values,
        orientation="h",
        marker_color=colors,
        text=[f"{v*100:.1f}%" for v in series.values],
        textposition="outside",
        cliponaxis=False,
    ))
    fig.update_layout(
        title=title,
        xaxis=dict(showgrid=False, showticklabels=False,
                   range=[0, series.max() * 1.35] if len(series) else [0, 1]),
        yaxis=dict(showgrid=False, autorange="reversed"),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=80, t=36, b=10),
        height=max(200, len(series) * 34 + 60),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True, key=key)


def _grouped_bar(df_long, split_col, label_col, value_col, title,
                 top_n=10, key=None):
    if df_long is None or df_long.empty:
        return
    sub = df_long[df_long["split"] == split_col]
    if sub.empty:
        st.info("No data for this split.")
        return

    top_labels = (
        sub.groupby(label_col)[value_col].max()
        .nlargest(top_n).index.tolist()
    )
    sub = sub[sub[label_col].isin(top_labels)]
    groups = sorted(sub["group"].unique())

    traces = []
    for i, grp in enumerate(groups):
        gdf = sub[sub["group"] == grp].set_index(label_col)[value_col]
        traces.append(go.Bar(
            name=str(grp),
            x=gdf.index.astype(str),
            y=gdf.values,
            marker_color=FEM_PALETTE[i % len(FEM_PALETTE)],
            text=[f"{v*100:.0f}%" for v in gdf.values],
            textposition="outside",
        ))
    if not traces:
        return
    fig = go.Figure(traces)
    fig.update_layout(
        title=title,
        barmode="group",
        yaxis=dict(tickformat=".0%", showgrid=False, title="% of respondents"),
        xaxis=dict(showgrid=False, tickangle=-30),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=40, b=80, l=10, r=10),
        height=380,
        legend_title=split_col,
    )
    st.plotly_chart(fig, use_container_width=True, key=key)


def _overall_series(df_long, label_col="label", value_col="proportion", question=None):
    if df_long is None or df_long.empty:
        return pd.Series(dtype=float)
    mask = (df_long["split"] == "none") & (df_long["group"] == "all")
    if question and "question" in df_long.columns:
        mask &= df_long["question"] == question
    return df_long[mask].set_index(label_col)[value_col].sort_values(ascending=False)


def _likert_stacked(df_long, question, title, split_col=None, key=None):
    """Stacked horizontal bar for Likert responses."""
    if df_long is None or df_long.empty:
        return

    sub = df_long[df_long["question"] == question]
    if sub.empty:
        return

    if split_col and split_col != "none":
        sub = sub[sub["split"] == split_col]
        y_labels = sorted(sub["group"].dropna().unique().tolist())
    else:
        sub = sub[(sub["split"] == "none") & (sub["group"] == "all")]
        y_labels = ["All respondents"]

    traces = []
    for lvl, color in zip(LIKERT_ORDER, LIKERT_COLORS):
        x_vals = []
        for grp in y_labels:
            row = sub[sub["group"] == grp] if split_col else sub
            row = row[row["label"] == lvl]
            x_vals.append(row["proportion"].iloc[0] * 100 if not row.empty else 0)
        traces.append(go.Bar(
            name=lvl,
            y=y_labels,
            x=x_vals,
            orientation="h",
            marker_color=color,
            text=[f"{v:.0f}%" if v >= 5 else "" for v in x_vals],
            textposition="inside",
        ))

    fig = go.Figure(traces)
    fig.update_layout(
        title=title,
        barmode="stack",
        xaxis=dict(range=[0, 100], ticksuffix="%", showgrid=False),
        yaxis=dict(showgrid=False),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=40, b=160, l=10, r=10),
        height=max(280, len(y_labels) * 52 + 220),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.55,
            xanchor="left",
            x=0,
            font=dict(size=11),
        ),
    )
    st.plotly_chart(fig, use_container_width=True, key=key)


# ── Section renderers ─────────────────────────────────────────────────────────

def render_life_goals(df_goals, df_achievable, split_col):
    st.subheader("Life goals")
    st.caption("Top 3 things respondents would most like to change in their lives.")

    if df_goals is None:
        st.warning(_MISSING)
        return

    col1, col2 = st.columns([3, 2])
    with col1:
        sub = df_goals[df_goals.get("question", pd.Series("top3", index=df_goals.index)) == "top3"] \
              if "question" in df_goals.columns else df_goals
        _hbar(_overall_series(sub), "Top life goals (% mentioning)", top_n=12,
              key="pg_goals")
    with col2:
        if "question" in df_goals.columns:
            _hbar(_overall_series(df_goals, question="main"),
                  "Single most important goal", top_n=8, key="pg_goals_main")

    with st.expander("Goals split by demographic"):
        tab1, tab2 = st.tabs(["Top 3 goals", "Most important goal"])
        with tab1:
            sub3 = df_goals[df_goals["question"] == "top3"] \
                   if "question" in df_goals.columns else df_goals
            _grouped_bar(sub3, split_col, "label", "proportion", "",
                         top_n=8, key=f"pgs_{split_col}")
        with tab2:
            if "question" in df_goals.columns:
                subm = df_goals[df_goals["question"] == "main"]
                _grouped_bar(subm, split_col, "label", "proportion", "",
                             top_n=8, key=f"pgm_{split_col}")

    if df_achievable is not None:
        st.markdown("**Can goals be achieved through family planning?**")
        _hbar(_overall_series(df_achievable), "", top_n=4, key="pg_achievable")


def _groups(df_long, split):
    if df_long is None or "split" not in df_long.columns:
        return []
    return sorted(df_long.loc[df_long["split"] == split, "group"].dropna().unique())


def _gender_label(g):
    """'Femme  Nyɔnuwo' / 'Mace / Femme' -> 'Women'; raw value otherwise."""
    low = str(g).lower()
    if "femme" in low:
        return "Women"
    if "homme" in low:
        return "Men"
    return str(g)


SMALL_GROUP_N = 30


def _split_group(gender, age):
    """(split, group) for the gender/age filters. Both set uses the
    gender x age split ("gender_age") from etl_personality."""
    if gender == "All" and age == "All":
        return "none", "all"
    if age == "All":
        return "gender", gender
    if gender == "All":
        return "age_group", age
    return "gender_age", f"{gender} | {age}"


def _group_n(df_long, split, group):
    """Respondents in the group (the % denominator), or None for older files without `n`."""
    if df_long is None or "n" not in df_long.columns:
        return None
    n = df_long.loc[(df_long["split"] == split) & (df_long["group"] == group), "n"].dropna()
    return int(n.iloc[0]) if len(n) else None


def _with_n(label, n):
    return label if n is None else f"{label} (n={n:,})"


def _filtered_series(df_long, gender, age):
    """Overall series, or one subgroup when the gender/age filters are set."""
    split, group = _split_group(gender, age)
    if split == "none":
        return _overall_series(df_long)
    sub = df_long[(df_long["split"] == split) & (df_long["group"] == group)]
    return sub.set_index("label")["proportion"].sort_values(ascending=False)


def render_role_models(df_models, df_traits, split_col):
    st.subheader("Role models")
    st.caption("Who do respondents look up to?")

    f1, f2 = st.columns(2)
    with f1:
        gender = st.selectbox(
            "Gender", ["All"] + _groups(df_models, "gender"),
            format_func=lambda g: g if g == "All"
            else _with_n(_gender_label(g), _group_n(df_models, "gender", g)),
            key="rm_gender")
    with f2:
        age = st.selectbox(
            "Age group", ["All"] + _groups(df_models, "age_group"),
            format_func=lambda a: a if a == "All"
            else _with_n(a, _group_n(df_models, "age_group", a)),
            key="rm_age")
    if (gender != "All" and age != "All" and df_models is not None
            and "gender_age" not in set(df_models["split"])):
        st.info("Gender + age data not generated yet. "
                "Run `python -m pipeline.run_pipeline --pages personality`.")
        return
    n = _group_n(df_models, *_split_group(gender, age))
    if n is not None:
        st.caption(f"Based on {n:,} respondents."
                   + (" Small group: read these percentages with care." if n < SMALL_GROUP_N else ""))

    col1, col2 = st.columns(2)
    with col1:
        if df_models is not None:
            _hbar(_filtered_series(df_models, gender, age), "Role models (% mentioning)",
                  top_n=12, key="pg_rm")
    with col2:
        if df_traits is not None:
            _hbar(_filtered_series(df_traits, gender, age), "Why do they look up to them?",
                  top_n=12, key="pg_traits")

    if df_models is not None:
        with st.expander("Role models split by demographic"):
            _grouped_bar(df_models, split_col, "label", "proportion", "",
                         top_n=8, key=f"pgrs_{split_col}")


def render_health_beliefs(df_beliefs, df_confident, split_col):
    st.subheader("Health belief formation")
    st.caption("How do respondents form beliefs about health topics?")

    if df_beliefs is not None:
        _hbar(_overall_series(df_beliefs),
              "How beliefs are formed (% mentioning)", key="pg_beliefs")
        with st.expander("Split by demographic"):
            _grouped_bar(df_beliefs, split_col, "label", "proportion", "",
                         top_n=8, key=f"pgbs_{split_col}")

    st.markdown("**Most trusted person for difficult health decisions**")
    if df_confident is not None:
        col1, col2 = st.columns(2)
        with col1:
            sub_single = df_confident[df_confident["question"] == "single"] \
                         if "question" in df_confident.columns else df_confident
            _hbar(_overall_series(sub_single), "Single most trusted person",
                  top_n=10, key="pg_trust1")
        with col2:
            if "question" in df_confident.columns:
                sub3 = df_confident[df_confident["question"] == "top3"]
                _hbar(_overall_series(sub3), "Top 3 trusted people",
                      top_n=10, key="pg_trust3")


def render_wellbeing(df_wellbeing, split_col):
    st.subheader("Wellbeing")
    st.caption("Self-reported happiness and life satisfaction.")

    if df_wellbeing is None:
        st.warning(_MISSING)
        return

    # Stack vertically so the horizontal legend has full width and doesn't overlap bars
    _likert_stacked(df_wellbeing, "happiness",
                    "How often do you feel joy in daily life?",
                    split_col=split_col, key="pg_happy")
    _likert_stacked(df_wellbeing, "satisfaction",
                    "How often do you feel satisfied with life overall?",
                    split_col=split_col, key="pg_satisfy")


# ── Main render ───────────────────────────────────────────────────────────────

def render():
    st.title("Personality & Influencers")

    df_goals      = load_personality_life_goals()
    df_achievable = load_personality_goals_achievable()
    df_models     = load_personality_role_models()
    df_traits     = load_personality_likeable_traits()
    df_beliefs    = load_personality_forming_beliefs()
    df_confident  = load_personality_decision_confident()
    df_wellbeing  = load_personality_wellbeing()

    split_by  = st.radio("Split all charts by", list(SPLIT_MAP.keys()), horizontal=True)
    split_col = SPLIT_MAP[split_by]

    st.divider()
    render_life_goals(df_goals, df_achievable, split_col)
    st.divider()
    render_role_models(df_models, df_traits, split_col)
    st.divider()
    render_health_beliefs(df_beliefs, df_confident, split_col)
    st.divider()
    render_wellbeing(df_wellbeing, split_col)
