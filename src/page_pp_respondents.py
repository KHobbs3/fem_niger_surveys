"""
Phone Pulse — Respondent Profile.
Descriptive statistics of the analysis sample, laid out like the Formative
Research Respondents page (headline N + Variable / Category / N / % table).
All data is pre-aggregated (no PII).

The Pulse questionnaire did not ask age, occupation, religion or settlement
type; those rows come from each respondent's formative baseline record via
3_linkage/link_respondents.py (linked_demographics.csv), so they cover only
the linked share of the sample (_n_linked).
"""

import streamlit as st
import pandas as pd

from src.data_loader import load_pp_respondents_profile, load_pp_village_stations

# Display order of variables and their labels — same variables, in the same
# order, as the Formative Research Respondents page.
VAR_ORDER = [
    ("fp_use",  "Current FP use"),
    ("gender",      "Gender"),
    ("age_group",   "Age group"),
    ("occupation",  "Occupation"),
    ("religion",    "Religion"),
    ("urban_rural", "Settlement type"),
]

# Phone-Pulse-only location breakdown, shown in an expander below the main table
LOCATION_VAR_ORDER = [
    ("region",  "Region"),
    ("village", "Village"),
]

_TABLE_COLUMN_CONFIG = {
    "Variable": st.column_config.TextColumn("Variable", width="medium"),
    "Category": st.column_config.TextColumn("Category", width="medium"),
    "N":        st.column_config.NumberColumn("N", format="%d", width="small"),
    "%":        st.column_config.TextColumn("%", width="small"),
}

# Preferred category order within variables (others sorted by count)
CATEGORY_ORDER = {
    "fp_use": ["Using FP", "Not using FP"],
    "gender":    ["Female", "Male"],
    "age_group": ["16-20", "21-30", "31-45"],
    "urban_rural": ["Rurale", "Semi-urbaine", "Urbaine"],
}

# Raw roster labels are bilingual Hausa / French; show English like the
# formative page does.
CATEGORY_LABELS = {
    "gender": {"Mace / Femme": "Female", "Namiji / Homme": "Male"},
}


def _row_count(df: pd.DataFrame, variable: str):
    row = df[df["variable"] == variable]
    if row.empty or pd.isna(row["count"].iloc[0]):
        return None
    return int(row["count"].iloc[0])


def _build_table(df: pd.DataFrame, var_order=VAR_ORDER) -> pd.DataFrame:
    rows = []
    for var, label in var_order:
        sub = df[df["variable"] == var].copy()
        if sub.empty:
            continue
        sub["category"] = sub["category"].replace(CATEGORY_LABELS.get(var, {}))

        # Apply preferred category order
        if var in CATEGORY_ORDER:
            ordered = [c for c in CATEGORY_ORDER[var] if c in sub["category"].values]
            rest    = sorted(c for c in sub["category"].values if c not in ordered)
            sub = sub.set_index("category").reindex(ordered + rest).reset_index()
        else:
            sub = sub.sort_values("count", ascending=False)

        for _, row in sub.iterrows():
            rows.append({
                "Variable": label,
                "Category": row["category"],
                "N":        int(row["count"]),
                "%":        f"{row['proportion'] * 100:.1f}%",
            })

    return pd.DataFrame(rows)


def render() -> None:
    st.markdown("## Respondent Profile")

    df = load_pp_respondents_profile()

    n_raw           = _row_count(df, "_n_raw")
    n_excl_quality  = _row_count(df, "_n_quality_excluded")
    n_after_qa      = _row_count(df, "_n_after_qa")
    n_no_radio      = _row_count(df, "_n_no_radio")
    n_radio_not_fem = _row_count(df, "_n_radio_not_fem")
    n_fem           = _row_count(df, "_n_fem_listeners")
    n_total         = _row_count(df, "_total")
    n_linked        = _row_count(df, "_n_linked")

    # Headline N
    if n_total is not None:
        st.metric("Survey respondents (N)", f"{n_total:,}")

    st.markdown("")

    table = _build_table(df)
    if table.empty:
        st.info("No demographic data available.")
        return

    st.dataframe(
        table,
        use_container_width=True,
        hide_index=True,
        column_config=_TABLE_COLUMN_CONFIG,
    )
    if n_linked is not None and n_total:
        demo_note = (
            f"Age group, occupation, religion and settlement type come from the "
            f"formative baseline survey (not asked in Phone Pulse), for the {n_linked} "
            f"of {n_total} respondents ({100 * n_linked / n_total:.0f}%) linked to "
            f"their baseline record; % is of linked respondents."
        )
    else:
        demo_note = (
            "Age group, occupation, religion and settlement type were not asked in "
            "Phone Pulse and appear once the baseline linkage "
            "(3_linkage/link_respondents.py) has been run."
        )
    st.caption(
        f"{demo_note} Current FP use % is of respondents who answered fpbeh_fpnow."
    )

    if n_raw is not None:
        n_comparison = (n_no_radio or 0) + (n_radio_not_fem or 0)
        with st.expander("How the sample was defined"):
            st.markdown(
                f"Of {n_raw} raw submissions, {n_excl_quality} were excluded for quality "
                f"concerns (duplicates, errors, nonresponse, placebo-station, dishonesty, "
                f"or not-a-radio-listener flags — see manual_flags.csv). Of the {n_after_qa} "
                f"that passed QA, this page covers only the {n_fem} FEM-partner-station "
                f"listeners (Treatment). The remaining {n_comparison} respondents (no radio, "
                f"or radio but not a FEM station) are the Comparison arm, analysed on the "
                f"Campaign Exposure page."
            )

    location = _build_table(df, LOCATION_VAR_ORDER)
    if not location.empty:
        with st.expander("Region & village"):
            st.dataframe(
                location,
                use_container_width=True,
                hide_index=True,
                column_config=_TABLE_COLUMN_CONFIG,
            )
            st.caption("Villages with fewer than 5 respondents are omitted for privacy.")

    # Village x station coverage map
    vs = load_pp_village_stations()
    if vs is not None and not vs.empty:
        with st.expander("Station coverage by village"):
            _render_village_stations(vs)
    elif vs is None:
        st.info(
            "Village x station coverage pending: run `export_pp_app_data.py`, upload "
            "`pp_village_stations.csv` to Drive, then paste its file ID into `data_loader.py`."
        )


def _render_village_stations(vs: pd.DataFrame) -> None:
    st.caption(
        "Real FEM partner station(s) assigned to cover each village's settlement "
        "(from the roster, not listening behaviour). Villages with fewer than 5 "
        "respondents are suppressed for privacy."
    )
    vs_disp = vs.rename(
        columns={"village": "Village", "station": "Station", "n_respondents": "N respondents"}
    )
    st.dataframe(vs_disp, use_container_width=True, hide_index=True)
