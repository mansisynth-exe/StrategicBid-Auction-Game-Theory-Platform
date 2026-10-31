"""
counterfactual_replay.py: Counterfactual Mechanism Replay on Authentic Historical Bids.
Executes First-Price and Second-Price payment rules on genuine historical bid sequences.
Maintains clear demarcation between historical observations and counterfactual re-simulations.
"""

from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np

from src.auctions import (
    BidSubmission,
    AuctionResult,
    resolve_first_price_auction,
    resolve_second_price_auction
)

COUNTERFACTUAL_DISCLAIMER = (
    "Counterfactual replay of historical bid records — not an observed outcome under this auction mechanism."
)


@dataclass
class ReplayComparison:
    """Detailed comparison between historical observation and counterfactual replays."""
    auctionid: int
    item: str
    auction_type: str
    duration_days: float
    openbid: float
    observed_closing_price: float
    total_bids_submitted: int
    unique_bidders_count: int
    
    # First-Price Replay
    fp_winner_id: Optional[str]
    fp_payment: float
    fp_winning_bid: float
    
    # Second-Price Replay
    sp_winner_id: Optional[str]
    sp_payment: float
    sp_second_bid: float
    
    # Comparative Metrics
    payment_difference_fp_minus_sp: float
    payment_difference_fp_minus_obs: float
    payment_difference_sp_minus_obs: float
    same_winner: bool
    is_tied: bool
    is_eligible: bool
    ineligibility_reason: str
    disclaimer: str = COUNTERFACTUAL_DISCLAIMER

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def replay_single_auction(
    auction_bids_df: pd.DataFrame,
    auction_meta: Optional[pd.Series] = None,
    tie_break_seed: Optional[int] = None
) -> ReplayComparison:
    """
    Executes counterfactual mechanism replay for a single auction's bid records.
    Input DataFrame must contain bids for one auction.
    """
    if auction_bids_df.empty:
        raise ValueError("Cannot replay empty bids DataFrame")

    aid = int(auction_bids_df["auctionid"].iloc[0])
    item = str(auction_bids_df["item"].iloc[0])
    atype = str(auction_bids_df["auction_type"].iloc[0])
    openbid = float(auction_bids_df["openbid"].iloc[0])
    obs_price = float(auction_bids_df["price"].iloc[0])
    duration = float(auction_bids_df["duration_days"].iloc[0]) if "duration_days" in auction_bids_df.columns else 7.0

    # Convert to BidSubmission objects
    # Note: Use bidder_id (pseudonym) or bidder (raw username mapped safely)
    bidder_col = "bidder_id" if "bidder_id" in auction_bids_df.columns else "bidder"
    
    submissions = [
        BidSubmission(
            bidder_id=str(row[bidder_col]),
            bid_amount=float(row["bid"]),
            bid_time=float(row["bidtime"])
        )
        for _, row in auction_bids_df.iterrows()
    ]

    max_submitted = max(s.bid_amount for s in submissions)
    unique_bidders = len(set(s.bidder_id for s in submissions))

    # Check eligibility
    is_eligible = True
    ineligibility_reason = ""

    if obs_price > max_submitted + 1e-4:
        is_eligible = False
        ineligibility_reason = f"Price (${obs_price:.2f}) exceeds max submitted bid (${max_submitted:.2f}) - truncated bid crawl."
    elif max_submitted < openbid - 1e-4:
        is_eligible = False
        ineligibility_reason = "All submitted bids are below the opening bid."

    if not is_eligible:
        return ReplayComparison(
            auctionid=aid,
            item=item,
            auction_type=atype,
            duration_days=duration,
            openbid=openbid,
            observed_closing_price=obs_price,
            total_bids_submitted=len(submissions),
            unique_bidders_count=unique_bidders,
            fp_winner_id=None,
            fp_payment=0.0,
            fp_winning_bid=0.0,
            sp_winner_id=None,
            sp_payment=0.0,
            sp_second_bid=0.0,
            payment_difference_fp_minus_sp=0.0,
            payment_difference_fp_minus_obs=0.0,
            payment_difference_sp_minus_obs=0.0,
            same_winner=False,
            is_tied=False,
            is_eligible=False,
            ineligibility_reason=ineligibility_reason
        )

    # Execute Replays
    fp_res = resolve_first_price_auction(submissions, openbid=openbid, tie_break_seed=tie_break_seed)
    sp_res = resolve_second_price_auction(submissions, openbid=openbid, tie_break_seed=tie_break_seed)

    same_winner = (fp_res.winner_id == sp_res.winner_id) and (fp_res.winner_id is not None)
    is_tied = fp_res.is_tied or sp_res.is_tied

    diff_fp_sp = fp_res.payment - sp_res.payment
    diff_fp_obs = fp_res.payment - obs_price
    diff_sp_obs = sp_res.payment - obs_price

    return ReplayComparison(
        auctionid=aid,
        item=item,
        auction_type=atype,
        duration_days=duration,
        openbid=openbid,
        observed_closing_price=obs_price,
        total_bids_submitted=len(submissions),
        unique_bidders_count=unique_bidders,
        fp_winner_id=fp_res.winner_id,
        fp_payment=fp_res.payment,
        fp_winning_bid=fp_res.winning_bid,
        sp_winner_id=sp_res.winner_id,
        sp_payment=sp_res.payment,
        sp_second_bid=sp_res.second_bid,
        payment_difference_fp_minus_sp=diff_fp_sp,
        payment_difference_fp_minus_obs=diff_fp_obs,
        payment_difference_sp_minus_obs=diff_sp_obs,
        same_winner=same_winner,
        is_tied=is_tied,
        is_eligible=True,
        ineligibility_reason=""
    )


