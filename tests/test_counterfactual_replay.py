"""
tests/test_counterfactual_replay.py: Unit and integration tests for counterfactual mechanism replays.
Verifies separation of historical and counterfactual quantities, eligibility filters,
and reproducibility on genuine eBay bid records.
"""

import pytest
import pandas as pd
import numpy as np

from src.counterfactual_replay import (
    replay_single_auction,
    replay_all_auctions,
    COUNTERFACTUAL_DISCLAIMER
)
from src.data_loader import load_raw_auction_data
from src.preprocessing import preprocess_auction_data


def test_insufficient_information_auction_ineligibility():
    """Case 11: Auctions with insufficient information must be flagged ineligible with reasons."""
    # Fixture: Auction where closing price exceeds submitted bids (like real auction 3016587753)
    fixture_bids = pd.DataFrame({
        "auctionid": [3016587753],
        "bid": [5.0],
        "bidtime": [0.077],
        "bidder_id": ["Bidder-A"],
        "bidderrate": [1.0],
        "openbid": [0.01],
        "price": [255.0],  # Price is 255 but max bid is 5
        "item": ["Palm Pilot M515 PDA"],
        "auction_type": ["7 day auction"],
        "duration_days": [7.0]
    })

    comp = replay_single_auction(fixture_bids)
    assert comp.is_eligible is False
    assert "truncated" in comp.ineligibility_reason.lower() or "exceeds" in comp.ineligibility_reason.lower()
    assert comp.fp_winner_id is None
    assert comp.sp_winner_id is None


def test_separation_of_observed_and_counterfactual_payments():
    """Case 12: Observed closing price and counterfactual replay payments must never overwrite each other."""
    fixture_bids = pd.DataFrame({
        "auctionid": [9999, 9999, 9999],
        "bid": [100.0, 150.0, 180.0],
        "bidtime": [1.0, 2.0, 3.0],
        "bidder_id": ["Bidder-1", "Bidder-2", "Bidder-3"],
        "bidderrate": [1.0, 2.0, 3.0],
        "openbid": [10.0, 10.0, 10.0],
        "price": [160.0, 160.0, 160.0],  # Historical observed price
        "item": ["Xbox game console", "Xbox game console", "Xbox game console"],
        "auction_type": ["3 day auction", "3 day auction", "3 day auction"],
        "duration_days": [3.0, 3.0, 3.0]
    })

    comp = replay_single_auction(fixture_bids)
    assert comp.is_eligible is True
    assert np.isclose(comp.observed_closing_price, 160.0)  # Historical
    assert np.isclose(comp.fp_payment, 180.0)              # Counterfactual FP
    assert np.isclose(comp.sp_payment, 150.0)              # Counterfactual SP

    # Verify they are strictly distinct numbers
    assert comp.fp_payment != comp.observed_closing_price
    assert comp.sp_payment != comp.observed_closing_price
    assert comp.fp_payment > comp.sp_payment


def test_batch_replay_on_authentic_data():
    """Case 13 & 14: Reproducible batch replay on authentic dataset with exact exclusion accounting."""
    df_raw = load_raw_auction_data()
    clean_bids, clean_auctions, cleaning_log = preprocess_auction_data(df_raw, save_processed=False)

    replay_df1, summary1 = replay_all_auctions(clean_bids, tie_break_seed=123)
    replay_df2, summary2 = replay_all_auctions(clean_bids, tie_break_seed=123)

    # Deterministic reproducibility
    assert summary1 == summary2
    pd.testing.assert_frame_equal(replay_df1, replay_df2)

    # Exclusion accounting (Case 13)
    assert summary1["total_auctions"] == 628
    assert summary1["eligible_auctions"] == 627
    assert summary1["ineligible_auctions"] == 1

    # Economic validity on real bids: First-Price payment >= Second-Price payment
    eligible = replay_df1[replay_df1["is_eligible"]]
    assert (eligible["fp_payment"] >= eligible["sp_payment"] - 1e-5).all()

    # Replay disclaimer presence
    assert summary1["disclaimer"] == COUNTERFACTUAL_DISCLAIMER
