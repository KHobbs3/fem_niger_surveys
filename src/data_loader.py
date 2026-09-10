import pandas as pd
import re
import streamlit as st
import os

# ── Raw data loader (only used by pages not yet on the pipeline) ──────────────

def load_raw_data(path="../table_analysis/data/2_cleaned/fem_survey_niger_mapped.csv"):
    df = pd.read_csv(path, low_memory=False)
    df.columns = df.columns.str.strip()
    return df


# ── Pre-aggregated loaders (safe: no PII) ─────────────────────────────────────

DATA_DIR = "data"

def _load(file_id, **kwargs):
    # path = os.path.join(DATA_DIR, filename)
    # if not os.path.exists(path):
    #     return None
    return pd.read_csv("https://drive.google.com/uc?export=download&id="+file_id, **kwargs)


# @st.cache_data
def load_drivers_barriers():
    # df = pd.read_csv(path, low_memory=False)
    # df.columns = df.columns.str.strip()
    return _load("1yr-zA6R7hNEexDGZj06KrO0m0Hb-hOYy") #"1_sKBFc3b32PjHatgIaBY-SSyKlSjCTTQ") - november 2025 version (4 user cats)
                                                     # "1xf4Gkm70WKMC0R_zN6SJZ9JSEqdZUMt9") - december 2025 version (4 user cats)


def load_statement_labels():
    # df = pd.read_csv(path, encoding="ISO-8859-1", low_memory=False)
    # df.columns = df.columns.str.strip()
    # df.dropna(axis=0, how="all", inplace=True)
    # return df
    return _load("1cVSOTJ6VA8FGVUmt8Xw3klBOEobdBqpN")


# ── Access page ───────────────────────────────────────────────────────────────

# @st.cache_data
def load_access_stockouts():
    return _load("1EBowX6uQpTx-fX45a8a-I1QO-qz4UwcR")

# @st.cache_data
def load_access_stockout_responses():
    return _load("1Le5TxvRVT2uQYe-fQQUZikUqduMng3hP", index_col=0)

# @st.cache_data
def load_access_travel():
    return _load("18jWrVGiGDfOw8AZNCNQs5bsuiH8z18Pr", index_col=0)

# @st.cache_data
def load_access_affordability():
    return _load("1ahsiIFxBX-ZjPZ_inL6YCu-Df-W0ClW2", index_col=0)
    # return _load("access_affordability.csv", index_col=0)

# @st.cache_data
def load_access_composite():
    return _load("1pcCZAUorv8coIqW2k_yjkQNXX8rpaSUR", index_col=0)


# ── Statements page ───────────────────────────────────────────────────────────

# @st.cache_data
def load_statements_heatmap():
    return _load("1ezpz_FqegwF1GAPrhtsjQARHI9xxEjT9")

# ── Radio page ──────────────────────────────────────────────────────
def clean_column_name(col):
    col = re.sub(r'^\d+_\d+_', '', col)
    col = re.sub(r'_+\d+$', '', col)
    col = col.replace('_', ' ').strip().title()
    return col

# @st.cache_data
def load_radio_by_station():
    df = _load("1MNO6t_yappsE5ZVp4l2jlZA7qvh1gs5i") #"1l2n9CJcenNTt7CUpf-krApXe9fDsi4r4") November 2025 version
    df.set_index(df.columns[0], inplace=True)
    return df

def load_radio_by_state():
    df = _load("1fMMjeFEEoM6EUgIPC4sNa5xcyi3lOakw")
    df.set_index(df.columns[0], inplace=True)
    return df

# ── Family planning page ──────────────────────────────────────────────────────

# @st.cache_data
def load_fp_funnel():
    return _load("1HfnLz7AaEBRVkWcX5sv8F9uUnmFveju-")

# @st.cache_data
def load_fp_timing():
    return _load("1Oa8g4iGf_IuJiMriVUSZTFILGkutG29c")

# @st.cache_data
def load_fp_methods():
    return _load("1qus99-nxSJVZSbX1x7yA7wCTJyRpCZPQ")

# @st.cache_data
def load_fp_reason_use():
    return _load("1KRrqi-N_tj3GoFAXD8pmns2GgXdxZzws")

# @st.cache_data
def load_fp_intent():
    return _load("1n4r4uPOmsqvMADJDncrvxvzpIFF0y48r")

# @st.cache_data
def load_fp_nonuse_reasons():
    return _load("1My0suLDCypo9G0xbHdMuaHrUocZJKMix")


