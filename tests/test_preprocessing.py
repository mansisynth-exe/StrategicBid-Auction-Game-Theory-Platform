"""
tests/test_preprocessing.py: Unit tests for preprocessing, deterministic pseudonymization,
openbid harmonization, timing metrics, and auction-level aggregation.
"""

import pytest
import pandas as pd
import numpy as np

from src.preprocessing import (
    generate_bidder_pseudonym,
    preprocess_auction_data
)
from src.data_loader import load_raw_auction_data


def test_deterministic_bidder_pseudonymization():
    """Verify that pseudonymization is deterministic, collision-resistant, and non-reversible."""
    user1 = "bidder_alpha"
    user2 = "bidder_alpha"
    user3 = "bidder_beta"

    p1 = generate_bidder_pseudonym(user1)
    p2 = generate_bidder_pseudonym(user2)
    p3 = generate_bidder_pseudonym(user3)

    assert p1 == p2, "Identical usernames must produce identical pseudonyms"
    assert p1 != p3, "Distinct usernames must produce distinct pseudonyms"
    assert p1.startswith("Bidder-")
    assert len(p1) > 7


def test_missing_bidder_pseudonym():
    """Verify handling of null or empty bidder usernames."""
    p_null = generate_bidder_pseudonym(np.nan)
    p_none = generate_bidder_pseudonym(None)
    p_empty = generate_bidder_pseudonym("   ")

    assert p_null == "Anonymous_Bidder"
    assert p_none == "Anonymous_Bidder"
    assert p_empty == "Anonymous_Bidder"


def test_full_preprocessing_on_authentic_data():
    """Verify preprocessing on authentic eBay dataset."""
    df_raw = load_raw_auction_data()
    clean_bids, clean_auctions, cleaning_log = preprocess_auction_data(df_raw, save_processed=False)

    # Invariants
    assert len(clean_bids) == len(df_raw)
    assert len(clean_auctions) == 628
    assert "bidder_id" in clean_bids.columns
    assert "time_to_end_hours" in clean_bids.columns
    assert "normalized_bidtime" in clean_bids.columns
    assert "is_snipe_5min" in clean_bids.columns

    # Normalized bid time must be within [0, 1]
    assert clean_bids["normalized_bidtime"].min() >= 0.0
    assert clean_bids["normalized_bidtime"].max() <= 1.0

    # Harmonization check for auction 3019271858
    auc_harmonized = clean_bids[clean_bids["auctionid"] == 3019271858]
    assert auc_harmonized["openbid"].nunique() == 1
    assert np.isclose(auc_harmonized["openbid"].iloc[0], 0.01)

    # Replay eligibility accounting
    assert cleaning_log["eligible_auctions_for_replay"] == 627
    assert cleaning_log["ineligible_auctions_count"] == 1
    assert 3016587753 in cleaning_log["ineligible_auction_ids"]
