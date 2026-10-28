"""
page_family_planning.py  —  improved version
Changes vs original:
  • Funnel group dropdown: deduplicated; "all" / "All" unified → single "All"
    entry; groups sorted alphabetically after "All".
  • Non-use reasons table: index column hidden; Hausa/French labels translated
    to English via a best-effort mapping (falls back gracefully if label not
    recognised).
  • Minor UX: split radio uses consistent labels.
"""

import textwrap

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from src.fem_colours import FEM_ORANGE, FEM_BROWN, FEM_TAUPE, FEM_STEEL, FEM_NAVY
from src import key_indicators as ki
from src.data_loader import (
    load_fp_funnel,
    load_fp_timing,
    load_fp_methods,
    load_fp_reason_use,
    load_fp_intent,
    load_fp_nonuse_reasons,
    load_fp_unmet,
    load_fp_headline,
)

FEM_PALETTE = [FEM_ORANGE, FEM_BROWN, FEM_TAUPE, FEM_STEEL, FEM_NAVY]

SPLIT_MAP = {
    "User group": "use",
    "Gender":     "gender",
    "Age group":  "age_group",
}

_MISSING = (
    "Pre-aggregated data not found. "
    "Run `python pipeline/run_pipeline.py --pages family_planning` to generate it."
)

# ── Translation map for non-use reason labels ─────────────────────────────────
# Add/extend as more Hausa or French labels become known.
_NONUSE_TRANSLATIONS = {
    # Hausa
    "ban son": "I don't want to",
    "ban sani ba": "I don't know",
    "mijina baya son": "My husband doesn't want to",
    "bana bukatar hana ciki": "I don't need contraception",
    "tsoron illa": "Fear of side effects",
    "addini": "Religious reasons",
    "tsada": "Too expensive",
    "nisa da asibiti": "Clinic too far away",
    "ba ya cikin asibiti": "Not available at clinic",
    "ina son yara": "I want (more) children",
    # French
    "mon mari ne veut pas": "My husband doesn't want to",
    "effets secondaires": "Fear of side effects",
    "religion": "Religious reasons",
    "trop cher": "Too expensive",
    "loin de la clinique": "Clinic too far away",
    "indisponible": "Not available",
    "je veux des enfants": "I want (more) children",
    "je ne sais pas": "I don't know",
}


def _translate_label(label):
    """Return English translation if label is in map; else return original."""
    if pd.isna(label):
        return label
    lower = str(label).lower().strip()
    return _NONUSE_TRANSLATIONS.get(lower, label)


# ── Chart helpers ─────────────────────────────────────────────────────────────

def _wrap_labels(series, wrap_at=35):
    """Wrap long index labels with <br> so Plotly can display them fully."""
    wrapped = [
        "<br>".join(textwrap.wrap(str(label), wrap_at)) if len(str(label)) > wrap_at else str(label)
        for label in series.index
    ]
    return series.set_axis(wrapped)

def _hbar(series, title, top_n=12, key=None):
    series = series.head(top_n)
    if series is None or series.empty:
        return
    series = _wrap_labels(series, wrap_at=35)
    colors = (FEM_PALETTE * (len(series) // len(FEM_PALETTE) + 1))[:len(series)]
    # Left margin: ~7px per character of the widest single wrapped line
    max_line_chars = max(
        (len(line) for label in series.index for line in str(label).split("<br>")),
        default=10,
    )
    left_margin = min(max(max_line_chars * 7, 80), 300)
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
        xaxis=dict(
            showgrid=False, showticklabels=False,
            range=[0, series.max() * 1.35] if len(series) else [0, 1],
        ),
        yaxis=dict(showgrid=False, autorange="reversed"),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=left_margin, r=80, t=36, b=10),
        height=max(180, len(series) * 44 + 60),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True, key=key)


def _grouped_bar(df_long, split_col, label_col, value_col, title,
                 top_n=8, key=None):
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
        height=360,
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


