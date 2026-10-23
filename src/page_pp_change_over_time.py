"""
Phone Pulse — Change Over Time (home page tying baseline + every follow-up
round together).

Two top-level comparison types, each with the same six metric sub-tabs
(Method Awareness, Current FP Use, Method Switching, Unmet Need, Attitudes,
Barriers), each rendered as a time series across survey rounds:

- **Cross-sectional**: full Formative Research baseline (968 respondents)
  vs. EACH round's full achieved Phone Pulse sample — independent samples,
  NOT the same people. Source: 3_linkage/cross_sectional/compare_*_unlinked.py.
- **Longitudinal**: the SAME respondents, paired across waves (471 linked
  out of 968 baseline / 509 pulse). Source: 3_linkage/compare_*.py.

Today only round 1 (~3 months post-campaign) has real data; round 2 (~6 mo)
and round 3 (~24 mo) are registered below as upcoming placeholders — they
render as a labeled gap in each time series, never a fabricated value. Add
a new round here (ROUNDS) once its data exists; it flows straight through
to every chart on this page with no other change needed here.
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from src.data_loader import (
    # Longitudinal (linked panel)
    load_knowledge_change, load_fp_use_change,
    load_method_switching, load_method_switching_crosstab,
    load_unmet_need_change, load_attitudes_change, load_barriers_change,
    # Cross-sectional (independent samples)
    load_knowledge_change_unlinked, load_fp_use_change_unlinked,
    load_method_switching_unlinked, load_method_switching_crosstab_unlinked,
    load_unmet_need_change_unlinked, load_attitudes_change_unlinked,
    load_barriers_change_unlinked,
)

FEM_ORANGE = "#C1693A"
FEM_NAVY   = "#2E3F52"
FEM_TAUPE  = "#7A7068"
FEM_BROWN  = "#8B5E45"
FEM_STEEL  = "#5A6E7F"
PALETTE = [FEM_NAVY, FEM_ORANGE, FEM_TAUPE, FEM_STEEL, FEM_BROWN,
           "#8fa998", "#c9a34e", "#6b4e71", "#4c7a8f", "#a35b5b"]

_CHART = dict(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
SIG_THRESHOLD = 0.05

# ── Round registry ──────────────────────────────────────────────────────────
# Mirrors 3_linkage/config.py's ROUNDS — kept in sync manually since this app
# deploys standalone (data/ is gitignored, no cross-repo import). Add a row
# here (+ a matching row in 3_linkage/config.py and, for cross-sectional,
# cross_sectional/config.py's ROUND_PULSE_DATA) once a new round's data
# exists; every chart on this page picks it up automatically.
ROUNDS = [
    {"round_id": "round1", "label": "Round 1 (~3 mo)",  "status": "live"},
    {"round_id": "round2", "label": "Round 2 (~6 mo)",  "status": "pending"},
    {"round_id": "round3", "label": "Round 3 (~24 mo)", "status": "pending"},
]


def _round_x_label(r: dict) -> str:
    return r["label"] if r["status"] == "live" else f"{r['label']} — pending"


# ── Compare-as mode (mirrors Benin's page_baseline_followup.py toggle) ───────
MODE_DESCRIPTIONS = {
    "Cross-sectional": (
        "Each wave's own respondents (the full formative baseline, then "
        "each Phone Pulse round's full achieved sample) compared as "
        "independent population-level snapshots — shows how the "
        "population overall is moving, not whether any individual changed."
    ),
    "Longitudinal": (
        "Only respondents present in every wave (the 471-person linked "
        "panel, out of 968 baseline / 509 Phone Pulse round 1 "
        "respondents), tracked across time — shows whether the SAME "
        "people's answers changed, not just the population mix."
    ),
}


def _ensure_round_column(df: pd.DataFrame) -> pd.DataFrame:
    """Defensive fallback: the Drive-hosted CSVs for the 4 metrics that
    existed before this page's rebuild may still be the pre-round-column
    snapshot until someone re-uploads the regenerated CSV (see
    data_loader.py comments) — treat those as round1 rather than erroring."""
    if df is None:
        return None
    df = df.copy()
    if "round" not in df.columns:
        df["round"] = "round1"
    return df


def _footnotes(items: list[str]) -> None:
    st.caption("Sources:  " + "&nbsp;&nbsp;·&nbsp;&nbsp; ".join(
        f"{i+1}. {text}" for i, text in enumerate(items)
    ))


def _render_questions_asked(baseline_q: str, followup_q: str, sources: list[str],
                             is_linked: bool) -> None:
    pop_note = (
        "Same 471 people, paired across waves." if is_linked else
        "Two different groups of people: the full baseline sample vs. each "
        "round's full achieved Phone Pulse sample."
    )
    with st.expander("Survey questions asked"):
        st.markdown(f"**Formative Research (baseline, in-person interview):**¹\n\n> {baseline_q}")
        st.markdown(f"**Phone Pulse (follow-up, phone call):**²\n\n> {followup_q}")
        st.caption(f"{pop_note} The two surveys were run in different "
                   "languages/modes and don't use identical wording — see "
                   "the Limitations section below.")
        st.markdown("---")
        _footnotes(sources)


def _detail_table(table: pd.DataFrame) -> None:
    """Round-1 detail table with percentages to one decimal place."""
    st.dataframe(
        table, use_container_width=True, hide_index=True,
        column_config={
            **{c: st.column_config.NumberColumn(c, format="%.1f")
               for c in ("Baseline %", "Round 1 %") if c in table.columns},
            **({"p-value": st.column_config.NumberColumn("p-value", format="%.4f")}
               if "p-value" in table.columns else {}),
        },
    )


def _sig_note(p_value, direction: str, test_name: str) -> str:
    if pd.isna(p_value):
        return ""
    verdict = "Statistically significant" if p_value < SIG_THRESHOLD else "Not statistically significant"
    dirtxt = direction.capitalize() if direction and not direction.startswith(("wilcoxon", "mannwhitney")) else ""
    prefix = f"{dirtxt} — " if dirtxt else ""
    return f"{prefix}{verdict} ({test_name}, p = {p_value:.4f})"


# ── Generic time-series chart builders ──────────────────────────────────────

def _single_metric_timeseries(df: pd.DataFrame, baseline_col: str, value_col: str,
                                title: str, y_title: str) -> go.Figure:
    """One line: Baseline -> Round 1 -> Round 2 -> Round 3, single metric."""
    df = _ensure_round_column(df)
    x_labels = ["Baseline"] + [_round_x_label(r) for r in ROUNDS]

    baseline_val = None
    if df is not None and not df.empty and df[baseline_col].notna().any():
        baseline_val = df[baseline_col].dropna().iloc[0]

    y_vals, texts = [baseline_val], [f"{baseline_val:.1f}%" if baseline_val is not None else ""]
    for r in ROUNDS:
        row = df[df["round"] == r["round_id"]] if df is not None else pd.DataFrame()
        if r["status"] != "live" or row.empty or pd.isna(row.iloc[0].get(value_col)):
            y_vals.append(None)
            texts.append("")
        else:
            v = row.iloc[0][value_col]
            y_vals.append(v)
            texts.append(f"{v:.1f}%")

    fig = go.Figure(go.Scatter(
        x=x_labels, y=y_vals, mode="lines+markers+text",
        text=texts, textposition="top center",
        line=dict(color=FEM_NAVY, width=2), marker=dict(size=11, color=FEM_NAVY),
        connectgaps=False, hovertemplate="%{x}: %{y:.1f}%<extra></extra>",
    ))
    fig.update_layout(
        **_CHART, title=title, yaxis_title=y_title,
        yaxis_range=[0, max([v for v in y_vals if v is not None] + [10]) * 1.4],
        height=320, margin=dict(l=10, r=30, t=60, b=10),
    )
    return fig


def _multi_item_timeseries(df: pd.DataFrame, item_col: str, baseline_col: str,
                             value_col: str, title: str, y_title: str,
                             max_items: int = 10) -> go.Figure:
    """One line per item (method / attitude item / barrier category)."""
    df = _ensure_round_column(df)
    x_labels = ["Baseline"] + [_round_x_label(r) for r in ROUNDS]
    fig = go.Figure()
    if df is None or df.empty:
        fig.update_layout(**_CHART, title=title, height=200)
        return fig

    items = [i for i in df[item_col].dropna().unique().tolist() if i != "__OVERALL__"][:max_items]
    for i, item in enumerate(items):
        sub = df[df[item_col] == item]
        baseline_val = sub[baseline_col].dropna().iloc[0] if sub[baseline_col].notna().any() else None
        y_vals = [baseline_val]
        for r in ROUNDS:
            row = sub[sub["round"] == r["round_id"]]
            if r["status"] != "live" or row.empty or pd.isna(row.iloc[0].get(value_col)):
                y_vals.append(None)
            else:
                y_vals.append(row.iloc[0][value_col])
        fig.add_trace(go.Scatter(
            x=x_labels, y=y_vals, mode="lines+markers", name=str(item)[:40],
            line=dict(color=PALETTE[i % len(PALETTE)]), marker=dict(size=8),
            connectgaps=False, hovertemplate="%{x}: %{y:.1f}%",
        ))
    fig.update_layout(
        **_CHART, title=title, yaxis_title=y_title,
        height=max(360, 40 * len(items) + 160),
        margin=dict(l=10, r=10, t=60, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, font=dict(size=10)),
    )
    return fig


def _pending_note() -> None:
    st.caption(
        "Round 2 (~6 mo) and Round 3 (~24 mo) show as a gap in the line "
        "above — that data has not been collected yet. It is never shown "
        "as zero or omitted silently."
    )


def _population_caption(is_linked: bool, linked_text: str, cross_text: str) -> None:
    st.caption(linked_text if is_linked else cross_text)


# ── Method Awareness ─────────────────────────────────────────────────────────

def _render_knowledge(is_linked: bool) -> None:
    df = load_knowledge_change() if is_linked else load_knowledge_change_unlinked()
    df = _ensure_round_column(df)
    if df is None or df.empty:
        st.info("Data pending — see data_loader.py for the script to run and CSV to upload.")
        return

    _population_caption(
        is_linked,
        "Awareness of specific contraceptive methods, for the SAME 471 "
        "respondents linked across both waves.",
        "Awareness of specific contraceptive methods, for the FULL "
        "formative baseline (968) vs. each round's FULL achieved Phone "
        "Pulse sample (509 for round 1) — independent samples.",
    )
    _render_questions_asked(
        "\"Which contraceptive methods are you familiar with?\" — "
        "**enumerator instruction: do NOT read the method list out loud; "
        "only record methods the respondent volunteers unprompted "
        "(unaided recall).**",
        "\"I want you to think about methods you have heard of for "
        "delaying or avoiding pregnancies...\" — **enumerator instruction: "
        "read each method and ask if the respondent has heard of it "
        "(aided recall).**",
        sources=[
            "field `known_contraceptive_options` — `1_formative_research/"
            "table_analysis/data/1_raw/Ha-Fr_Collecte de Données sur le "
            "Terrain.xlsx`, sheet `survey`.",
            "field `fpbeh_awarefp` — `2_phone pulse/meta/"
            "Participants_Appels de Suivi.xlsx`, sheet `survey`.",
        ],
        is_linked=is_linked,
    )
    st.warning(
        "⚠️ **Not apples-to-apples**: baseline used unaided recall, "
        "follow-up used aided recall. Aided recall reliably produces "
        "higher \"known\" rates independent of any real change in "
        "awareness — some (possibly most) of the increase shown could be "
        "this measurement artifact rather than the campaign."
    )
    st.markdown("---")

    overall = df[df["method"] == "__OVERALL__"]
    if not overall.empty:
        row1 = overall[overall["round"] == "round1"]
        if not row1.empty:
            row = row1.iloc[0]
            col1, col2 = st.columns(2)
            col1.metric("Known at baseline", f"{row['known_baseline_pct']:.1f}%")
            col2.metric(
                "Known — Round 1", f"{row['known_pulse_pct']:.1f}%",
                delta=f"{row['known_pulse_pct'] - row['known_baseline_pct']:+.1f} pts",
            )

    methods = df[df["method"] != "__OVERALL__"]
    fig = _multi_item_timeseries(
        methods, "method", "known_baseline_pct", "known_pulse_pct",
        "Method awareness over time", "% aware of method",
    )
    st.plotly_chart(fig, use_container_width=True)
    _pending_note()

    p_col = "mcnemar_p_value" if is_linked else "ztest_p_value"
    r1 = methods[methods["round"] == "round1"]
    if p_col in r1.columns:
        sig = r1[r1[p_col] < SIG_THRESHOLD]
        if not sig.empty:
            test_name = "McNemar's exact test" if is_linked else "two-proportion z-test"
            st.caption(f"Statistically significant change at Round 1 ({test_name}, "
                       f"p < {SIG_THRESHOLD}): " + ", ".join(sig["method"].tolist()))

    st.markdown("#### Detail — Round 1")
    show_cols = ["method", "known_baseline_pct", "known_pulse_pct", p_col, "direction"]
    show_cols = [c for c in show_cols if c in r1.columns]
    if not r1.empty:
        _detail_table(
            r1[show_cols].rename(columns={
                "method": "Method", "known_baseline_pct": "Baseline %",
                "known_pulse_pct": "Round 1 %", p_col: "p-value", "direction": "Direction",
            }).sort_values("p-value").reset_index(drop=True),
        )


# ── Current FP Use ───────────────────────────────────────────────────────────

def _render_fp_use(is_linked: bool) -> None:
    df = load_fp_use_change() if is_linked else load_fp_use_change_unlinked()
    df = _ensure_round_column(df)
    if df is None or df.empty:
        st.info("Data pending — see data_loader.py for the script to run and CSV to upload.")
        return

    _population_caption(
        is_linked,
        "Current FP use, for the SAME 471 respondents linked across both waves.",
        "Current FP use, for the FULL formative baseline (968) vs. each "
        "round's FULL achieved Phone Pulse sample — independent samples.",
    )
    _render_questions_asked(
        "\"In the last six months, have you used any methods of childbirth "
        "spacing?\" Only asked of respondents who indicated they'd ever "
        "used FP — skipped (treated as \"not using\") otherwise.",
        "\"Are you currently doing something or using any method to delay "
        "or avoid (your wife) getting pregnant?\" Only asked of respondents "
        "not currently pregnant.",
        sources=[
            "field `current_use` — `1_formative_research/table_analysis/"
            "data/1_raw/Ha-Fr_Collecte de Données sur le Terrain.xlsx`, "
            "sheet `survey`; relevance condition on field `ever_use`.",
            "field `fpbeh_fpnow` — `2_phone pulse/meta/"
            "Participants_Appels de Suivi.xlsx`, sheet `survey`; relevance "
            "condition on field `current_pregnant`.",
        ],
        is_linked=is_linked,
    )
    st.caption(
        "Note the reference period differs: baseline asks about the last "
        "6 months, follow-up asks about right now."
    )
    st.markdown("---")

    fig = _single_metric_timeseries(
        df, "using_baseline_pct", "using_pulse_pct",
        "Current FP use over time", "% currently using FP",
    )
    st.plotly_chart(fig, use_container_width=True)
    _pending_note()

    r1 = df[df["round"] == "round1"]
    if not r1.empty:
        row = r1.iloc[0]
        p_col = "mcnemar_p_value" if is_linked else "ztest_p_value"
        test_name = "McNemar's exact test" if is_linked else "two-proportion z-test"
        st.caption(_sig_note(row.get(p_col), row.get("direction", ""), test_name))
        if is_linked:
            st.caption(f"Started using / Stopped: {int(row['started_using_n'])} / "
                       f"{int(row['stopped_using_n'])}")


# ── Method Switching ─────────────────────────────────────────────────────────

def _render_method_switching(is_linked: bool) -> None:
    df = load_method_switching() if is_linked else load_method_switching_unlinked()
    df = _ensure_round_column(df)
    if df is None or df.empty:
        st.info("Data pending — see data_loader.py for the script to run and CSV to upload.")
        return

    if is_linked:
        _population_caption(
            is_linked,
            "Whether respondents who used a traditional method at baseline "
            "had switched to a modern method by follow-up, for the SAME "
            "471 linked respondents.",
            "",
        )
    else:
        st.caption(
            "**Reinterpreted for independent samples**: two different "
            "groups of people can't show individual switching, only "
            "whether the overall modern / traditional / none-or-other mix "
            "shifted between the full baseline and each round's full "
            "achieved sample (chi-square test)."
        )
    st.markdown("---")

    if is_linked:
        r1_users = df[(df["round"] == "round1") & (df["metric"].str.startswith("% of baseline traditional"))]
        r1_women = df[(df["round"] == "round1") & (df["metric"].str.contains("all linked women"))]
        col1, col2 = st.columns(2)
        if not r1_users.empty:
            row = r1_users.iloc[0]
            col1.metric(
                "Of baseline traditional users, now on a modern method (R1)",
                f"{row['pct']:.1f}%" if pd.notna(row["pct"]) else "N/A",
                help=f"{int(row['numerator_n'])} of {int(row['denominator_n'])}",
            )
        if not r1_women.empty:
            row = r1_women.iloc[0]
            col2.metric(
                "Of all linked women, switched traditional → modern (R1)",
                f"{row['pct']:.1f}%" if pd.notna(row["pct"]) else "N/A",
                help=f"{int(row['numerator_n'])} of {int(row['denominator_n'])}",
            )
        if not r1_users.empty and r1_users.iloc[0]["denominator_n"] < 10:
            st.warning(
                f"⚠️ Only **{int(r1_users.iloc[0]['denominator_n'])}** linked "
                "respondent(s) reported using a traditional method at "
                "baseline — the \"% of baseline traditional users\" figure "
                "is not statistically meaningful at this sample size."
            )

        crosstab = load_method_switching_crosstab()
        crosstab = _ensure_round_column(crosstab)
        if crosstab is not None and not crosstab.empty:
            ct = crosstab[crosstab["round"] == "round1"].drop(columns=["round"])
            ct = ct.rename(columns={ct.columns[0]: "Baseline \\ Follow-up (R1)"})
            st.markdown("#### Baseline category → Round 1 category")
            st.dataframe(ct, use_container_width=True, hide_index=True)
    else:
        r1 = df[df["round"] == "round1"]
        if not r1.empty:
            fig = go.Figure()
            fig.add_trace(go.Bar(x=r1["baseline_pct"], y=r1["category"], orientation="h",
                                  name="Baseline", marker_color=FEM_TAUPE,
                                  text=r1["baseline_pct"].map(lambda v: f"{v:.1f}%"), textposition="outside"))
            fig.add_trace(go.Bar(x=r1["pulse_pct"], y=r1["category"], orientation="h",
                                  name="Round 1", marker_color=FEM_NAVY,
                                  text=r1["pulse_pct"].map(lambda v: f"{v:.1f}%"), textposition="outside"))
            fig.update_layout(**_CHART, title="Current-method mix: baseline vs. Round 1",
                               barmode="group", xaxis_title="% of full sample",
                               xaxis_range=[0, 115], height=320,
                               margin=dict(l=10, r=30, t=60, b=10),
                               legend=dict(orientation="h", yanchor="bottom", y=1.15))
            st.plotly_chart(fig, use_container_width=True)
            p = r1["chi_square_p_value"].iloc[0]
            if pd.notna(p):
                st.caption(f"Chi-square test of independence across the full mix: p = {p:.4f} "
                           f"({'significant' if p < SIG_THRESHOLD else 'not significant'}).")


# ── Unmet Need ────────────────────────────────────────────────────────────────

def _render_unmet_need(is_linked: bool) -> None:
    df = load_unmet_need_change() if is_linked else load_unmet_need_change_unlinked()
    df = _ensure_round_column(df)
    if df is None or df.empty:
        st.info("Data pending — see data_loader.py for the script to run and CSV to upload.")
        return

    _population_caption(
        is_linked,
        "Unmet need for contraception, for the SAME 471 respondents linked "
        "across both waves.",
        "Unmet need for contraception, for the FULL formative baseline "
        "(968) vs. each round's FULL achieved Phone Pulse sample — "
        "independent samples.",
    )
    st.warning(
        "⚠️ **Narrower than the Family Planning page's \"Unmet need\" "
        "figure**: uses the restricted \"wants no more children AND not "
        "currently using any method\" definition on BOTH waves, since "
        "Phone Pulse never asked the future-timing question the fuller "
        "baseline definition needs — see 3_linkage/compare_unmet_need.py."
    )
    st.markdown("---")

    fig = _single_metric_timeseries(
        df, "unmet_need_baseline_pct", "unmet_need_pulse_pct",
        "Unmet need over time", "% with unmet need",
    )
    st.plotly_chart(fig, use_container_width=True)
    _pending_note()

    r1 = df[df["round"] == "round1"]
    if not r1.empty:
        row = r1.iloc[0]
        p_col = "mcnemar_p_value" if is_linked else "ztest_p_value"
        test_name = "McNemar's exact test" if is_linked else "two-proportion z-test"
        st.caption(_sig_note(row.get(p_col), row.get("direction", ""), test_name))


# ── Attitudes ─────────────────────────────────────────────────────────────────

def _render_attitudes(is_linked: bool) -> None:
    df = load_attitudes_change() if is_linked else load_attitudes_change_unlinked()
    df = _ensure_round_column(df)
    if df is None or df.empty:
        st.info("Data pending — see data_loader.py for the script to run and CSV to upload.")
        return

    st.warning(
        "⚠️ **Best-effort thematic crosswalk, not a matched question**: "
        "Phone Pulse asks 8 fixed attitude statements; the formative "
        "baseline instead shows a 62-item randomized message-testing "
        "statement bank. Only 4 of the 8 Phone Pulse items had a "
        "plausible baseline equivalent at all — see "
        "3_linkage/config.py `ATTITUDE_CROSSWALK` for the exact wording "
        "matched and each pair's confidence."
    )
    _population_caption(
        is_linked,
        "% of the SAME 471 linked respondents holding each view.",
        "% of the FULL formative baseline vs. each round's FULL achieved "
        "Phone Pulse sample holding each view — independent samples.",
    )
    st.markdown("---")

    fig = _multi_item_timeseries(
        df, "item", "holds_view_baseline_pct", "holds_view_pulse_pct",
        "Attitude items over time", "% holding the view",
    )
    st.plotly_chart(fig, use_container_width=True)
    _pending_note()

    r1 = df[df["round"] == "round1"]
    p_col = "mcnemar_p_value" if is_linked else "ztest_p_value"
    show_cols = ["item", "holds_view_baseline_pct", "holds_view_pulse_pct", p_col, "direction"]
    show_cols = [c for c in show_cols if c in r1.columns]
    if not r1.empty:
        st.markdown("#### Detail — Round 1")
        _detail_table(
            r1[show_cols].rename(columns={
                "item": "Item", "holds_view_baseline_pct": "Baseline %",
                "holds_view_pulse_pct": "Round 1 %", p_col: "p-value", "direction": "Direction",
            }).reset_index(drop=True),
        )


# ── Barriers ──────────────────────────────────────────────────────────────────

def _render_barriers(is_linked: bool) -> None:
    df = load_barriers_change() if is_linked else load_barriers_change_unlinked()
    df = _ensure_round_column(df)
    if df is None or df.empty:
        st.info("Data pending — see data_loader.py for the script to run and CSV to upload.")
        return

    st.warning(
        "⚠️ **Keyword-based crosswalk, not a matched question**: the "
        "formative baseline records open-taxonomy reasons for non-use; "
        "Phone Pulse asks a fixed 12-category list. Each formative label "
        "is mapped to the closest fixed category by keyword match — "
        "approximate, not verified. See 3_linkage/config.py "
        "`BARRIER_KEYWORDS`."
    )
    if is_linked:
        st.caption(
            "Restricted to the ~68 linked respondents who reported NOT "
            "using FP on BOTH waves (the question wasn't asked of current "
            "users) — a small, non-random subset; treat as directional only."
        )
    else:
        st.caption(
            "Each survey's own respondents who reported not currently "
            "using FP — a different, larger set on each side than the "
            "linked comparison's ~68."
        )
    st.markdown("---")

    fig = _multi_item_timeseries(
        df, "category", "cited_baseline_pct", "cited_pulse_pct",
        "Reasons for non-use over time", "% citing this reason",
    )
    st.plotly_chart(fig, use_container_width=True)
    _pending_note()

    r1 = df[df["round"] == "round1"]
    p_col = "mcnemar_p_value" if is_linked else "ztest_p_value"
    show_cols = ["category", "cited_baseline_pct", "cited_pulse_pct", p_col, "direction"]
    show_cols = [c for c in show_cols if c in r1.columns]
    if not r1.empty:
        st.markdown("#### Detail — Round 1")
        _detail_table(
            r1[show_cols].rename(columns={
                "category": "Reason", "cited_baseline_pct": "Baseline %",
                "cited_pulse_pct": "Round 1 %", p_col: "p-value", "direction": "Direction",
            }).sort_values("Baseline %", ascending=False).reset_index(drop=True),
        )


# ── Limitations & shell ──────────────────────────────────────────────────────

def _render_limitations(is_linked: bool) -> None:
    with st.expander("Limitations & caveats"):
        common = (
            "- **Measurement effect**: the baseline was an in-person "
            "interview and the follow-up a phone call; the change in "
            "mode/privacy could shift reported answers on its own.\n"
            "- **Confounding variables**: seasonal patterns, "
            "supply/stockout changes, or other health programming active "
            "over the same period could also contribute to any change "
            "shown here.\n"
        )
        if is_linked:
            st.markdown(common + (
                "- **Linkage / attrition selection**: only 471 of 968 "
                "formative respondents (92.5% of the 509 reachable Phone "
                "Pulse respondents) were successfully linked. If "
                "reachable/re-interviewed respondents differ "
                "systematically from those lost to follow-up, this isn't "
                "necessarily representative of the full baseline sample."
            ))
        else:
            st.markdown(common + (
                "- **Sample composition**: the two samples are drawn "
                "differently (in-person household roster vs. phone "
                "recontact of a subset) and are not necessarily "
                "comparable on age/gender/urbanicity — a shift shown here "
                "could reflect who's in each sample rather than a real "
                "population change. Unlike the Longitudinal tab, this "
                "comparison CANNOT tell you whether any individual "
                "person's answer changed."
            ))


def _render_comparison_type(is_linked: bool) -> None:
    tabs = st.tabs([
        "Method Awareness", "Current FP Use", "Method Switching",
        "Unmet Need", "Attitudes", "Barriers",
    ])
    renderers = [
        _render_knowledge, _render_fp_use, _render_method_switching,
        _render_unmet_need, _render_attitudes, _render_barriers,
    ]
    for tab, renderer in zip(tabs, renderers):
        with tab:
            renderer(is_linked)
            _render_limitations(is_linked)


def render() -> None:
    st.header("Baseline vs. Follow-up")
    st.caption(
        "Time series across the full survey program — baseline plus Phone "
        "Pulse follow-ups at 3, 6, and 24 months — for awareness of "
        "methods, attitudes, and family planning barriers."
    )

    mode = st.radio(
        "Compare as:",
        list(MODE_DESCRIPTIONS.keys()),
        horizontal=True,
        help="Cross-sectional = independent samples per wave. Longitudinal = same panel, tracked over time.",
    )
    is_linked = mode == "Longitudinal"
    st.caption(MODE_DESCRIPTIONS[mode])

    st.markdown(
        "**Waves:** " + " → ".join(["Baseline"] + [_round_x_label(r) for r in ROUNDS])
        + ("  *(471-person linked panel only)*" if is_linked else "  *(each wave's own respondents)*")
    )

    st.divider()

    with st.expander("How this comparison works"):
        st.markdown(
            "- **Rounds**: today only Round 1 (~3 months post-campaign) "
            "has real data. Round 2 (~6 mo) and Round 3 (~24 mo) are "
            "shown on every chart as upcoming, clearly-labeled gaps — "
            "never a fabricated value.\n"
            "- **Different survey mode either way**: baseline was an "
            "in-person interview (mostly Hausa); follow-up is a phone "
            "call — see \"Survey questions asked\" in each tab for exact "
            "wording and known differences."
        )
        st.markdown("---")
        _footnotes([
            "`3_linkage/outputs/match_report.txt` — 968 formative, 509 "
            "phone pulse, 471 linked (92.5% of phone pulse respondents).",
        ])

    _render_comparison_type(is_linked)
