"""
ui_helpers.py: Centralized Neumorphism (Soft UI) design system tokens,
styling components, and Plotly theme orchestrator for StrategicBid.
Adheres strictly to the Cool Monochromatic #E0E5EC design system.
"""

import streamlit as st
from typing import Optional, Dict, Any, List
from src.data_loader import ensure_data_available, load_raw_auction_data
from src.preprocessing import preprocess_auction_data
import pandas as pd
import plotly.graph_objects as go

# ==============================================================================
# NEUMORPHIC DESIGN SYSTEM TOKENS & CSS
# ==============================================================================

CUSTOM_CSS = """
<style>
/* Import Google Fonts with display=swap */
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,700;1,9..40,400&family=Plus+Jakarta+Sans:wght@500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --neu-bg: #E0E5EC;
    --neu-fg: #3D4852;
    --neu-muted: #6B7280;
    --neu-accent: #6C63FF;
    --neu-accent-light: #8B84FF;
    --neu-accent-secondary: #38B2AC;
    
    /* Shadows */
    --shadow-extruded: 9px 9px 16px rgba(163, 177, 198, 0.6), -9px -9px 16px rgba(255, 255, 255, 0.5);
    --shadow-extruded-hover: 12px 12px 20px rgba(163, 177, 198, 0.7), -12px -12px 20px rgba(255, 255, 255, 0.6);
    --shadow-extruded-sm: 5px 5px 10px rgba(163, 177, 198, 0.6), -5px -5px 10px rgba(255, 255, 255, 0.5);
    --shadow-inset: inset 6px 6px 10px rgba(163, 177, 198, 0.6), inset -6px -6px 10px rgba(255, 255, 255, 0.5);
    --shadow-inset-deep: inset 10px 10px 20px rgba(163, 177, 198, 0.7), inset -10px -10px 20px rgba(255, 255, 255, 0.6);
    --shadow-inset-sm: inset 3px 3px 6px rgba(163, 177, 198, 0.6), inset -3px -3px 6px rgba(255, 255, 255, 0.5);
}

/* Global Background and Typography */
html, body, .stApp {
    background-color: var(--neu-bg) !important;
    color: var(--neu-fg) !important;
    font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

h1, h2, h3, h4, .font-display {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    color: var(--neu-fg) !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em !important;
}

code, pre {
    font-family: 'JetBrains Mono', monospace !important;
    background-color: var(--neu-bg) !important;
    box-shadow: var(--shadow-inset-sm) !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.2rem 0.4rem !important;
    color: var(--neu-fg) !important;
}

/* Header & Sidebar overrides */
header[data-testid="stHeader"] {
    background-color: rgba(224, 229, 236, 0.85) !important;
    backdrop-filter: blur(12px) !important;
}

section[data-testid="stSidebar"] {
    background-color: var(--neu-bg) !important;
    border-right: none !important;
    box-shadow: 4px 0 16px rgba(163, 177, 198, 0.35) !important;
}

section[data-testid="stSidebar"] * {
    color: var(--neu-fg) !important;
}

/* Neumorphic Extruded Metric Card */
.metric-card {
    background: var(--neu-bg);
    border-radius: 32px;
    padding: 1.4rem 1.6rem;
    box-shadow: var(--shadow-extruded);
    border: none;
    transition: all 300ms ease-out;
    margin-bottom: 1.2rem;
}

.metric-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-extruded-hover);
}

.metric-label {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.82rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--neu-muted);
    margin-bottom: 0.4rem;
    font-weight: 700;
}

.metric-value {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 2.1rem;
    font-weight: 800;
    color: var(--neu-fg);
    letter-spacing: -0.03em;
    line-height: 1.15;
}

.metric-sub {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.82rem;
    color: var(--neu-muted);
    margin-top: 0.45rem;
    font-weight: 500;
}

/* Neumorphic Inset Deep Well (Info & Containers) */
.info-box {
    background: var(--neu-bg);
    border-radius: 24px;
    padding: 1.3rem 1.6rem;
    margin: 1.2rem 0;
    font-size: 0.92rem;
    color: var(--neu-fg);
    line-height: 1.6;
    box-shadow: var(--shadow-inset-deep);
    border: none;
}

.info-box strong {
    color: var(--neu-fg);
    font-weight: 700;
}

/* Neumorphic Disclaimer Banner */
.disclaimer-banner {
    background: var(--neu-bg);
    border-radius: 24px;
    padding: 1.2rem 1.5rem;
    margin: 1.2rem 0;
    font-size: 0.88rem;
    color: var(--neu-fg);
    line-height: 1.55;
    box-shadow: var(--shadow-inset);
    border-left: 5px solid #F59E0B;
}

.disclaimer-banner strong {
    color: #D97706;
}

/* Neumorphic Badge Tag */
.badge-tag {
    display: inline-block;
    padding: 0.35rem 0.85rem;
    border-radius: 9999px;
    font-size: 0.74rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    background: var(--neu-bg);
    color: var(--neu-accent);
    box-shadow: var(--shadow-inset-sm);
    margin-bottom: 0.6rem;
}

/* Streamlit Native Button Overrides */
.stButton > button, div.stDownloadButton > button {
    background-color: var(--neu-bg) !important;
    color: var(--neu-fg) !important;
    border: none !important;
    border-radius: 16px !important;
    box-shadow: var(--shadow-extruded-sm) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.92rem !important;
    padding: 0.65rem 1.4rem !important;
    transition: all 300ms ease-out !important;
}

.stButton > button:hover, div.stDownloadButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: var(--shadow-extruded-hover) !important;
    color: var(--neu-accent) !important;
}

.stButton > button:active, div.stDownloadButton > button:active {
    transform: translateY(0.5px) !important;
    box-shadow: var(--shadow-inset-sm) !important;
}

.stButton > button:focus, div.stDownloadButton > button:focus {
    outline: none !important;
    box-shadow: var(--shadow-extruded-sm), 0 0 0 2px var(--neu-bg), 0 0 0 4px var(--neu-accent) !important;
}

/* Primary / Highlight Button */
.stButton > button[kind="primary"] {
    background-color: var(--neu-accent) !important;
    color: #FFFFFF !important;
    box-shadow: 5px 5px 12px rgba(108, 99, 255, 0.4), -5px -5px 12px rgba(255, 255, 255, 0.7) !important;
}

/* Streamlit Selectbox & Input Overrides */
div[data-baseweb="select"] > div,
div[data-baseweb="input"] > div {
    background-color: var(--neu-bg) !important;
    border: none !important;
    border-radius: 16px !important;
    box-shadow: var(--shadow-inset) !important;
    color: var(--neu-fg) !important;
    padding: 0.2rem 0.5rem !important;
    font-family: 'DM Sans', sans-serif !important;
}

div[data-baseweb="select"] > div:hover,
div[data-baseweb="input"] > div:hover {
    box-shadow: var(--shadow-inset-deep) !important;
}

div[data-baseweb="select"] * {
    color: var(--neu-fg) !important;
}

/* Selectbox Dropdown Menu Popover */
div[data-baseweb="popover"], ul[role="listbox"] {
    background-color: var(--neu-bg) !important;
    border-radius: 20px !important;
    border: none !important;
    box-shadow: var(--shadow-extruded) !important;
    padding: 0.5rem !important;
}

li[role="option"] {
    background-color: transparent !important;
    color: var(--neu-fg) !important;
    border-radius: 12px !important;
    padding: 0.5rem 0.8rem !important;
    transition: all 150ms ease-out !important;
}

li[role="option"]:hover, li[aria-selected="true"] {
    background-color: rgba(108, 99, 255, 0.12) !important;
    color: var(--neu-accent) !important;
}

/* Streamlit Slider Styling */
.stSlider div[data-baseweb="slider"] {
    padding: 1.2rem 0 !important;
}

.stSlider div[data-baseweb="slider"] > div > div {
    background-color: rgba(163, 177, 198, 0.4) !important;
    box-shadow: var(--shadow-inset-sm) !important;
    height: 8px !important;
    border-radius: 9999px !important;
}

.stSlider div[data-baseweb="slider"] > div > div > div {
    background-color: var(--neu-accent) !important;
    border-radius: 9999px !important;
}

.stSlider div[role="slider"] {
    background-color: var(--neu-bg) !important;
    box-shadow: var(--shadow-extruded-sm) !important;
    border: 2px solid var(--neu-accent) !important;
    width: 20px !important;
    height: 20px !important;
    transition: transform 150ms ease-out !important;
}

.stSlider div[role="slider"]:hover {
    transform: scale(1.15) !important;
}

/* Streamlit DataFrame / Table styling */
div[data-testid="stDataFrame"] {
    background: var(--neu-bg) !important;
    border-radius: 24px !important;
    padding: 0.8rem !important;
    box-shadow: var(--shadow-inset) !important;
}

/* Plotly Chart Card Container */
.plotly-card {
    background: var(--neu-bg);
    border-radius: 32px;
    padding: 1.2rem 1.4rem;
    box-shadow: var(--shadow-extruded);
    margin-bottom: 1.5rem;
    transition: all 300ms ease-out;
}

.plotly-card:hover {
    box-shadow: var(--shadow-extruded-hover);
}

/* Universal Transitions */
* {
    transition: color 200ms ease-out;
}
</style>
"""


