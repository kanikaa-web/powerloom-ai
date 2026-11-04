"""
branding.py
-----------
Central brand configuration for Barkavi Textiles.
Change the name / logo here once and it applies to the whole app,
PDF reports and Excel reports.
"""

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

# ---------- Brand text ----------
BRAND_NAME = "Barkavi Textiles"
BRAND_TAGLINE = "AI-Powered Smart Powerloom Production System"
BRAND_SUBTITLE = "Raw Material Prediction & Production Planning using Machine Learning"
BRAND_ADDRESS = "2/198 Panamarathukadu, Rasagoundampalayam, Palladam - 641664, Tirupur"
BRAND_GST = "33AFLPV4411JZA"

# ---------- Brand colours (taken from the logo) ----------
BRAND_GOLD = "#B07A1E"
BRAND_GOLD_LIGHT = "#D4A445"

# ---------- Logo files ----------
LOGO_BANNER = os.path.join(ASSETS_DIR, "barkavi_banner.png")                  # full letterhead (GST + address)
LOGO_MAIN = os.path.join(ASSETS_DIR, "barkavi_logo.png")                      # emblem + name, cream background
LOGO_MAIN_TRANSPARENT = os.path.join(ASSETS_DIR, "barkavi_logo_transparent.png")
LOGO_ICON = os.path.join(ASSETS_DIR, "barkavi_icon.png")                      # emblem only, square
LOGO_ICON_TRANSPARENT = os.path.join(ASSETS_DIR, "barkavi_icon_transparent.png")


def page_icon():
    """Return the favicon path (falls back to an emoji if the file is missing)."""
    return LOGO_ICON if os.path.exists(LOGO_ICON) else "🧵"


def apply_sidebar_logo():
    """Show the Barkavi Textiles logo at the top of the sidebar on every page."""
    import streamlit as st

    if not os.path.exists(LOGO_MAIN_TRANSPARENT):
        return
    try:
        # Streamlit >= 1.35
        st.logo(LOGO_MAIN_TRANSPARENT, icon_image=LOGO_ICON_TRANSPARENT)
    except AttributeError:
        st.sidebar.image(LOGO_MAIN_TRANSPARENT)

    # Make the sidebar logo larger than Streamlit's small default
    st.markdown(
        """
        <style>
            [data-testid="stSidebarHeader"] img,
            [data-testid="stLogo"] { height: 3.4rem !important; max-width: 100% !important; }
            [data-testid="stSidebarHeader"] { padding-bottom: 0.5rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )
