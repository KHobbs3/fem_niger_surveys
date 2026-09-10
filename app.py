import streamlit as st
from streamlit_option_menu import option_menu

# Formative research pages
from src.page_respondents import render as render_respondents
from src.page_drivers_barriers import render as render_drivers_barriers
from src.page_radio import render as render_radio
from src.page_personas import render as render_personas
from src.page_statements import render as render_agreement_characteristics
from src.page_access import render as render_access
from src.page_family_planning import render as render_family_planning
from src.page_personality_traits import render as render_personality_traits

# Phone Pulse pages
from src.page_pp_respondents import render as render_pp_respondents
from src.page_pp_family_planning import render as render_pp_family_planning
from src.page_pp_attitudes import render as render_pp_attitudes
from src.page_pp_radio import render as render_pp_radio
from src.page_pp_partner_norms import render as render_pp_partner_norms
from src.page_pp_media import render as render_pp_media
from src.page_pp_access import render as render_pp_access
from src.page_pp_social_pressure import render as render_pp_social_pressure
from src.page_pp_exposure import render as render_pp_exposure
from src.page_pp_change_over_time import render as render_pp_change_over_time

# from src.page_stubs import (
    # render_personas,
    # render_agreement_characteristics,
    # render_family_planning,
    # render_personality_traits,
    # render_access,
# )

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FEM Survey Analysis — Niger (2025)",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# FEM colour palette (warm terracotta -> taupe -> steel -> navy)
FEM_ORANGE  = "#C1693A"
FEM_BROWN   = "#8B5E45"
FEM_TAUPE   = "#7A7068"
FEM_STEEL   = "#5A6E7F"
FEM_NAVY    = "#2E3F52"

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
    /* Top bar colour */
    [data-testid="stHeader"] {{ background: {FEM_STEEL}; }}

    /* Main title text — ensure black */
    h1, h2, h3 {{ color: {FEM_BROWN} !important; }}

    /* Nav menu tweaks */
    .nav-link {{ font-size: 13px !important; padding: 4px 8px !important; }}
    .nav-link-selected {{ background-color: {FEM_BROWN} !important; }}

    /* Tighten plotly chart margins */
    .js-plotly-plot {{ margin-bottom: -1rem; }}

    /* Divider colour */
    hr {{ border-color: #e5e7eb !important; margin: 0.6rem 0 !important; }}

    /* Priority badge alignment */
    .stMarkdown p {{ margin-bottom: 0.2rem; }}
</style>
""", unsafe_allow_html=True)

# ── Title ─────────────────────────────────────────────────────────────────────
st.markdown(
    f"<h2 style='margin-bottom:0.2rem;color:{FEM_BROWN};'>FEM Survey Analysis - Niger (2025)</h2>",
    unsafe_allow_html=True,
)
st.caption(
    "Niger Phone Pulse survey margin of error: designed for a 5% minimum "
    "detectable effect (MDE), target sample size ~750 respondents. Actual "
    "achieved sample: 544 raw submissions, 509 after QA exclusions (see the "
    "Phone Pulse → Respondents page for the full funnel)."
)

# ── Top-level survey switcher ─────────────────────────────────────────────────
survey = option_menu(
    menu_title=None,
    options=["Formative Research", "Phone Pulse"],
    icons=["journal-text", "telephone-fill"],
    menu_icon="cast",
    default_index=0,
    orientation="horizontal",
    styles={
        "container": {"background-color": FEM_BROWN, "padding": "0 4px", "margin": "0 0 4px 0"},
        "icon":      {"color": "#f5e6d8", "font-size": "15px"},
        "nav-link":  {"color": "#f5e6d8", "padding": "5px 18px", "--hover-color": FEM_ORANGE,
                      "font-size": "14px", "font-weight": "600"},
        "nav-link-selected": {"background-color": FEM_NAVY, "color": "#ffffff"},
    },
)

st.markdown("")  # breathing room

# ══════════════════════════════════════════════════════════════════════════════
# FORMATIVE RESEARCH
# ══════════════════════════════════════════════════════════════════════════════
if survey == "Formative Research":
    selected = option_menu(
        menu_title=None,
        options=[
            "Respondents",
            "Personas",
            "Drivers & Barriers",
            "Agreement & Characteristics",
            "Radio",
            "Family Planning",
            "Personality Traits",
            "Access & Supply",
        ],
        icons=[
            "bar-chart-fill",
            "people-fill",
            "speedometer2",
            "card-checklist",
            "speaker-fill",
            "house-heart-fill",
            "file-earmark-person-fill",
            "capsule",
        ],
        menu_icon="cast",
        default_index=1,
        orientation="horizontal",
        styles={
            "container": {"background-color": FEM_TAUPE, "padding": "0", "margin": "0"},
            "icon":      {"color": FEM_ORANGE, "font-size": "14px"},
            "nav-link":  {"padding": "4px 10px", "--hover-color": FEM_STEEL},
            "nav-link-selected": {"background-color": FEM_NAVY},
        },
    )

    st.markdown("")

    if selected == "Respondents":
        render_respondents()
    elif selected == "Personas":
        render_personas()
    elif selected == "Drivers & Barriers":
        render_drivers_barriers()
    elif selected == "Agreement & Characteristics":
        render_agreement_characteristics()
    elif selected == "Radio":
        render_radio()
    elif selected == "Family Planning":
        render_family_planning()
    elif selected == "Personality Traits":
        render_personality_traits()
    elif selected == "Access & Supply":
        render_access()

# ══════════════════════════════════════════════════════════════════════════════
# PHONE PULSE
# ══════════════════════════════════════════════════════════════════════════════
elif survey == "Phone Pulse":
    pp_selected = option_menu(
        menu_title=None,
        options=[
            "Change Over Time",
            "Respondents",
            "Campaign Exposure",
            "Family Planning",
            "Attitudes",
            "Radio",
            "Partner & Norms",
            "Media",
            "Access Barriers",
            "Social Pressure",
        ],
        icons=[
            "arrow-left-right",
            "bar-chart-fill",
            "broadcast",
            "house-heart-fill",
            "chat-quote-fill",
            "speaker-fill",
            "people-fill",
            "tv-fill",
            "signpost-split-fill",
            "chat-square-heart-fill",
        ],
        menu_icon="telephone-fill",
        default_index=0,
        orientation="horizontal",
        styles={
            "container": {"background-color": FEM_STEEL, "padding": "0", "margin": "0"},
            "icon":      {"color": "#dce8f0", "font-size": "14px"},
            "nav-link":  {"color": "#dce8f0", "padding": "4px 10px",
                          "--hover-color": FEM_TAUPE},
            "nav-link-selected": {"background-color": FEM_NAVY},
        },
    )

    st.markdown("")

    if pp_selected == "Change Over Time":
        render_pp_change_over_time()
    elif pp_selected == "Respondents":
        render_pp_respondents()
    elif pp_selected == "Campaign Exposure":
        render_pp_exposure()
    elif pp_selected == "Family Planning":
        render_pp_family_planning()
    elif pp_selected == "Attitudes":
        render_pp_attitudes()
    elif pp_selected == "Radio":
        render_pp_radio()
    elif pp_selected == "Partner & Norms":
        render_pp_partner_norms()
    elif pp_selected == "Media":
        render_pp_media()
    elif pp_selected == "Access Barriers":
        render_pp_access()
    elif pp_selected == "Social Pressure":
        render_pp_social_pressure()
