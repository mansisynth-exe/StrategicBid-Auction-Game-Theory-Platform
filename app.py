"""
app.py: StrategicBid Main Entry Point & Overview Dashboard.
Authentic historical auction analytics powered by game-theoretic foundations.
Strictly adheres to real data verification with zero synthetic fallbacks.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from src.ui_helpers import (
    apply_theme,
    render_page_header,
    render_sidebar_metadata,
    get_cached_datasets,
    apply_plotly_theme,
    NEU_PALETTE
)
from src.metrics import format_currency, format_integer, format_percentage
from src.data_loader import DataAcquisitionError

# Configure page settings
st.set_page_config(
    page_title="StrategicBid | Auction Game Theory",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_theme()
render_sidebar_metadata()

render_page_header(
    title="StrategicBid: Auction Game Theory Platform",
    subtitle="Empirical historical analysis and counterfactual mechanism replays on authentic online auction records.",
    tag="Neumorphic Soft UI • Monochromatic"
)

try:
    clean_bids, clean_auctions, cleaning_log = get_cached_datasets()
except DataAcquisitionError as err:
    st.error(f"### 🛑 Authentic Data Acquisition Blocker\n{str(err)}")
    st.info("Under strict scientific guidelines, synthetic or simulated fallback records are prohibited.")
    st.stop()
except Exception as e:
    st.error(f"### ⚠️ Data Pipeline Execution Error: {str(e)}")
    st.stop()

# ==============================================================================
# SECTION 1: TOP-LEVEL AUTHENTIC METRICS
# ==============================================================================

total_bids = len(clean_bids)
total_auctions = len(clean_auctions)
distinct_bidders = clean_bids["bidder_id"].nunique()
median_price = clean_auctions["price"].median()
mean_price = clean_auctions["price"].mean()
median_bids_per_auc = clean_auctions["bids_count"].median()
eligible_replays = clean_auctions["is_eligible_replay"].sum()

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Historical Bids</div>
            <div class="metric-value">{format_integer(total_bids)}</div>
            <div class="metric-sub">Observed bid records</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col2:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Unique Auctions</div>
            <div class="metric-value">{format_integer(total_auctions)}</div>
            <div class="metric-sub">Unit of price analysis</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col3:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Distinct Bidders</div>
            <div class="metric-value">{format_integer(distinct_bidders)}</div>
            <div class="metric-sub">Salted SHA-256 tokens</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col4:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Median Price</div>
            <div class="metric-value">{format_currency(median_price)}</div>
            <div class="metric-sub">Mean: {format_currency(mean_price)}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col5:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Median Bids/Auc</div>
            <div class="metric-value">{median_bids_per_auc:.1f}</div>
            <div class="metric-sub">Eligible replays: {eligible_replays}/{total_auctions}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

# ==============================================================================
# SECTION 2: PLATFORM SUMMARY & SCIENTIFIC SCOPE
# ==============================================================================

st.markdown("### 🔬 Executive Overview & Methodological Principles")

overview_col1, overview_col2 = st.columns([3, 2])

with overview_col1:
    st.markdown(
        """
        **StrategicBid** investigates the strategic behavior of online auction bidders by linking
        non-cooperative game-theoretic equilibrium concepts with authentic empirical observations from eBay.

        Unlike standard textbook treatments that assume private valuations $v_i$ are directly accessible,
        real-world ascending proxy auctions obscure valuations and introduce strategic temporal incentives.
        This platform separates empirical facts from theoretical equilibrium benchmarks:
        """
    )
    
    st.markdown(
        """
        - **Component A: Empirical Analysis**: Examines actual observed bid timing (sniping),
          bids-per-auction distributions, opening bid correlations, and category-level pricing across
          **Palm Pilot M515 PDAs**, **Xbox game consoles**, and **Cartier wristwatches**.
        - **Component B: Counterfactual Mechanism Replay**: Uses actual submitted bids to simulate
          payment outcomes under alternative First-Price and Second-Price sealed-bid rules without
          fabricating unobserved buyer willingness-to-pay.
        """
    )

with overview_col2:
    st.markdown(
        """
        <div class="info-box">
            <strong>🔒 Scientific & Privacy Commitments:</strong><br><br>
            • <strong>Real Data Only</strong>: Zero synthetic records or mock fallbacks.<br>
            • <strong>Traceability</strong>: Every chart and metric derives from Zenodo record 11259259.<br>
            • <strong>No Unfounded Claims</strong>: Does not claim Nash Equilibrium proof from observational averages.<br>
            • <strong>Bidder Privacy</strong>: Usernames are deterministically pseudonymized with salted SHA-256 tokens.
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown("<br>", unsafe_allow_html=True)