def _mcpr_value(df_funnel, split_col="use", group_val="all"):
    """Baseline modern CPR for one subgroup: % currently using a method
    (Q: are you doing anything to avoid pregnancy right now?) whose method
    (Q: which one?) is a modern/effective one -- see effective_use /
    MODERN_METHOD_KEYS in etl_family_planning.py. Every split's "all" group
    covers the full sample, so the default args give the page-wide figure.
    """
    if df_funnel is None or df_funnel.empty:
        return None
    row = df_funnel[(df_funnel["split"] == split_col) & (df_funnel["group"] == group_val)]
    if row.empty:
        return None
    val = row.iloc[0].get("effective_use")
    return val if pd.notna(val) else None


def _total_cpr_value(df_funnel, split_col="use", group_val="all"):
    """Total contraceptive prevalence rate (any method, modern + traditional)
    -- the funnel's current_use stage. Needed for the official DHS Demand
    Satisfied formula: mCPR / (total CPR + unmet need) -- NOT
    mCPR / (mCPR + unmet need), which silently drops traditional-method
    users from the denominator even though they're correctly excluded from
    the unmet-need numerator (their need counts as "met")."""
    if df_funnel is None or df_funnel.empty:
        return None
    row = df_funnel[(df_funnel["split"] == split_col) & (df_funnel["group"] == group_val)]
    if row.empty:
        return None
    val = row.iloc[0].get("current_use")
    return val if pd.notna(val) else None


def _unmet_bar_by_group(df_unmet, split_col, key):
    sub = df_unmet[(df_unmet["split"] == split_col) & (df_unmet["group"] != "all")]
    if sub.empty:
        return
    sub = sub.sort_values("unmet_need", ascending=False)
    fig = go.Figure()
    fig.add_bar(
        name="Unmet need", x=sub["group"].astype(str), y=sub["unmet_need"],
        marker_color=FEM_BROWN,
        text=[f"{v*100:.0f}%" for v in sub["unmet_need"]], textposition="outside",
    )
    if sub["unmet_demand"].notna().any():
        fig.add_bar(
            name="Unmet demand", x=sub["group"].astype(str), y=sub["unmet_demand"],
            marker_color=FEM_ORANGE,
            text=[f"{v*100:.0f}%" for v in sub["unmet_demand"]], textposition="outside",
        )
    fig.update_layout(
        barmode="group",
        yaxis=dict(tickformat=".0%", showgrid=False, title="% of respondents"),
        xaxis=dict(showgrid=False),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=20, b=40, l=10, r=10),
        height=340,
        legend_title=split_col,
    )
    st.plotly_chart(fig, use_container_width=True, key=key)


# ── Funnel ────────────────────────────────────────────────────────────────────

