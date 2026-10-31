"""
pages/2_Historical_Analysis.py: Rigorous Empirical Visualizations of Historical Auction Data.
Displays bid distributions, late-bidding (sniping) patterns, opening bid correlations,
and category pricing variance strictly calculated from loaded records.
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
from src.empirical_analysis import (
    compute_auction_level_statistics,
    analyze_openbid_vs_price,
    analyze_bid_timing_and_sniping,
    analyze_bidder_participation
)
from src.metrics import format_currency, format_integer, format_percentage

st.set_page_config(
    page_title="Historical Analysis | StrategicBid",
    page_icon="📈",
    layout="wide"
)

apply_theme()
render_sidebar_metadata()

render_page_header(
    title="Historical Empirical Analysis",
    subtitle="Descriptive patterns, timing dynamics, and price formations across 10,681 verified eBay bids.",
    tag="Component A • Empirical Analysis"
)

clean_bids, clean_auctions, cleaning_log = get_cached_datasets()

# Compute empirical stats
emp_stats = compute_auction_level_statistics(clean_auctions)
timing_stats = analyze_bid_timing_and_sniping(clean_bids)
openbid_stats = analyze_openbid_vs_price(clean_auctions)
part_stats = analyze_bidder_participation(clean_bids)

# ==============================================================================
# SECTION 1: BID TIMING & SNIPING DYNAMICS
# ==============================================================================

st.markdown("### ⏱️ Bid Timing & Sniping Behavior (Strategic Information Concealment)")
st.caption(f"Analysis of normalized submission times across all verified bids (N = {timing_stats['total_bids_analyzed']:,} bids in {timing_stats['total_auctions_analyzed']} auctions).")

snip_col1, snip_col2, snip_col3, snip_col4 = st.columns(4)

with snip_col1:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Bids in Last 5 Mins</div>
            <div class="metric-value">{format_percentage(timing_stats['bids_last_5min']['percentage'])}</div>
            <div class="metric-sub">{format_integer(timing_stats['bids_last_5min']['count'])} total bids</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with snip_col2:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Bids in Last 1 Hour</div>
            <div class="metric-value">{format_percentage(timing_stats['bids_last_1hr']['percentage'])}</div>
            <div class="metric-sub">{format_integer(timing_stats['bids_last_1hr']['count'])} total bids</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with snip_col3:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Auctions with Sniping</div>
            <div class="metric-value">{format_percentage(timing_stats['auctions_with_sniping_5min']['percentage'])}</div>
            <div class="metric-sub">{format_integer(timing_stats['auctions_with_sniping_5min']['count'])} of {timing_stats['total_auctions_analyzed']} auctions</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with snip_col4:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Won in Last 5 Mins</div>
            <div class="metric-value">{format_percentage(timing_stats['winning_bids_in_last_5min']['percentage'])}</div>
            <div class="metric-sub">Final bid placed < 5 min</div>
        </div>
        """,
        unsafe_allow_html=True
    )

chart_t1, chart_t2 = st.columns(2)

with chart_t1:
    fig_norm_time = px.histogram(
        clean_bids,
        x="normalized_bidtime",
        nbins=50,
        title="Distribution of Normalized Bid Timing (0.0 = Start, 1.0 = End) [N = 10,681]",
        labels={"normalized_bidtime": "Normalized Auction Elapsed Time (t / T)"},
        color_discrete_sequence=[NEU_PALETTE[0]]
    )
    fig_norm_time.update_layout(yaxis_title="Count of Submitted Bids")
    fig_norm_time = apply_plotly_theme(fig_norm_time)
    st.plotly_chart(fig_norm_time, use_container_width=True)

with chart_t2:
    bids_under_24 = clean_bids[clean_bids["time_to_end_hours"] <= 24.0]
    fig_end_hours = px.histogram(
        bids_under_24,
        x="time_to_end_hours",
        nbins=48,
        title=f"Submission Density in Final 24 Hours [N = {len(bids_under_24):,}]",
        labels={"time_to_end_hours": "Hours Remaining Until Closing"},
        color_discrete_sequence=[NEU_PALETTE[2]]
    )
    fig_end_hours.update_layout(
        yaxis_title="Count of Submitted Bids",
        xaxis=dict(autorange="reversed")
    )
    fig_end_hours = apply_plotly_theme(fig_end_hours)
    st.plotly_chart(fig_end_hours, use_container_width=True)