# 2026-09-04: new output from etl_family_planning.py (ported from
# benin_app), not yet uploaded to Drive. Run
# `python pipeline/run_pipeline.py --pages family_planning` to regenerate
# niger_app/data/fp_unmet.csv, upload it to the same Drive folder as the
# other fp_*.csv files, and paste its file ID below in place of the
# placeholder. Returns None (rather than raising) until then, so the page
# shows its "data not found" message instead of crashing.
def load_fp_unmet():
    try:
        return _load("1VCK1jAU0yDxL0Yx5DEXJ-VrqI4VOGUnK", index_col=0)
    except Exception:
        return None


# ── Personality page ──────────────────────────────────────────────────────────

# @st.cache_data
def load_personality_life_goals():
    return _load("13TCMkDQj1y2X2VrmHBPc_8p098EOI3KY")

# @st.cache_data
def load_personality_goals_achievable():
    return _load("1A5kkyQfiZX_m-e6FqNXMJn75uKDvHhh-")

# @st.cache_data
def load_personality_role_models():
    return _load("1o0zX7lLFPTtJ1yCexMQTFdxara5hawwJ", index_col=0)

# @st.cache_data
def load_personality_likeable_traits():
    return _load("1XjDJRro4Sof1LB_XIfYumwtQJ3QTTmSX")

# @st.cache_data
def load_personality_forming_beliefs():
    return _load("1cRzqqLNGC9PfG7KjGkYJPykDmWCFKxia")

# @st.cache_data
def load_personality_decision_confident():
    return _load("1g1P6ZpElSAzGO09_KGeAgkeenIA8lYYd")

# @st.cache_data
def load_personality_wellbeing():
    return _load("1qnlGPl5N2D0syOBQjSvGe9HAldGi-WfB")


# ── Respondent profile page ───────────────────────────────────────────────────
def load_respondents_profile():
    return _load("1Wiq13fTLzZS1aGRjU_5PwWcpjNnaQ-MU")


# ── Phone Pulse pages ──────────────────────────────────────────────────────────

def _load_pp(file_id: str, **kwargs) -> pd.DataFrame:
    return pd.read_csv("https://drive.google.com/uc?export=download&id="+file_id, **kwargs)


def _load_pp_or_none(file_id: str, **kwargs) -> pd.DataFrame | None:
    """
    Like _load_pp, but returns None instead of raising if the file_id is
    still a PASTE_* placeholder or the Drive fetch fails. Used by pages for
    sections whose export exists locally (etl_pipeline/export_pp_app_data.py)
    but hasn't been uploaded to Drive yet — see each load_pp_* below for the
    exact CSV filename to upload and where to paste the resulting file ID.
    """
    if not file_id or file_id.startswith("PASTE_FILE_ID"):
        return None
    try:
        return _load_pp(file_id, **kwargs)
    except Exception:
        return None

def load_pp_respondents_profile():   return _load_pp("1TVHSn3BwIUvHqT4jwABQ73G35N9qmv0J")
def load_pp_village_stations():      return _load_pp_or_none("1KPlAzbyLNcKE308VwGhwqKcrGze9TZHS")
def load_pp_fp_awareness():          return _load_pp("16ypwYJhHa7FC8d9MRzeticWl1t54N-BK")
def load_pp_fp_method_used():        return _load_pp("1WCjN2ZOKQMnVpxTVG7038FIqV75xEHAu")
def load_pp_fp_whynot():             return _load_pp("15a57RxqiM3S0-ssCj3uhs3P03k0Rdy8z")
def load_pp_fp_preg_chance():        return _load_pp("14ff2F-ApOYekPElVLC9Cc6V-QVGJOzw4")
def load_pp_attitudes():             return _load_pp("1-V85eytJWPhLoSZ6jJkYyK62aNclNY6n")

# pp_info_perceptions.csv output of export_pp_app_data.py. Generate/refresh it with:
#   cd "2_phone pulse/etl_pipeline" && python export_pp_app_data.py
# then upload data/pp_info_perceptions.csv to Drive and paste its file ID
# in place of the placeholder below.
def load_pp_info_perceptions():      return _load_pp_or_none("1wBDMx7GWhJqotPdGVqgQzjXjrm1CM-Ub")
def load_pp_radio_any():             return _load_pp("1Z7n4t6Ym4kPZaT4rufaxk3NojWjkyPVr")
def load_pp_radio_hours():           return _load_pp("1pxyN2c4tk73XuG5qjgk1iMMgRTWc2g1z")
def load_pp_radio_days():            return _load_pp("1Zd0j1fXD6I9OiRGegniDVEHzbf0nhJZb")
def load_pp_radio_uptake():          return _load_pp("1VXQkr5fXazGnRJSUhipSB9Otn1-Pg6fM")
def load_pp_radio_stations():        return _load_pp("1BhMoXwxsw5FgPULn3UitjXdvW_oIedCt")

