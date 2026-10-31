"""
pages/1_Data_Explorer.py: Interactive exploration of authentic auction records and bids.
Provides multidimensional filtering, bid sequence inspection, and privacy-safe CSV export.
"""

import streamlit as st
import pandas as pd
import numpy as np

from src.ui_helpers import apply_theme, render_page_header, render_sidebar_metadata, get_cached_datasets
from src.metrics import format_currency, format_integer

st.set_page_config(
    page_title="Data Explorer | StrategicBid",
    page_icon="🔍",
    layout="wide"
)

apply_theme()
render_sidebar_metadata()

render_page_header(
    title="Data Explorer: Historical Bid & Auction Records",
    subtitle="Query, filter, and inspect authentic micro-level bid sequences with privacy-safe bidder pseudonyms.",
    tag="Component A • Empirical Exploration"
)

clean_bids, clean_auctions, cleaning_log = get_cached_datasets()

# ==============================================================================
# SECTION 1: INTERACTIVE FILTERS
# ==============================================================================

st.markdown("### 🎛️ Filter Options")

filter_col1, filter_col2, filter_col3 = st.columns(3)

with filter_col1:
    available_items = ["All Categories"] + sorted(clean_auctions["item"].unique().tolist())
    selected_item = st.selectbox("Product Category", available_items)

with filter_col2:
    available_types = ["All Durations"] + sorted(clean_auctions["auction_type"].unique().tolist())
    selected_type = st.selectbox("Auction Duration Format", available_types)

with filter_col3:
    replay_filter = st.selectbox(
        "Replay Eligibility",
        ["All Auctions", "Eligible for Replay Only", "Ineligible Only"]
    )

# Apply filters to clean_auctions
filtered_auctions = clean_auctions.copy()

if selected_item != "All Categories":
    filtered_auctions = filtered_auctions[filtered_auctions["item"] == selected_item]

if selected_type != "All Durations":
    filtered_auctions = filtered_auctions[filtered_auctions["auction_type"] == selected_type]

if replay_filter == "Eligible for Replay Only":
    filtered_auctions = filtered_auctions[filtered_auctions["is_eligible_replay"]]
elif replay_filter == "Ineligible Only":
    filtered_auctions = filtered_auctions[~filtered_auctions["is_eligible_replay"]]

filtered_auction_ids = set(filtered_auctions["auctionid"].unique())
filtered_bids = clean_bids[clean_bids["auctionid"].isin(filtered_auction_ids)].copy()

# Summary KPI banner for filtered subset
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Filtered Auctions</div>
            <div class="metric-value">{format_integer(len(filtered_auctions))}</div>
            <div class="metric-sub">Out of {len(clean_auctions)} total</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with kpi2:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Filtered Bids</div>
            <div class="metric-value">{format_integer(len(filtered_bids))}</div>
            <div class="metric-sub">Out of {len(clean_bids)} total</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with kpi3:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Median Closing Price</div>
            <div class="metric-value">{format_currency(filtered_auctions['price'].median())}</div>
            <div class="metric-sub">Mean: {format_currency(filtered_auctions['price'].mean())}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with kpi4:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Distinct Bidders</div>
            <div class="metric-value">{format_integer(filtered_bids['bidder_id'].nunique())}</div>
            <div class="metric-sub">In selected subset</div>
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown("---")

# ==============================================================================
# SECTION 2: AUCTION-LEVEL TABLE VIEW
# ==============================================================================

st.markdown("### 📋 Auction-Level Summaries (Unit of Analysis)")
st.caption("Each row represents one unique auction ($N = 628$). Prices and openbids are aggregated at the auction level.")

display_auction_cols = [
    "auctionid",
    "item",
    "auction_type",
    "openbid",
    "price",
    "bids_count",
    "unique_bidders",
    "max_bid",
    "second_highest_bid",
    "has_sniping",
    "is_eligible_replay"
]

st.dataframe(
    filtered_auctions[display_auction_cols].style.format({
        "openbid": "${:,.2f}",
        "price": "${:,.2f}",
        "max_bid": "${:,.2f}",
        "second_highest_bid": "${:,.2f}"
    }),
    use_container_width=True,
    height=320
)

# ==============================================================================
# SECTION 3: DEEP-DIVE INTO A SINGLE AUCTION BID SEQUENCE
# ==============================================================================

st.markdown("### 🔬 Inspect Micro-Level Bid Sequence for a Specific Auction")