def apply_theme():
    """Injects custom Neumorphic CSS into the Streamlit session."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def render_page_header(title: str, subtitle: str, tag: str = "Empirical Auction Game Theory"):
    """Renders a standardized, Neumorphic page header."""
    st.markdown(
        f"""
        <div style="margin-bottom: 2rem; padding-bottom: 1rem;">
            <span class="badge-tag">{tag}</span>
            <h1 style="margin: 0.4rem 0 0.4rem 0; font-size: 2.3rem; font-weight: 800; color: #3D4852; letter-spacing: -0.03em;">
                {title}
            </h1>
            <p style="margin: 0; color: #6B7280; font-size: 1.02rem; font-weight: 500;">
                {subtitle}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_counterfactual_disclaimer():
    """Displays the mandatory scientific disclaimer banner for counterfactual replays."""
    st.markdown(
        """
        <div class="disclaimer-banner">
            <strong>⚠️ SCIENTIFIC NOTICE & COUNTERFACTUAL SPECIFICATION:</strong><br>
            Counterfactual replay calculates theoretical payment rules using static, observed historical bid records.
            This is <em>not</em> an observed outcome under this auction mechanism.
            Strategic bidders in an actual First-Price auction would have shaded their bids,
            resulting in different submitted values.
        </div>
        """,
        unsafe_allow_html=True
    )