# pp_radio_fp_stations.csv output of export_pp_app_data.py. Generate/refresh it with:
#   cd "2_phone pulse/etl_pipeline" && python export_pp_app_data.py
# then upload data/pp_radio_fp_stations.csv to Drive and paste its file ID
# in place of the placeholder below.
def load_pp_radio_fp_stations():     return _load_pp_or_none("1sOZpY4vk6ySP2VH1qESCkOWtEzS33RTy")
def load_pp_partner_decision():      return _load_pp("1CWL6zkAIausdpGTAJ_99-AS8tevYcfOB")
def load_pp_partner_norms():         return _load_pp("1frZ0a4TYoA85OBoSOUQUdh7WVj6kFlbn")
def load_pp_partner_discuss():       return _load_pp("1jCFxGacV2ggeRs74zrwLDmVwCFrL34h_")


# ── Media / Access / Social-pressure — NOT YET LIVE ────────────────────────────
# export_pp_app_data.py now writes these CSVs to niger_app/data/ locally. To
# activate a page section: upload the named CSV to Drive with "anyone with the
# link" sharing (same as the loaders above), then paste its file ID in place
# of the PASTE_FILE_ID_<name> placeholder below. Pages using these loaders
# show a "data pending" notice until a real ID is supplied.

def load_pp_tv_any():                return _load_pp_or_none("1mal10JBAvNlf58pXyzTSC0aPPKN2nU8v")
def load_pp_tv_hours():              return _load_pp_or_none("1VuVGUSTdYUOma3Vbp9WJERdBe_xf7Rfs")
def load_pp_tv_topics():             return _load_pp_or_none("1X6LIfwwH9bnHAaAnpRrAiupGPvjMIFAt")
def load_pp_tv_uptake():             return _load_pp_or_none("1RVaL8B1Py5pjN4cPhdCyavzfAHamuXZM")

def load_pp_social_any():            return _load_pp_or_none("15hjjiq6nrPRU6UCOWDzoieJ4IMWWyX9K")
def load_pp_social_hours():          return _load_pp_or_none("1LCPBTw8J6uzkgtcy1nv-95GtVgkhZAwE")
def load_pp_social_uptake():         return _load_pp_or_none("1sKfz1YvJsPKUM8BumYLQRAhOVzGIjyUI")

def load_pp_radio_device():             return _load_pp_or_none("1yEzTFrrtuZpS9MjJ9iD77i0bgxdESGux")
def load_pp_radio_station_frequency():  return _load_pp_or_none("1SjOadZXFGjR3L99SLgt0b7rzgJUhsSrX")
def load_pp_radio_topics():             return _load_pp_or_none("1KPgzfjQAERBMMmL6e9LzrnxAYrOumtr8")
def load_pp_radio_fp_freq():            return _load_pp_or_none("1im_38ITSaHLFmIUTXwOGO_-UGN23dYd-")
def load_pp_radio_conversation():       return _load_pp_or_none("1j2XRgYAke2yxyTMz57Hc2fneKFRUHQL3")
def load_pp_radio_broadcast_opinion():  return _load_pp_or_none("1nKLIUQowFTS8I4Y-FC-MS2HAWiF0Y4Ia")

def load_pp_access_tried():          return _load_pp_or_none("1nlourGhmRMpWf5PO1M14db5VrIs8sHv0")
def load_pp_access_appointment():    return _load_pp_or_none("1iNsgNZhGrWx2_o8SxXBNuSl-1Lwboaah")
def load_pp_access_got_wanted():     return _load_pp_or_none("1tRNSY0HuCvnm2XnDZ3u8TCoCEHP82e7B")
def load_pp_access_unavailable():    return _load_pp_or_none("1sLFTZpKgNyzPu_wYDKy5j7XI4f7LGXa4")
def load_pp_access_location():       return _load_pp_or_none("1CAPvQKIRjGe6oIBej9chXjzib-C2344y")
def load_pp_access_distance():       return _load_pp_or_none("1uy0rZG5pd1Y9jWTxOqtHkhrdY4TmUZF-")

def load_pp_religious_influence():   return _load_pp_or_none("1Tesq6uOxyLKWCBZUGk0GQvPrWuE3Gb04")
def load_pp_info_sources():          return _load_pp_or_none("18UBsj-a-x80n9Z9pXYAXS3TTeDmUZOYj")

# ── Campaign exposure comparison: Treatment vs Comparison ──────────────────────
def load_pp_exposure_profile():        return _load_pp_or_none("1QJXnztFZSW72ZmmVDE0L6FsJ8hUeMbn3")
def load_pp_exposure_fp_awareness():   return _load_pp_or_none("1JUIUgmdR36rRxafBVrU4lHvEm6n8cNuG")
def load_pp_exposure_fp_use():         return _load_pp_or_none("1Gzuh9k3UwWWJL7gECAgKaRimn7EhlUmn")
def load_pp_exposure_attitudes():      return _load_pp_or_none("1LPnUh-FGkcwVqcOe2_UZP6I6zqEMKqWM")
def load_pp_exposure_partner_norms():  return _load_pp_or_none("1BbnIICp3K3CHASeS3_5Bp8Wbl-sDEbhc")


# ── Knowledge change (baseline vs Phone Pulse) ─────────────────────────────────
# TODO: not live yet. Generated by 3_linkage/compare_knowledge.py, which is
# itself blocked on a missing SurveyCTO roster file — see
# "Niger/3_linkage/README.md" for details. Once compare_knowledge.py produces
# outputs/knowledge_change_summary.csv, upload it to Drive (same "anyone with
# the link" sharing as the pp_* files above) and paste its file ID below.
def load_knowledge_change():         return _load_pp("1SIp5w07_e2Q7QwZAkAqW-FdQEpx0ClJv")

# Same deal for compare_fp_use.py's output. Generate it with:
#   cd 3_linkage && python compare_fp_use.py
# then upload outputs/fp_use_change_summary.csv to Drive and paste its file
# ID in place of the placeholder below.
def load_fp_use_change():            return _load_pp_or_none("1seUEGljG3vNDAIfNp61_bvYElpYqYL6M")

# Same deal for compare_unmet_need.py's output (2026-09-04). Generate it with:
#   cd 3_linkage && python link_respondents.py && python compare_unmet_need.py
# then upload outputs/unmet_need_change_summary.csv to Drive and paste its
# file ID in place of the placeholder below.
def load_unmet_need_change():        return _load_pp_or_none("1kdJMRPY33t4JCLKb9Ct5HDaMtT3yrbW1")

# Same deal for compare_method_switching.py's output. Generate it with:
#   cd 3_linkage && python compare_method_switching.py
# then upload outputs/method_switching_summary.csv and
# outputs/method_switching_crosstab.csv to Drive and paste their file IDs in
# place of the placeholders below.
def load_method_switching():         return _load_pp_or_none("1Cb8UuxaA2bwAESTpPIOlCrWyyf5uJuqc")
def load_method_switching_crosstab(): return _load_pp_or_none("17cqQzQKlD5MTWYXPTuu6Tg9EZa9eXRrc")

# Same deal for compare_attitudes.py's output (2026-09-10). Generate it with:
#   cd 3_linkage && python compare_attitudes.py
# then upload outputs/attitudes_change_summary.csv to Drive and paste its
# file ID in place of the placeholder below. NOTE: only 4 of Phone Pulse's 8
# fpatt_* attitude items are covered — see 3_linkage/config.py
# ATTITUDE_CROSSWALK for which, and why the other 4 have no usable baseline
# equivalent.
def load_attitudes_change():         return _load_pp_or_none("PASTE_FILE_ID_attitudes_change")

# Same deal for compare_barriers.py's output (2026-09-10). Generate it with:
#   cd 3_linkage && python compare_barriers.py
# then upload outputs/barriers_change_summary.csv to Drive and paste its
# file ID in place of the placeholder below. NOTE: restricted to the ~68
# linked respondents who answered "why not using FP" on BOTH waves — small,
# treat as directional only.
def load_barriers_change():          return _load_pp_or_none("PASTE_FILE_ID_barriers_change")