# ==============================================================================
# SECTION 3: VISUAL DATASET BREAKDOWN
# ==============================================================================

st.markdown("### 📦 Commodity and Auction Coverage")

item_counts = clean_auctions["item"].value_counts().reset_index()
item_counts.columns = ["Item Category", "Auctions Count"]

bids_per_item = clean_bids["item"].value_counts().reset_index()
bids_per_item.columns = ["Item Category", "Bids Count"]

merged_item_stats = pd.merge(item_counts, bids_per_item, on="Item Category")

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    fig_items = px.bar(
        merged_item_stats,
        x="Item Category",
        y="Auctions Count",
        text="Auctions Count",
        title="Unique Auctions by Product Category (N = 628)",
        color="Item Category",
        color_discrete_sequence=[NEU_PALETTE[0], NEU_PALETTE[1], NEU_PALETTE[2]]
    )
    fig_items.update_traces(textposition="outside")
    fig_items.update_layout(showlegend=False)
    fig_items = apply_plotly_theme(fig_items)
    st.plotly_chart(fig_items, use_container_width=True)

with chart_col2:
    fig_bids = px.bar(
        merged_item_stats,
        x="Item Category",
        y="Bids Count",
        text="Bids Count",
        title="Submitted Historical Bids by Product Category (N = 10,681)",
        color="Item Category",
        color_discrete_sequence=[NEU_PALETTE[0], NEU_PALETTE[1], NEU_PALETTE[2]]
    )
    fig_bids.update_traces(textposition="outside")
    fig_bids.update_layout(showlegend=False)
    fig_bids = apply_plotly_theme(fig_bids)
    st.plotly_chart(fig_bids, use_container_width=True)

# ==============================================================================
# SECTION 4: PLATFORM NAVIGATION GUIDE
# ==============================================================================

st.markdown("### 🧭 Platform Navigation")

nav1, nav2, nav3, nav4, nav5 = st.columns(5)

with nav1:
    st.markdown(
        """
        <div class="metric-card" style="padding: 1.2rem; min-height: 140px;">
            <div class="metric-label">Page 1</div>
            <strong style="color: #3D4852; font-size: 1.05rem;">Data Explorer</strong>
            <p style="font-size: 0.8rem; color: #6B7280; margin-top: 0.4rem;">
                Filter raw bid sequences and inspect pseudonymized records.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

with nav2:
    st.markdown(
        """
        <div class="metric-card" style="padding: 1.2rem; min-height: 140px;">
            <div class="metric-label">Page 2</div>
            <strong style="color: #3D4852; font-size: 1.05rem;">Historical Analysis</strong>
            <p style="font-size: 0.8rem; color: #6B7280; margin-top: 0.4rem;">
                Sniping timing density, OLS regressions, and price variance.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

with nav3:
    st.markdown(
        """
        <div class="metric-card" style="padding: 1.2rem; min-height: 140px;">
            <div class="metric-label">Page 3</div>
            <strong style="color: #3D4852; font-size: 1.05rem;">Auction Lab</strong>
            <p style="font-size: 0.8rem; color: #6B7280; margin-top: 0.4rem;">
                First-Price vs. Second-Price counterfactual replays.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

with nav4:
    st.markdown(
        """
        <div class="metric-card" style="padding: 1.2rem; min-height: 140px;">
            <div class="metric-label">Page 4</div>
            <strong style="color: #3D4852; font-size: 1.05rem;">Game Theory</strong>
            <p style="font-size: 0.8rem; color: #6B7280; margin-top: 0.4rem;">
                Mathematical BNE models, dominance proofs, and RL limits.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

with nav5:
    st.markdown(
        """
        <div class="metric-card" style="padding: 1.2rem; min-height: 140px;">
            <div class="metric-label">Page 5</div>
            <strong style="color: #3D4852; font-size: 1.05rem;">Data Quality</strong>
            <p style="font-size: 0.8rem; color: #6B7280; margin-top: 0.4rem;">
                SHA-256 hashes, provenance audit, and data dictionary.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown("---")
st.caption("StrategicBid Platform • Built with Python, pandas, Plotly & Streamlit • Real Historical Data Only")