selected_aid = st.selectbox(
    "Choose an Auction ID to inspect all submitted bids:",
    filtered_auctions["auctionid"].tolist() if not filtered_auctions.empty else []
)

if selected_aid:
    single_auc_meta = clean_auctions[clean_auctions["auctionid"] == selected_aid].iloc[0]
    single_bids = clean_bids[clean_bids["auctionid"] == selected_aid].sort_values("bidtime")

    st.markdown(
        f"""
        <div class="metric-card" style="padding: 1.4rem 1.6rem; margin-bottom: 1.2rem;">
            <div style="display: flex; flex-wrap: wrap; justify-content: space-between; gap: 1rem;">
                <div>
                    <span style="font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: #6B7280;">Item Category</span><br>
                    <strong style="color: #3D4852; font-size: 1.15rem; font-family: 'Plus Jakarta Sans', sans-serif;">{single_auc_meta['item']}</strong>
                </div>
                <div>
                    <span style="font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: #6B7280;">Duration</span><br>
                    <strong style="color: #3D4852; font-size: 1.15rem; font-family: 'Plus Jakarta Sans', sans-serif;">{single_auc_meta['auction_type']}</strong>
                </div>
                <div>
                    <span style="font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: #6B7280;">Opening Bid</span><br>
                    <strong style="color: #6C63FF; font-size: 1.15rem; font-family: 'Plus Jakarta Sans', sans-serif;">{format_currency(single_auc_meta['openbid'])}</strong>
                </div>
                <div>
                    <span style="font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: #6B7280;">Closing Price</span><br>
                    <strong style="color: #38B2AC; font-size: 1.15rem; font-family: 'Plus Jakarta Sans', sans-serif;">{format_currency(single_auc_meta['price'])}</strong>
                </div>
                <div>
                    <span style="font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: #6B7280;">Bids (Unique)</span><br>
                    <strong style="color: #3D4852; font-size: 1.15rem; font-family: 'Plus Jakarta Sans', sans-serif;">{len(single_bids)} ({single_auc_meta['unique_bidders']} bidders)</strong>
                </div>
                <div>
                    <span style="font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: #6B7280;">Replay Eligible</span><br>
                    <strong style="color: {'#38B2AC' if single_auc_meta['is_eligible_replay'] else '#F43F5E'}; font-size: 1.15rem; font-family: 'Plus Jakarta Sans', sans-serif;">
                        {'Eligible' if single_auc_meta['is_eligible_replay'] else 'Ineligible'}
                    </strong>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("#### Chronological Bid Stream")
    st.caption("Bidder usernames are deterministically pseudonymized with salted SHA-256 tokens to preserve privacy.")

    display_bid_cols = [
        "bidtime",
        "bidder_id",
        "bid",
        "bidderrate",
        "time_to_end_hours",
        "is_snipe_5min"
    ]

    st.dataframe(
        single_bids[display_bid_cols].rename(columns={
            "bidtime": "Elapsed Days",
            "bidder_id": "Pseudonymized Bidder",
            "bid": "Submitted Bid ($)",
            "bidderrate": "Feedback Rating",
            "time_to_end_hours": "Hours to End",
            "is_snipe_5min": "Sniping (< 5 min)"
        }).style.format({
            "Submitted Bid ($)": "${:,.2f}",
            "Elapsed Days": "{:.4f}",
            "Hours to End": "{:.2f}"
        }),
        use_container_width=True
    )

st.markdown("---")

# ==============================================================================
# SECTION 4: PRIVACY-SAFE CSV EXPORT
# ==============================================================================

st.markdown("### 💾 Export Filtered Analytical Dataset")
st.caption("Export contains pseudonymized bidder identifiers and auction-level features. No personal identifiable information is released.")

exp_col1, exp_col2 = st.columns(2)

with exp_col1:
    csv_auctions = filtered_auctions.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download Filtered Auctions (CSV)",
        data=csv_auctions,
        file_name="strategicbid_filtered_auctions.csv",
        mime="text/csv"
    )

with exp_col2:
    # Remove raw username column if present, keep pseudonym only
    export_bids = filtered_bids.drop(columns=["bidder"], errors="ignore")
    csv_bids = export_bids.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download Filtered Bids with Pseudonyms (CSV)",
        data=csv_bids,
        file_name="strategicbid_filtered_bids.csv",
        mime="text/csv"
    )