# ── Cross-sectional (full baseline vs. full achieved sample) comparison ────────
# Independent-samples counterpart to the "Knowledge change" loaders above —
# same six metrics, but comparing ALL 968 formative respondents against
# EACH round's full achieved Phone Pulse sample (not just the 471 linked),
# using two-proportion z-test / chi-square instead of McNemar/Wilcoxon. See
# 3_linkage/cross_sectional/README.md. Generate every file below with:
#   cd 3_linkage/cross_sectional && python compare_<metric>_unlinked.py
# then upload the named CSV to Drive and paste its file ID in place of the
# PASTE_FILE_ID_<name> placeholder.
def load_knowledge_change_unlinked():        return _load_pp_or_none("PASTE_FILE_ID_knowledge_unlinked")
def load_fp_use_change_unlinked():           return _load_pp_or_none("PASTE_FILE_ID_fp_use_unlinked")
def load_method_switching_unlinked():        return _load_pp_or_none("PASTE_FILE_ID_method_switching_unlinked")
def load_method_switching_crosstab_unlinked(): return _load_pp_or_none("PASTE_FILE_ID_method_switching_crosstab_unlinked")
def load_unmet_need_change_unlinked():       return _load_pp_or_none("PASTE_FILE_ID_unmet_need_unlinked")
def load_attitudes_change_unlinked():        return _load_pp_or_none("PASTE_FILE_ID_attitudes_unlinked")
def load_barriers_change_unlinked():         return _load_pp_or_none("PASTE_FILE_ID_barriers_unlinked")


# ── Personas page ─────────────────────────────────────────────────────────────
# Drive-hosted, like every other page — this app deploys to Streamlit
# Community Cloud from GitHub, and data/ is gitignored (never committed), so
# a local-file loader works on your machine but breaks on the deployed app.

# @st.cache_data
def load_personas_centroids():
    return _load("1qCO4Oh7j4oiK3ZEf28SrxIqNt01CiBAC")

# @st.cache_data
def load_personas_profile():
    return _load("1gbbOIVYiPTV0TKRg2n568I7hlwvcleK4")

def load_personas_centroids_by_gender():
    return _load("1q-NolDxH-kw9goSdKPVknYbqrvWYqe7-")

def load_personas_profile_by_gender():
    return _load("1qqCIVe1YscIRmljahbCLW06Ta9RO_xz8")

def load_personas_elbow():
    return _load("1qX7CZJpt7S7G9sYYd2bXOREVFgosdWc6")

# By-FP-use split (pipeline/etl_personas.py's fp_use clustering).
def load_personas_centroids_by_fp_use():
    return _load_pp_or_none("1UtuWJwHQlU7Am4pZAwxjPN-CRgJZEm_d")

def load_personas_profile_by_fp_use():
    return _load_pp_or_none("1Uh0gAbXueFwZrDiU8z_UoFwPzR1cP8t1")

def load_personas_elbow_by_fp_use():
    return _load_pp_or_none("1o9HKE7rb7j3uq4YsDQ6KYcTAgSxhoKah")


# ── Shared parsing helpers (used by drivers/barriers) ─────────────────────────

def parse_subgroup_prevalence(cell_str):
    result = {}
    if pd.isna(cell_str) or str(cell_str).strip() == "":
        return result
    for line in str(cell_str).split("\n"):
        line = line.strip()
        match = re.match(r"^(.+?):\s*([\d.]+)%", line)
        if match:
            result[match.group(1).strip()] = float(match.group(2))
    return result


def parse_statements(cell_str):
    if pd.isna(cell_str) or str(cell_str).strip() == "":
        return None, {}
    lines = [l.strip() for l in str(cell_str).split("\n") if l.strip()]
    statement = None
    percentages = {}
    for line in lines:
        match = re.match(r"^(.+?):\s*([\d.]+)%", line)
        if match:
            percentages[match.group(1).strip()] = float(match.group(2))
        elif statement is None and "%" not in line:
            statement = line
    return statement, percentages


PRIORITY_ORDER = {"Very high": 4, "High": 3, "Medium": 2, "Low": 1}

def get_priority_sort_key(p):
    return PRIORITY_ORDER.get(str(p).strip(), 0)

USER_CATEGORY_LABELS = {
    "user":        "Current user",
    "nonuser":    "Non-user",
    "future_user": "Future user",
    "past_user":   "Past user",
}

AGE_GROUPS  = ["16-20", "21-30", "31-45"]
GENDERS     = ["Mace / Femme", "Namiji / Homme"]
URBAN_RURAL = ["Rurale", "Semi-urbaine", "Urbaine"]