def render_funnel(df_funnel, split_col):
    st.markdown("**Contraceptive use funnel**")
    if df_funnel is None or df_funnel.empty:
        st.warning(_MISSING)
        return

    # Build clean, deduplicated group list
    raw_groups = (
        df_funnel[df_funnel["split"] == split_col]["group"]
        .dropna()
        .unique()
        .tolist()
    )
    # Normalise: treat "all", "All", "ALL" as the same
    normalised = {}
    for g in raw_groups:
        key = g.strip().lower()
        if key == "all":
            normalised["All"] = "all"   # display → actual value
        else:
            normalised[g.strip()] = g.strip()

    grp_options = ["All"] + sorted(k for k in normalised if k != "All")
    selected = st.selectbox("Filter group", grp_options, key="fp_funnel_grp")
    grp_val = normalised.get(selected, selected.lower())

    sub = df_funnel[
        (df_funnel["split"] == split_col) &
        (df_funnel["group"].str.strip().str.lower() == grp_val.lower())
    ]
    if sub.empty:
        st.info("No funnel data for this selection.")
        return

    row = sub.iloc[0]
    stages = ["Aware of methods"]
    values = [(row.get("aware", 0) or 0) * 100]

    # 2026-09-04 (ported from benin_app): stricter awareness check --
    # "Aware of methods" is a plain self-reported yes/no; this confirms the
    # "yes" by checking whether the respondent actually named a real modern
    # method in the XLSForm's own conditional follow-up question, rather
    # than just trusting the yes/no.
    aware_modern_val = row.get("aware_modern_method")
    if pd.notna(aware_modern_val):
        stages.append("...and named a modern method")
        values.append(aware_modern_val * 100)

    stages += ["Ever used", "Currently using"]
    values += [
        (row.get("ever_used",   0) or 0) * 100,
        (row.get("current_use", 0) or 0) * 100,
    ]
    # "Currently using" counts anyone doing *anything* to avoid pregnancy,
    # including less-effective traditional methods (withdrawal, calendar
    # method, etc.) -- add a narrower stage for modern/effective methods
    # specifically, so that gap is visible rather than implied.
    # (2026-09-04, ported from benin_app)
    effective_val = row.get("effective_use")
    if pd.notna(effective_val):
        stages.append("Using an effective method")
        values.append(effective_val * 100)

    if all(v == 0 for v in values):
        st.info("Funnel data is all zeros for this selection — check pipeline output.")
        return

    fig = go.Figure(go.Funnel(
        y=stages,
        x=values,
        textinfo="value+percent initial",
        texttemplate="%{value:.1f}%",
        marker_color=[FEM_ORANGE, FEM_TAUPE, FEM_BROWN, FEM_NAVY, FEM_STEEL][:len(stages)],
        connector=dict(line=dict(color=FEM_TAUPE, width=2)),
    ))
    fig.update_layout(
        height=280,
        margin=dict(l=20, r=20, t=10, b=10),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True, key="fp_funnel")

    with st.expander("How each stage is calculated"):
        st.markdown(
            "All stages are weighted (`combined_weight_adjusted`) shares of **every** "
            "respondent in the selected group — not just those who answered a given "
            "question — so a respondent skipped past a question by the survey's own "
            "skip logic still counts in the denominator, just not in that stage's "
            "numerator.\n\n"
            "- **Aware of methods** — `birth_spacing`: self-reported Yes/No on "
            "whether the respondent knows of effective methods to space births.\n"
            "- **...and named a modern method** — `known_contraceptive_options`: the "
            "survey's own conditional follow-up, only asked of respondents who said "
            "Yes above. This stage is the share who named **at least one modern/"
            "effective method** there — i.e. confirms the self-reported \"yes\" "
            "against an actual named method, rather than trusting it at face value.\n"
            "- **Ever used** — `ever_use`: whether the respondent has ever used a "
            "method to space births — Yes/No.\n"
            "- **Currently using** — `current_use`: whether the respondent is "
            "currently doing anything to avoid pregnancy — Yes/No. Includes "
            "traditional/less-effective methods (withdrawal, calendar method, etc.).\n"
            "- **Using an effective method** — `current_use_methods`: the follow-up "
            "listing which specific method(s) — share who named at least one modern "
            "method there, same \"confirm the self-report\" logic as the awareness "
            "stage above.\n\n"
            "\"Modern/effective method\" = sterilisation, implants, pills, IUD, "
            "injectables, condoms, vaginal ring/patch, vaginal barrier methods, "
            "standard days method, LAM, or emergency contraception — excludes "
            "withdrawal, abstinence and the calendar method."
        )


# ── Headline indicators ───────────────────────────────────────────────────────

