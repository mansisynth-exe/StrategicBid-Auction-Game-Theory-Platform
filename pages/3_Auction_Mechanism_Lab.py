"""
pages/3_Auction_Mechanism_Lab.py: Interactive Counterfactual Mechanism Replay Lab.
Simulates First-Price and Second-Price payment rules on genuine historical bid sequences.
Strictly demarcates theoretical counterfactual replays from observed historical outcomes.
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
    render_counterfactual_disclaimer,
    get_cached_datasets,
    apply_plotly_theme,
    NEU_PALETTE
)
from src.counterfactual_replay import replay_single_auction, replay_all_auctions
from src.metrics import format_currency, format_integer, format_percentage

st.set_page_config(
    page_title="Auction Mechanism Lab | StrategicBid",
    page_icon="⚖️",
    layout="wide"
)

apply_theme()
render_sidebar_metadata()

render_page_header(
    title="Auction Mechanism Lab: Counterfactual Replay",
    subtitle="Simulate and compare First-Price and Second-Price payment rules using actual submitted historical bids.",
    tag="Component B • Counterfactual Mechanism Replay"
)

render_counterfactual_disclaimer()

clean_bids, clean_auctions, cleaning_log = get_cached_datasets()

# Run or retrieve all replays
@st.cache_data
def get_all_replays(bids_data):
    return replay_all_auctions(bids_data)

replay_df, replay_summary = get_all_replays(clean_bids)

# ==============================================================================
# SECTION 1: AGGREGATE REPLAY SUMMARY (N = 627 Eligible Auctions)
# ==============================================================================

st.markdown("### 📊 Macro Mechanism Comparison (All 627 Eligible Auctions)")
st.caption("Aggregate payment and revenue comparisons holding actual observed bids constant.")

agg1, agg2, agg3, agg4, agg5 = st.columns(5)

with agg1:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Observed Revenue</div>
            <div class="metric-value">{format_currency(replay_summary['total_observed_revenue'])}</div>
            <div class="metric-sub">Mean: {format_currency(replay_summary['mean_observed_price'])}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with agg2:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">First-Price Replay</div>
            <div class="metric-value" style="color: #6C63FF;">{format_currency(replay_summary['total_fp_counterfactual_revenue'])}</div>
            <div class="metric-sub">Mean: {format_currency(replay_summary['mean_fp_payment'])}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with agg3:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Second-Price Replay</div>
            <div class="metric-value" style="color: #38B2AC;">{format_currency(replay_summary['total_sp_counterfactual_revenue'])}</div>
            <div class="metric-sub">Mean: {format_currency(replay_summary['mean_sp_payment'])}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with agg4:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Mean Payment Diff</div>
            <div class="metric-value" style="color: #F59E0B;">+{format_currency(replay_summary['mean_payment_difference_fp_minus_sp'])}</div>
            <div class="metric-sub">Median: +{format_currency(replay_summary['median_payment_difference_fp_minus_sp'])}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with agg5:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Winner Alignment</div>
            <div class="metric-value">100.0%</div>
            <div class="metric-sub">{replay_summary['auctions_with_same_winner']}/{replay_summary['eligible_auctions']} auctions</div>
        </div>
        """,
        unsafe_allow_html=True
    )

chart_r1, chart_r2 = st.columns(2)

with chart_r1:
    eligible_replays = replay_df[replay_df["is_eligible"]]
    fig_diff = px.histogram(
        eligible_replays,
        x="payment_difference_fp_minus_sp",
        nbins=40,
        title="Distribution of Payment Differences (FP Replay - SP Replay) [N = 627]",
        labels={"payment_difference_fp_minus_sp": "Payment Differential ($)"},
        color_discrete_sequence=[NEU_PALETTE[0]]
    )
    fig_diff.update_layout(yaxis_title="Count of Auctions")
    fig_diff = apply_plotly_theme(fig_diff)
    st.plotly_chart(fig_diff, use_container_width=True)

with chart_r2:
    cat_comp = eligible_replays.groupby("item")[["observed_closing_price", "fp_payment", "sp_payment"]].mean().reset_index()
    cat_comp_melted = pd.melt(
        cat_comp,
        id_vars=["item"],
        value_vars=["observed_closing_price", "fp_payment", "sp_payment"],
        var_name="Mechanism",
        value_name="Mean Payment ($)"
    )
    cat_comp_melted["Mechanism"] = cat_comp_melted["Mechanism"].map({
        "observed_closing_price": "Historical Observed",
        "fp_payment": "First-Price Replay",
        "sp_payment": "Second-Price Replay"
    })
    fig_bars = px.bar(
        cat_comp_melted,
        x="item",
        y="Mean Payment ($)",
        color="Mechanism",
        barmode="group",
        title="Mean Payment by Commodity across Mechanisms [N = 627]",
        color_discrete_sequence=["#6B7280", NEU_PALETTE[0], NEU_PALETTE[1]]
    )
    fig_bars = apply_plotly_theme(fig_bars)
    st.plotly_chart(fig_bars, use_container_width=True)

st.markdown("---")