def render_sidebar_metadata():
    """Renders data provenance and source links in the Streamlit sidebar."""
    with st.sidebar:
        st.markdown(
            """
            <div style="padding: 0.5rem 0;">
                <span class="badge-tag">Soft UI • Monochromatic</span>
                <h3 style="margin-top: 0.4rem; font-size: 1.35rem; color: #3D4852;">StrategicBid</h3>
                <p style="font-size: 0.85rem; color: #6B7280; margin-bottom: 1rem;">
                    Game Theory for Data Science
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        st.markdown(
            """
            <div class="info-box" style="padding: 1rem 1.2rem; font-size: 0.84rem; margin-top: 0;">
                <strong>Dataset Provenance:</strong><br>
                • <strong>Source</strong>: Online Auctions Dataset<br>
                • <strong>Platform</strong>: Historical eBay Records<br>
                • <strong>DOI</strong>: <a href="https://doi.org/10.5281/zenodo.11259259" target="_blank" style="color: #6C63FF; text-decoration: none; font-weight: 600;">10.5281/zenodo.11259259</a><br>
                • <strong>License</strong>: CC-BY-4.0<br>
                • <strong>Verification</strong>: SHA-256 Verified
            </div>
            """,
            unsafe_allow_html=True
        )
        st.caption("Tactile Neumorphic Design • #E0E5EC Cool Clay")


def apply_plotly_theme(fig: go.Figure) -> go.Figure:
    """
    Applies the Neumorphic Design System theme to any Plotly chart.
    Ensures seamless blending with the #E0E5EC surface, DM Sans typography,
    subtle cool grey gridlines, and WCAG-compliant color accents.
    """
    fig.update_layout(
        paper_bgcolor="#E0E5EC",
        plot_bgcolor="#E0E5EC",
        font=dict(
            family="DM Sans, -apple-system, sans-serif",
            size=12,
            color="#3D4852"
        ),
        title_font=dict(
            family="Plus Jakarta Sans, sans-serif",
            size=15,
            color="#3D4852"
        ),
        margin=dict(l=24, r=24, t=48, b=24),
        hoverlabel=dict(
            bgcolor="#E0E5EC",
            font_size=12,
            font_family="DM Sans, sans-serif",
            bordercolor="rgba(163, 177, 198, 0.7)"
        ),
        legend=dict(
            bgcolor="rgba(224, 229, 236, 0.8)",
            bordercolor="rgba(163, 177, 198, 0.4)",
            borderwidth=1,
            font=dict(color="#3D4852")
        )
    )

    fig.update_xaxes(
        gridcolor="rgba(163, 177, 198, 0.35)",
        linecolor="rgba(163, 177, 198, 0.5)",
        tickfont=dict(color="#6B7280"),
        title_font=dict(color="#3D4852", size=13, family="Plus Jakarta Sans")
    )
    fig.update_yaxes(
        gridcolor="rgba(163, 177, 198, 0.35)",
        linecolor="rgba(163, 177, 198, 0.5)",
        tickfont=dict(color="#6B7280"),
        title_font=dict(color="#3D4852", size=13, family="Plus Jakarta Sans")
    )
    return fig


# Neumorphic Color Palette
NEU_PALETTE = ["#6C63FF", "#38B2AC", "#F43F5E", "#8B84FF", "#F59E0B"]


@st.cache_data(show_spinner="Loading verified auction data...")
def get_cached_datasets():
    """
    Cached data loader for Streamlit pages.
    Guarantees that raw data is verified, preprocessed, and cached in memory.
    """
    ensure_data_available()
    raw_df = load_raw_auction_data()
    clean_bids, clean_auctions, cleaning_log = preprocess_auction_data(raw_df, save_processed=True)
    return clean_bids, clean_auctions, cleaning_log
