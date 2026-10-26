"""
Key family planning indicators -- shared table builders so the Formative
Research, Phone Pulse and Change Over Time pages show them identically.
Identical copy in niger_app, benin_app and togo_app.

Input rows (from fp_headline.csv / pp_headline.csv / key_indicators_change.csv)
are keyed by population ("full_sample", "women") and metric (HEADLINE_METRICS).
"""

import pandas as pd
import streamlit as st

HEADLINE_POPULATIONS = {
    "full_sample": "Full sample",
    "women":       "All women",
}

HEADLINE_METRICS = {
    "mcpr":                  "mCPR",
    "unmet_need":            "Unmet need",
    "unmet_demand":          "Unmet demand",
    "demand_satisfied":      "Demand satisfied (modern methods)",
    "aware_modern":          "Awareness of methods (all)",
    "aware_modern_nonusers": "Awareness of methods (non-users)",
}

# Phone Pulse adds campaign content recall: heard FP programmes/ads on the
# radio AND knows the campaign's "wait at least two years" message.
PULSE_METRICS = {**HEADLINE_METRICS, "campaign_recall": "Campaign content recall"}

NOT_ASKED = "Not asked"
PENDING = "Pending"


def pct(v):
    return f"{v * 100:.1f}%" if pd.notna(v) else "—"


def ci(lo, hi):
    return f"{lo * 100:.1f}–{hi * 100:.1f}%" if pd.notna(lo) and pd.notna(hi) else "—"


def _lookup(df, pop, metric, value="value", lo="ci_low", hi="ci_high", status=None):
    """(value, lo, hi) for one population/metric, NOT_ASKED, or None if absent."""
    if df is None or df.empty:
        return None
    r = df[(df["metric"] == metric) & (df["population"] == pop)]
    if r.empty:
        return None
    r = r.iloc[0]
    if status and r.get(status) == "not_asked":
        return NOT_ASKED
    return r.get(value), r.get(lo), r.get(hi)


def headline_table(df, status=None, metrics=HEADLINE_METRICS):
    """Indicator x population table with 95% CIs (one survey, one wave)."""
    rows = []
    for metric, label in metrics.items():
        row = {"Indicator": label}
        for pop, pop_label in HEADLINE_POPULATIONS.items():
            got = _lookup(df, pop, metric, status=status)
            if got == NOT_ASKED:
                row[pop_label], row[f"{pop_label} 95% CI"] = NOT_ASKED, ""
            else:
                v, lo, hi = got if got else (None, None, None)
                row[pop_label], row[f"{pop_label} 95% CI"] = pct(v), ci(lo, hi)
        rows.append(row)
    return pd.DataFrame(rows)


def wave_cell(got):
    if isinstance(got, str):          # NOT_ASKED, PENDING or pre-formatted text
        return got
    if not got:
        return "—"
    v, lo, hi = got
    return f"{pct(v)} ({ci(lo, hi)})" if pd.notna(lo) else pct(v)


def change_cell(pp, lo, hi, p, n_boot=1000):
    """'+8.7 pp (−1.6 to +19.6), p = 0.10' for a change in percentage points."""
    if pd.isna(pp):
        return "—"
    ptxt = f"p < {2 / n_boot:.3f}" if p <= 2 / n_boot else f"p = {p:.2f}" if p >= 0.01 else f"p = {p:.3f}"
    return f"{pp:+.1f} pp ({lo:+.1f} to {hi:+.1f}), {ptxt}".replace("-", "−")


def change_table(population, waves, metrics=HEADLINE_METRICS):
    """One row per indicator, one column per wave: "x% (lo–hi%)".

    waves: list of (column label, lookup function (metric) -> (v, lo, hi) |
    NOT_ASKED | PENDING | None).
    """
    rows = []
    for metric, label in metrics.items():
        row = {"Indicator": label}
        for wave_label, lookup in waves:
            row[wave_label] = wave_cell(lookup(metric))
        rows.append(row)
    return pd.DataFrame(rows)


def show(table):
    st.dataframe(table, use_container_width=True, hide_index=True)