# ==============================================================================
# SECTION 2: INTERACTIVE SINGLE AUCTION LAB
# ==============================================================================

st.markdown("### 🔍 Single Auction Replay Simulator")
st.caption("Select an eligible historical auction to inspect input bids and counterfactual payments step-by-step.")

sim_col1, sim_col2 = st.columns([1, 2])

with sim_col1:
    selected_item = st.selectbox("Filter Commodity:", ["All"] + sorted(eligible_replays["item"].unique().tolist()))
    
    sub_eligible = eligible_replays if selected_item == "All" else eligible_replays[eligible_replays["item"] == selected_item]
    
    selected_aid = st.selectbox(
        "Select Auction ID:",
        sub_eligible["auctionid"].tolist()
    )

selected_replay = eligible_replays[eligible_replays["auctionid"] == selected_aid].iloc[0]
selected_bids = clean_bids[clean_bids["auctionid"] == selected_aid].sort_values("bidtime")

with sim_col2:
    st.markdown(
        f"""
        <div class="info-box" style="margin-top: 0; padding: 1.2rem 1.6rem;">
            <div style="display: flex; flex-wrap: wrap; justify-content: space-between; gap: 0.8rem;">
                <div>
                    <span style="font-size: 0.78rem; text-transform: uppercase; font-weight: 700; color: #6B7280;">Item Category</span><br>
                    <strong style="color: #3D4852; font-size: 1.15rem; font-family: 'Plus Jakarta Sans', sans-serif;">{selected_replay['item']}</strong>
                </div>
                <div>
                    <span style="font-size: 0.78rem; text-transform: uppercase; font-weight: 700; color: #6B7280;">Duration</span><br>
                    <strong style="color: #3D4852; font-size: 1.15rem; font-family: 'Plus Jakarta Sans', sans-serif;">{selected_replay['auction_type']}</strong>
                </div>
                <div>
                    <span style="font-size: 0.78rem; text-transform: uppercase; font-weight: 700; color: #6B7280;">Opening Bid</span><br>
                    <strong style="color: #6C63FF; font-size: 1.15rem; font-family: 'Plus Jakarta Sans', sans-serif;">{format_currency(selected_replay['openbid'])}</strong>
                </div>
                <div>
                    <span style="font-size: 0.78rem; text-transform: uppercase; font-weight: 700; color: #6B7280;">Bids Submitted</span><br>
                    <strong style="color: #3D4852; font-size: 1.15rem; font-family: 'Plus Jakarta Sans', sans-serif;">{selected_replay['total_bids_submitted']}</strong>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown("#### Outcome Comparison Matrix")

mat1, mat2, mat3, mat4 = st.columns(4)

with mat1:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Historical Observed</div>
            <div class="metric-value">{format_currency(selected_replay['observed_closing_price'])}</div>
            <div class="metric-sub">Closing price on eBay</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with mat2:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">First-Price Replay</div>
            <div class="metric-value" style="color: #6C63FF;">{format_currency(selected_replay['fp_payment'])}</div>
            <div class="metric-sub">Winner: <code>{selected_replay['fp_winner_id']}</code></div>
        </div>
        """,
        unsafe_allow_html=True
    )

with mat3:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Second-Price Replay</div>
            <div class="metric-value" style="color: #38B2AC;">{format_currency(selected_replay['sp_payment'])}</div>
            <div class="metric-sub">Winner: <code>{selected_replay['sp_winner_id']}</code></div>
        </div>
        """,
        unsafe_allow_html=True
    )

with mat4:
    diff_val = selected_replay['payment_difference_fp_minus_sp']
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Payment Differential</div>
            <div class="metric-value" style="color: #F59E0B;">+{format_currency(diff_val)}</div>
            <div class="metric-sub">FP minus SP Replay</div>
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown("#### Input Bid History for Selected Auction")

bid_history_cols = [
    "bidtime",
    "bidder_id",
    "bid",
    "bidderrate",
    "time_to_end_hours",
    "is_snipe_5min"
]

st.dataframe(
    selected_bids[bid_history_cols].rename(columns={
        "bidtime": "Elapsed Days",
        "bidder_id": "Pseudonymized Bidder",
        "bid": "Observed Bid ($)",
        "bidderrate": "Feedback Rating",
        "time_to_end_hours": "Hours to Closing",
        "is_snipe_5min": "Sniping (< 5 min)"
    }).style.format({
        "Observed Bid ($)": "${:,.2f}",
        "Elapsed Days": "{:.4f}",
        "Hours to Closing": "{:.2f}"
    }),
    use_container_width=True
)

st.markdown(
    """
    <div class="info-box">
        <strong>💡 Key Theoretical Takeaway:</strong><br>
        In an ascending proxy auction, the recorded winning bid is mathematically set to the second-highest bid plus an increment.
        Therefore, First-Price counterfactual replay payment represents the highest proxy bid recorded by eBay,
        while Second-Price replay drops the payment to the exact second-highest submitted bid without the platform increment.
        Neither replay reveals the true, unobserved maximum valuation that the winning bidder kept in reserve.
    </div>
    """,
    unsafe_allow_html=True
)
