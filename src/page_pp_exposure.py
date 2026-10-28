"""Phone Pulse — Campaign Exposure: Treatment vs Comparison."""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from src.data_loader import (
    load_pp_exposure_profile, load_pp_exposure_fp_use,
    load_pp_exposure_attitudes, load_pp_exposure_partner_norms, _load_pp, EXPOSURE_BY_ROUND_ID,
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


ROUND_LABELS = {"round1": "Round 1 (~3 mo)", "round2_early": "Round 2 early group (Haddin Kay, ~5 mo)",
                "round2": "Round 2 (~6 mo)"}
INDICATOR_QUESTIONS = (
    "**How each indicator is calculated** (Phone Pulse questions; share of everyone in the group — "
    "anyone not asked, or answering don't know / refused, counts as no):\n"
    "- **Heard FP programmes/ads** — `uptake_fp`: *\"In the last month, do you remember hearing "
    "any radio programs or ads on the topics of maternal and child health, household fertility, "
    "and spacing of births?\"* = Yes. Only asked of radio listeners (`radio_any` = Yes).\n"
    "- **Knows the spacing message** — `knowledge_waiting`: *\"How long do doctors recommend "
    "waiting after giving birth before trying to conceive again?\"* = \"At least two years\" "
    "(the campaign's message).\n"
    "- **Campaign recall** — both of the above.\n"
    "- **Heard of a method** — `fpbeh_awarefp`: *\"I want you to think about methods you have heard "
    "of for delaying or avoiding pregnancies...\"*, each method read out. **At least one modern "
    "method** uses the baseline's modern list (Standard Days and LAM counted).\n\n"
    "**Groups**: Treatment = lives within a FEM partner station's coverage area and listened to "
    "that station in the past month (`radio_partner_N_listen`); Comparison = everyone else. "
    "**Weighted** = attrition weights (baseline weight ÷ chance of being reached in that round); "
    "**unweighted** = the same respondents counted once. Only respondents linked to the baseline "
    "are included. 95% CIs and two-sided p-values: cluster bootstrap over baseline settlements "
    "(1,000 replicates; same draws for every group and round)."
)


def _fmt_pct(v, lo, hi):
    return "—" if pd.isna(v) else f"{v:.1f}% ({lo:.1f}–{hi:.1f})"


def _fmt_pp(v, lo, hi):
    return "—" if pd.isna(v) else f"{v:+.1f} pp ({lo:+.1f} to {hi:+.1f})"


def _fmt_p(p):
    return "—" if pd.isna(p) else ("< 0.002" if p <= 0.002 else f"{p:.3f}")


def _html_table(head: list[str], body_rows: list[str]) -> str:
    th = "".join(f"<th style='text-align:{'left' if i == 0 else 'right'};padding:4px 8px'>{h}</th>"
                 for i, h in enumerate(head))
    return (f"<table style='width:100%;border-collapse:collapse'><thead><tr>{th}</tr></thead>"
            f"<tbody>{''.join(body_rows)}</tbody></table>")


def _row(label: str, hover: str, cells: list[str], bold: bool = False) -> str:
    style = "padding:4px 8px;border-top:1px solid rgba(128,128,128,0.25);" + ("font-weight:600;" if bold else "")
    tds = "".join(f"<td style='{style}text-align:right'>{c}</td>" for c in cells)
    return (f"<tr><td style='{style}text-align:left'><span title='{hover}' "
            f"style='border-bottom:1px dotted;cursor:help'>{label}</span></td>{tds}</tr>")


def _exposure_table(sub: pd.DataFrame) -> str:
    """Treatment vs Comparison, one row per indicator; hover the indicator for each group's N."""
    head = ["Indicator", "Treatment (partner station listener)<br>% (95% CI)",
            "Comparison (everyone else)<br>% (95% CI)", "Full sample<br>% (95% CI)",
            "Difference<br>Treatment − Comparison (95% CI)", "p-value"]
    rows = []
    for section in sub["section"].drop_duplicates():
        rows.append(f"<tr><td colspan='6' style='padding:10px 8px 2px;font-weight:600'>{section}</td></tr>")
        for ind in sub.loc[sub["section"] == section, "indicator"].drop_duplicates():
            g = sub[sub["indicator"] == ind].set_index("group")
            t, c, a = g.loc["Treatment"], g.loc["Comparison"], g.loc["All"]
            hover = (f"Treatment: {int(t['count'])} of N = {int(t['n'])}&#10;"
                     f"Comparison: {int(c['count'])} of N = {int(c['n'])}&#10;"
                     f"Full sample: {int(a['count'])} of N = {int(a['n'])}")
            rows.append(_row(t["label"], hover, [
                _fmt_pct(t["pct"], t["ci_low"], t["ci_high"]), _fmt_pct(c["pct"], c["ci_low"], c["ci_high"]),
                _fmt_pct(a["pct"], a["ci_low"], a["ci_high"]),
                _fmt_pp(t["diff_vs_comparison_pp"], t["diff_ci_low_pp"], t["diff_ci_high_pp"]),
                _fmt_p(t["diff_p_value"])], bold=ind in ("campaign_recall", "aware_modern")))
    return _html_table(head, rows)


def _round_change_table(sub: pd.DataFrame, round_label: str) -> str:
    """This round vs round 1, per group; hover the indicator for N in each group."""
    head = ["Indicator"] + [f"{g}<br>change (95% CI), p" for g in ("Treatment", "Comparison", "All")]
    rows = []
    for ind in sub["indicator"].drop_duplicates():
        g = sub[sub["indicator"] == ind].set_index("group")
        hover = "&#10;".join(f"{k}: N = {int(g.loc[k, 'n'])}" for k in ("Treatment", "Comparison", "All"))
        rows.append(_row(g.iloc[0]["label"], hover, [
            f"{_fmt_pp(g.loc[k, 'change_pp'], g.loc[k, 'change_ci_low_pp'], g.loc[k, 'change_ci_high_pp'])}"
            f"<br>p = {_fmt_p(g.loc[k, 'change_p_value'])}" for k in ("Treatment", "Comparison", "All")],
            bold=ind in ("campaign_recall", "aware_modern")))
    return _html_table(head, rows)


def _baseline_change_table(sub: pd.DataFrame, round_label: str) -> str:
    """Baseline -> this round for the same people, per group, plus Treatment change minus
    Comparison change. Recall rows: not asked at baseline. Shown on Change Over Time >
    Key Indicators (page_pp_change_over_time.py)."""
    groups = ("Treatment", "Comparison", "All")
    head = (["Indicator"] + [f"{g}<br>baseline → {round_label}<br>change (95% CI), p" for g in groups]
            + ["Treatment change − Comparison change<br>(95% CI), p"])
    rows = []
    for section in sub["section"].drop_duplicates():
        rows.append(f"<tr><td colspan='5' style='padding:10px 8px 2px;font-weight:600'>{section}</td></tr>")
        for ind in sub.loc[sub["section"] == section, "indicator"].drop_duplicates():
            g = sub[sub["indicator"] == ind].set_index("group")
            label = g.iloc[0]["label"]
            if pd.isna(g.loc["All"].get("baseline_pct")):
                why = ("Not asked at baseline" if section == "Recall"
                       else "Baseline combines male and female" if ind in ("aware_1", "aware_2", "aware_8", "aware_9")
                       else "No baseline option")
                rows.append(_row(label, why, [why, "", "", ""]))
                continue
            hover = "&#10;".join(f"{k}: baseline {int(g.loc[k, 'baseline_count'])}, now {int(g.loc[k, 'count'])} "
                                 f"of N = {int(g.loc[k, 'n'])}" for k in groups)
            cells = [f"{g.loc[k, 'baseline_pct']:.1f}% → {g.loc[k, 'pct']:.1f}%<br>"
                     f"{_fmt_pp(g.loc[k, 'change_vs_baseline_pp'], g.loc[k, 'change_vs_baseline_ci_low_pp'], g.loc[k, 'change_vs_baseline_ci_high_pp'])}"
                     f", p = {_fmt_p(g.loc[k, 'change_vs_baseline_p_value'])}" for k in groups]
            t = g.loc["Treatment"]
            cells.append(f"{_fmt_pp(t['did_pp'], t['did_ci_low_pp'], t['did_ci_high_pp'])}, p = {_fmt_p(t['did_p_value'])}")
            rows.append(_row(label, hover, cells, bold=ind == "aware_modern"))
    return _html_table(head, rows)


def _render_recall_awareness() -> None:
    try:   # load directly (not load_exposure_by_round) so a failed download says why
        df = _load_pp(EXPOSURE_BY_ROUND_ID)
    except Exception as e:
        st.info("Data pending: run `3_linkage/compare_exposure_rounds.py`, upload "
                "`3_linkage/outputs/exposure_by_round.csv` to Drive and paste its ID into "
                "`data_loader.py` (EXPOSURE_BY_ROUND_ID).")
        st.caption(f"Could not read the file from Drive ({type(e).__name__}: {str(e)[:200]}). "
                   "Check it is shared as 'Anyone with the link'.")
        return
    if "round" not in df.columns:
        st.error("exposure_by_round.csv didn't load as the expected CSV (no `round` column). Columns "
                 f"read: {', '.join(map(str, df.columns[:8]))}. Usually the Drive file isn't shared as "
                 "'Anyone with the link', so Drive returned a sign-in page instead of the file.")
        return
    rounds = [r for r in ROUND_LABELS if r in set(df["round"])]
    c1, c2 = st.columns(2)
    rnd = c1.selectbox("Survey round", rounds, format_func=ROUND_LABELS.get, key="exp_round")
    weighting = c2.radio("Estimates", ["weighted", "unweighted"], horizontal=True,
                         format_func=str.capitalize, key="exp_weighting")
    sub = df[(df["round"] == rnd) & (df["weighting"] == weighting)]
    st.markdown(_exposure_table(sub), unsafe_allow_html=True)
    st.caption("Hover over an indicator for the number of respondents in each group. Difference = "
               "Treatment minus Comparison, in percentage points.")

    if rnd != "round1" and "change_pp" in sub.columns:
        st.markdown(f"**Change since Round 1** ({ROUND_LABELS[rnd]} minus Round 1, same group)")
        st.markdown(_round_change_table(sub, ROUND_LABELS[rnd]), unsafe_allow_html=True)
    elif len(rounds) > 1:
        st.caption("Pick a later round to see its change since Round 1.")

    with st.expander("How these indicators are calculated"):
        st.markdown(INDICATOR_QUESTIONS)
    st.caption("Comparison includes people who don't listen to the radio, who were not asked about "
               "radio programmes, so part of the recall gap reflects radio listening itself rather "
               "than the campaign. Awareness: methods were read out, so this is prompted awareness.")


def render() -> None:
    st.markdown("### Phone Pulse — Campaign Exposure: Treatment vs Comparison")
    st.caption(
        "**Treatment** = respondents who live within a FEM partner station's coverage area and "
        "said they listened to that station in the past month — whether or not they recall "
        "hearing FP content (that is measured separately, as campaign recall). "
        "**Comparison** = everyone else who passed QA, whether or not they listen to radio at all."
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
    c1.metric("Treatment (partner station listener)", n_treatment)
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
        ["Recall & awareness", "Current FP use", "Attitudes", "Social norms"]
    )

    with tab1:
        _render_recall_awareness()

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
