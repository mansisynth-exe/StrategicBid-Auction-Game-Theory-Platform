"""
tests/test_auctions.py: Unit tests for game-theoretic auction models,
first-price and second-price settlement rules, single-bidder handling,
and deterministic/seeded tie-breaking.
"""

import pytest
import numpy as np

from src.auctions import (
    BidSubmission,
    resolve_first_price_auction,
    resolve_second_price_auction,
    first_price_equilibrium_bid,
    calculate_shading_factor,
    first_price_expected_revenue,
    second_price_dominant_bid,
    calculate_bidder_utility
)


def test_first_price_equilibrium_formula():
    """Verify FPSB theoretical equilibrium benchmark calculation."""
    # Under n=2: b*(v) = 0.5 * v
    assert np.isclose(first_price_equilibrium_bid(100.0, 2), 50.0)
    # Under n=5: b*(v) = 0.8 * v
    assert np.isclose(first_price_equilibrium_bid(100.0, 5), 80.0)
    # Under n=10: b*(v) = 0.9 * v
    assert np.isclose(first_price_equilibrium_bid(100.0, 10), 90.0)

    # Shading factor
    assert np.isclose(calculate_shading_factor(2), 0.5)
    assert np.isclose(calculate_shading_factor(4), 0.75)

    # Expected revenue
    assert np.isclose(first_price_expected_revenue(3, 100.0), 50.0)  # (2/4)*100 = 50

    with pytest.raises(ValueError):
        first_price_equilibrium_bid(-10.0, 3)
    with pytest.raises(ValueError):
        first_price_equilibrium_bid(100.0, 0)


def test_first_price_payment_calculation():
    """Case 7: Correct first-price payment calculation (winner pays submitted bid)."""
    bids = [
        BidSubmission("Bidder-A", 150.0, 1.0),
        BidSubmission("Bidder-B", 200.0, 1.5),
        BidSubmission("Bidder-C", 180.0, 2.0)
    ]
    res = resolve_first_price_auction(bids, openbid=10.0)
    assert res.winner_id == "Bidder-B"
    assert np.isclose(res.winning_bid, 200.0)
    assert np.isclose(res.payment, 200.0)
    assert np.isclose(res.second_bid, 180.0)
    assert res.is_tied is False


def test_second_price_payment_calculation():
    """Case 8: Correct second-price payment calculation (winner pays second-highest competing bid)."""
    bids = [
        BidSubmission("Bidder-A", 150.0, 1.0),
        BidSubmission("Bidder-B", 200.0, 1.5),
        BidSubmission("Bidder-C", 180.0, 2.0)
    ]
    res = resolve_second_price_auction(bids, openbid=10.0)
    assert res.winner_id == "Bidder-B"
    assert np.isclose(res.winning_bid, 200.0)
    assert np.isclose(res.payment, 180.0)  # Second-highest bid
    assert np.isclose(res.second_bid, 180.0)
    assert res.is_tied is False


def test_single_eligible_bidder_handling():
    """Case 9: Auctions with only one eligible bidder."""
    bids = [
        BidSubmission("Bidder-Sole", 100.0, 1.0)
    ]
    # First-price: pays 100.0
    res_fp = resolve_first_price_auction(bids, openbid=25.0)
    assert res_fp.winner_id == "Bidder-Sole"
    assert np.isclose(res_fp.payment, 100.0)

    # Second-price: pays openbid/reserve (25.0)
    res_sp = resolve_second_price_auction(bids, openbid=25.0)
    assert res_sp.winner_id == "Bidder-Sole"
    assert np.isclose(res_sp.payment, 25.0)


def test_tied_highest_bids():
    """Case 10: Tied highest bids with deterministic and seeded tie-breaking."""
    # Two bidders submit identical bid of 150.0 at different times
    bids = [
        BidSubmission("Bidder-Early", 150.0, 1.2),
        BidSubmission("Bidder-Late", 150.0, 2.4),
        BidSubmission("Bidder-Third", 100.0, 3.0)
    ]

    # Deterministic: Earliest submission wins
    res_fp = resolve_first_price_auction(bids, openbid=10.0)
    assert res_fp.winner_id == "Bidder-Early"
    assert np.isclose(res_fp.payment, 150.0)
    assert res_fp.is_tied is True

    # Second-price with tie: Winner pays second-highest, which equals the tied bid (150.0)
    res_sp = resolve_second_price_auction(bids, openbid=10.0)
    assert res_sp.winner_id == "Bidder-Early"
    assert np.isclose(res_sp.payment, 150.0)
    assert res_sp.is_tied is True


def test_reproducible_seeded_tie_break():
    """Verify that seeded tie-breaking produces deterministic outcomes without altering real records."""
    bids = [
        BidSubmission("Bidder-X", 100.0, 1.0),
        BidSubmission("Bidder-Y", 100.0, 1.0)  # Same amount, same time
    ]
    res1 = resolve_first_price_auction(bids, openbid=10.0, tie_break_seed=42)
    res2 = resolve_first_price_auction(bids, openbid=10.0, tie_break_seed=42)
    assert res1.winner_id == res2.winner_id
    assert res1.payment == res2.payment


def test_no_eligible_bids_meeting_openbid():
    """Auctions where all bids are below reserve/openbid."""
    bids = [
        BidSubmission("Bidder-A", 10.0, 1.0),
        BidSubmission("Bidder-B", 20.0, 2.0)
    ]
    res_fp = resolve_first_price_auction(bids, openbid=50.0)
    assert res_fp.winner_id is None
    assert res_fp.payment == 0.0

    res_sp = resolve_second_price_auction(bids, openbid=50.0)
    assert res_sp.winner_id is None
    assert res_sp.payment == 0.0