def render_headline(df_headline):
    st.subheader("Key indicators")
    if df_headline is None or df_headline.empty:
        st.warning(
            "Headline indicators not found. Run `python pipeline/run_pipeline.py "
            "--pages family_planning`, upload `fp_headline.csv` to Drive and paste "
            "its file ID into `data_loader.py`."
        )
        return

    ki.show(ki.headline_table(df_headline))

    n = df_headline.pivot(index="metric", columns="population", values="n_unweighted")
    n_note = " · ".join(
        f"{label}: N = {int(n.loc['mcpr', pop])} "
        f"({int(n.loc['aware_modern_nonusers', pop])} non-users)"
        for pop, label in ki.HEADLINE_POPULATIONS.items() if pop in n.columns
    )
    with st.expander("How each indicator is calculated"):
        st.markdown(
            "All figures are weighted (`combined_weight_adjusted`) shares of every "
            "respondent in the population, unless noted.\n\n"
            "- **mCPR** — currently using a modern/effective method "
            "(`current_use_methods`; same definition as the funnel's \"Using an "
            "effective method\" stage).\n"
            "- **Unmet need** — wants to wait more than 2 years before the next "
            "pregnancy, or wants no more children (`time_before_preferred_pregnancy`), "
            "but not currently using any method; traditional methods count as using. "
            "\"1–2 years\" is not counted: that answer straddles the 2-year line DHS "
            "uses, so including it would over-count.\n"
            "- **Unmet demand** — unmet need AND says they would be open to using "
            "contraception in future (`future_intent`).\n"
            "- **Demand satisfied** — mCPR ÷ (total CPR [any method] + unmet need), "
            "the official DHS formula.\n"
            "- **Awareness of methods (all)** — named at least one modern method "
            "(`known_contraceptive_options`).\n"
            "- **Awareness of methods (non-users)** — same, among respondents not "
            "currently using any method (`current_use` ≠ Yes).\n\n"
            "**95% confidence intervals** account for the clustered sample design: "
            "the surveyed settlements are resampled within each region 1,000 times "
            "(Rao–Wu bootstrap) and the interval is the middle 95% of the resulting "
            "estimates.\n\n"
            f"Unweighted N — {n_note}"
        )


# ── Section renderers ─────────────────────────────────────────────────────────

def render_unmet(df_unmet, df_funnel, split_col):
    """2026-09-04, ported from benin_app."""
    st.subheader("Unmet need & unmet demand")
    st.caption(
        "**Unmet need** — wants to delay her next pregnancy by more than 2 years, "
        "or wants no more children, but isn't currently using any method "
        "(traditional methods still count as \"using\" here, the same "
        "treatment as the \"Currently using\" funnel stage). **Unmet demand** "
        "is the narrower cut within that group: women who also say they're "
        "interested in or open to using contraception in future — grounding "
        "the estimate in stated preference rather than assumed need."
    )
    if df_unmet is None or df_unmet.empty:
        st.warning(_MISSING)
        return

    overall = df_unmet[(df_unmet["split"] == split_col) & (df_unmet["group"] == "all")]
    if not overall.empty:
        row = overall.iloc[0]
        mcpr = _mcpr_value(df_funnel, split_col, "all")
        total_cpr = _total_cpr_value(df_funnel, split_col, "all")
        cols = st.columns(3)
        cols[0].metric("Unmet need", f"{row['unmet_need']*100:.1f}%")
        if pd.notna(row.get("unmet_demand")):
            cols[1].metric("Unmet demand", f"{row['unmet_demand']*100:.1f}%")
        if mcpr is not None and total_cpr is not None and pd.notna(row.get("unmet_need")):
            # Official DHS formula: mCPR / (total CPR + unmet need), NOT
            # mCPR / (mCPR + unmet need) -- total CPR (current_use) includes
            # traditional-method users, who are correctly excluded from the
            # unmet-need numerator (their need counts as "met") but need to
            # stay in this denominator or they vanish from demand entirely.
            total_demand = total_cpr + row["unmet_need"]
            if total_demand:
                cols[2].metric(
                    "Demand satisfied (modern methods)",
                    f"{mcpr / total_demand * 100:.1f}%",
                    help=(
                        "mCPR ÷ (total CPR [any method] + unmet need) — official DHS "
                        "\"demand satisfied by modern methods\" formula. Total CPR "
                        f"here is {total_cpr*100:.1f}% (vs. {mcpr*100:.1f}% mCPR alone) "
                        "since traditional-method users count toward total demand "
                        "being met, even though their method isn't classified as "
                        "\"modern.\""
                    ),
                )

    st.markdown("**By split**")
    _unmet_bar_by_group(df_unmet, split_col, key=f"fp_unmet_{split_col}")