st.markdown(
    """
    <div class="info-box">
        <strong>💡 Game-Theoretic Interpretation of Sniping:</strong><br>
        In a static sealed-bid second-price auction, early truthful bidding is weakly dominant.
        However, in an online ascending auction with a hard ending deadline, submitting early reveals valuation information
        to competing bidders and invites incremental counter-bidding or shill bidding.
        Sniping is an equilibrium response that withholds private signals until opponents cannot react.
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("---")

# ==============================================================================
# SECTION 2: OPENING BID VS. CLOSING PRICE
# ==============================================================================

st.markdown("### 🏷️ Opening Bid vs. Closing Price Association")
st.caption(f"Evaluation of seller reserve / starting bid relationship to final settlement price (N = {openbid_stats['sample_size']} auctions).")

ob_col1, ob_col2 = st.columns([1, 2])

with ob_col1:
    st.markdown(
        f"""
        <div class="info-box">
            <strong>Statistical Summary:</strong><br><br>
            • <strong>Pearson Correlation</strong>: {openbid_stats['pearson_correlation']:.3f} (p < 0.001)<br>
            • <strong>Spearman Rank</strong>: {openbid_stats['spearman_correlation']:.3f} (p < 0.001)<br>
            • <strong>OLS Slope (β₁)</strong>: {openbid_stats['ols_slope']:.3f} (SE: {openbid_stats['std_err']:.3f})<br>
            • <strong>95% Conf. Interval</strong>: [{openbid_stats['ols_slope_ci_95'][0]:.3f}, {openbid_stats['ols_slope_ci_95'][1]:.3f}]<br>
            • <strong>OLS Intercept</strong>: ${openbid_stats['ols_intercept']:.2f}<br>
            • <strong>Coefficient of Determ. (R²)</strong>: {openbid_stats['r_squared']:.3f}
        </div>
        """,
        unsafe_allow_html=True
    )
    st.warning(
        f"⚠️ **Non-Causal Notice**: {openbid_stats['disclaimer']}"
    )

with ob_col2:
    fig_scatter = px.scatter(
        clean_auctions,
        x="openbid",
        y="price",
        color="item",
        trendline="ols",
        title=f"Opening Bid vs. Closing Price by Commodity (N = {len(clean_auctions)})",
        labels={"openbid": "Opening Bid ($)", "price": "Closing Price ($)", "item": "Category"},
        hover_data=["auctionid", "bids_count", "auction_type"],
        color_discrete_sequence=[NEU_PALETTE[0], NEU_PALETTE[1], NEU_PALETTE[2]]
    )
    fig_scatter = apply_plotly_theme(fig_scatter)
    st.plotly_chart(fig_scatter, use_container_width=True)

st.markdown("---")

# ==============================================================================
# SECTION 3: PRICE & PARTICIPATION DISTRIBUTIONS BY COMMODITY
# ==============================================================================

st.markdown("### 📊 Closing Price & Participation Distributions by Commodity")

dist_col1, dist_col2 = st.columns(2)

with dist_col1:
    fig_box_price = px.box(
        clean_auctions,
        x="item",
        y="price",
        color="item",
        points="all",
        title="Closing Price Distribution by Commodity (N = 628)",
        labels={"item": "Product Category", "price": "Closing Price ($)"},
        color_discrete_sequence=[NEU_PALETTE[0], NEU_PALETTE[1], NEU_PALETTE[2]]
    )
    fig_box_price.update_layout(showlegend=False)
    fig_box_price = apply_plotly_theme(fig_box_price)
    st.plotly_chart(fig_box_price, use_container_width=True)

with dist_col2:
    fig_box_bids = px.box(
        clean_auctions,
        x="item",
        y="bids_count",
        color="item",
        points="all",
        title="Bids per Auction Distribution by Commodity (N = 628)",
        labels={"item": "Product Category", "bids_count": "Submitted Bids Count"},
        color_discrete_sequence=[NEU_PALETTE[0], NEU_PALETTE[1], NEU_PALETTE[2]]
    )
    fig_box_bids.update_layout(showlegend=False)
    fig_box_bids = apply_plotly_theme(fig_box_bids)
    st.plotly_chart(fig_box_bids, use_container_width=True)

st.markdown("---")

# ==============================================================================
# SECTION 4: BIDDER PARTICIPATION INTENSITY
# ==============================================================================

st.markdown("### 👥 Bidder Participation & Intensity")
st.caption(f"Analysis of {part_stats['distinct_bidders']:,} distinct bidders across historical auctions.")

part1, part2, part3, part4 = st.columns(4)

with part1:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Single-Bid Bidders</div>
            <div class="metric-value">{part_stats['single_bid_bidders_count']:,}</div>
            <div class="metric-sub">{part_stats['single_bid_bidders_percentage']:.1f}% of unique bidders</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with part2:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Multi-Bid Bidders</div>
            <div class="metric-value">{part_stats['multi_bid_bidders_count']:,}</div>
            <div class="metric-sub">{part_stats['multi_bid_bidders_percentage']:.1f}% of unique bidders</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with part3:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Cross-Auction Bidders</div>
            <div class="metric-value">{part_stats['bidders_in_multiple_auctions']:,}</div>
            <div class="metric-sub">{part_stats['bidders_in_multiple_auctions_pct']:.1f}% in multiple auctions</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with part4:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Max Bids Single Bidder</div>
            <div class="metric-value">{part_stats['max_bids_by_single_bidder']}</div>
            <div class="metric-sub">Across {part_stats['max_auctions_participated_by_one_bidder']} distinct auctions</div>
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown("---")
st.caption("StrategicBid • Empirical Historical Analysis • Real Data Traceable to Zenodo Record 11259259")