def replay_all_auctions(
    bids_df: pd.DataFrame,
    tie_break_seed: Optional[int] = None
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Executes counterfactual replay on all auctions in the dataset.
    Returns:
        replay_df: DataFrame of auction-level replay results.
        summary_stats: High-level aggregate metrics across eligible auctions.
    """
    results = []
    grouped = bids_df.groupby("auctionid", sort=False)

    for _, g in grouped:
        comp = replay_single_auction(g, tie_break_seed=tie_break_seed)
        results.append(comp.to_dict())

    replay_df = pd.DataFrame(results)
    eligible = replay_df[replay_df["is_eligible"]]

    summary_stats = {
        "total_auctions": len(replay_df),
        "eligible_auctions": len(eligible),
        "ineligible_auctions": len(replay_df) - len(eligible),
        "total_observed_revenue": float(eligible["observed_closing_price"].sum()),
        "total_fp_counterfactual_revenue": float(eligible["fp_payment"].sum()),
        "total_sp_counterfactual_revenue": float(eligible["sp_payment"].sum()),
        "mean_fp_payment": float(eligible["fp_payment"].mean()) if not eligible.empty else 0.0,
        "mean_sp_payment": float(eligible["sp_payment"].mean()) if not eligible.empty else 0.0,
        "mean_observed_price": float(eligible["observed_closing_price"].mean()) if not eligible.empty else 0.0,
        "median_observed_price": float(eligible["observed_closing_price"].median()) if not eligible.empty else 0.0,
        "mean_payment_difference_fp_minus_sp": float(eligible["payment_difference_fp_minus_sp"].mean()) if not eligible.empty else 0.0,
        "median_payment_difference_fp_minus_sp": float(eligible["payment_difference_fp_minus_sp"].median()) if not eligible.empty else 0.0,
        "auctions_with_same_winner": int(eligible["same_winner"].sum()),
        "auctions_with_ties": int(eligible["is_tied"].sum()),
        "disclaimer": COUNTERFACTUAL_DISCLAIMER
    }

    return replay_df, summary_stats