def render_awareness_use(df_funnel, df_timing, df_reason, split_col):
    st.subheader("Awareness & use")

    col1, col2 = st.columns(2)
    with col1:
        render_funnel(df_funnel, split_col)
    with col2:
        st.markdown("**Preferred timing of next pregnancy**")
        if df_timing is not None:
            _hbar(_overall_series(df_timing), "", key="fp_timing")

    st.markdown("**Reason for current/recent use**")
    if df_reason is not None:
        _grouped_bar(df_reason, split_col, "label", "proportion", "",
                     key=f"fp_reason_{split_col}")


def render_methods(df_methods, split_col):
    st.subheader("Methods known vs. ever used vs. currently using")
    if df_methods is None or df_methods.empty:
        st.warning(_MISSING)
        return

    col1, col2, col3 = st.columns(3)
    for col_obj, mtype, title, key in [
        (col1, "known",   "Methods known",  "fp_known"),
        (col2, "ever",    "Ever used",       "fp_ever"),
        (col3, "current", "Currently using", "fp_curr"),
    ]:
        with col_obj:
            sub = df_methods[
                (df_methods["method_type"] == mtype) &
                (df_methods["split"] == "none") &
                (df_methods["group"] == "all")
            ]
            if not sub.empty:
                _hbar(
                    sub.set_index("method")["proportion"].sort_values(ascending=False),
                    title, top_n=10, key=key,
                )

    st.markdown("**Methods by split**")
    tab1, tab2, tab3 = st.tabs(["Known", "Ever used", "Current"])
    for tab, mtype, kpfx in [
        (tab1, "known",   "fpsk"),
        (tab2, "ever",    "fpse"),
        (tab3, "current", "fpsc"),
    ]:
        with tab:
            sub = df_methods[df_methods["method_type"] == mtype]
            _grouped_bar(sub, split_col, "method", "proportion", "",
                         top_n=8, key=f"{kpfx}_{split_col}")


def render_intent(df_intent, df_nonuse):
    st.subheader("Future intent & non-use reasons")

    col1, col2 = st.columns(2)
    for col_obj, question, title, key in [
        (col1, "future_intent",  "Intends to use contraception in future", "fp_intent"),
        (col2, "considered_use", "Considered use (non-users)",             "fp_considered"),
    ]:
        with col_obj:
            st.markdown(f"**{title}**")
            if df_intent is not None:
                sub = df_intent[
                    (df_intent["question"] == question) &
                    (df_intent["split"] == "none") &
                    (df_intent["group"] == "all")
                ]
                if not sub.empty:
                    _hbar(sub.set_index("response")["proportion"], "", key=key)

    if df_nonuse is not None and not df_nonuse.empty:
        st.markdown("**Reasons for non-use**")

        # Translate any Hausa/French labels to English
        display = df_nonuse.copy()
        for col in display.columns:
            if display[col].dtype == object:
                display[col] = display[col].apply(_translate_label)

        # Drop unnamed index-like columns
        display = display.loc[
            :, ~display.columns.str.match(r"^Unnamed")
        ].reset_index(drop=True)

        st.dataframe(display, use_container_width=True, hide_index=True)


# ── Main render ───────────────────────────────────────────────────────────────

def render():
    st.title("Family Planning")

    df_funnel  = load_fp_funnel()
    df_timing  = load_fp_timing()
    df_methods = load_fp_methods()
    df_reason  = load_fp_reason_use()
    df_intent  = load_fp_intent()
    df_nonuse  = load_fp_nonuse_reasons()
    df_unmet   = load_fp_unmet()
    df_headline = load_fp_headline()

    render_headline(df_headline)
    st.divider()

    split_by  = st.radio("Split all charts by", list(SPLIT_MAP.keys()), horizontal=True)
    split_col = SPLIT_MAP[split_by]

    st.divider()
    render_unmet(df_unmet, df_funnel, split_col)
    st.divider()
    render_awareness_use(df_funnel, df_timing, df_reason, split_col)
    st.divider()
    render_methods(df_methods, split_col)
    st.divider()
    render_intent(df_intent, df_nonuse)
