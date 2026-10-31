"""
auctions.py: Core Game-Theoretic Auction Models and Mathematical Formulations.
Provides theoretical benchmarks for First-Price and Second-Price sealed-bid auctions.
Contains rigorous mathematical documentation distinguishing theoretical equilibria from empirical observations.
"""

from dataclasses import dataclass
from typing import Optional, List, Tuple, Dict, Any
import numpy as np


@dataclass
class BidSubmission:
    """Represents a submitted bid in an auction."""
    bidder_id: str
    bid_amount: float
    bid_time: float  # elapsed days or timestamp


@dataclass
class AuctionResult:
    """Result of an auction mechanism resolution."""
    mechanism: str
    winner_id: Optional[str]
    winning_bid: float
    payment: float
    second_bid: float
    openbid: float
    is_tied: bool
    tie_break_method: str
    competing_bids_count: int
    eligible_bids_count: int
    notes: str


# ==============================================================================
# MODEL 1: STANDARD FIRST-PRICE SEALED-BID (FPSB) AUCTION
# ==============================================================================

def first_price_equilibrium_bid(valuation: float, n_bidders: int, v_max: Optional[float] = None) -> float:
    """
    Theoretical Bayesian Nash Equilibrium (BNE) bidding strategy for symmetric,
    risk-neutral bidders with Independent Private Values (IPV) uniformly distributed on [0, V].

    Mathematical Formulation:
        b(v) = ((n - 1) / n) * v

    Assumptions:
        - Symmetric risk-neutral bidders.
        - Valuations v_i ~ i.i.d. Uniform[0, V].
        - No reserve price (or non-binding reserve).
        - Sealed single-shot submission.

    CRITICAL SCIENTIFIC WARNING:
        This is a purely theoretical benchmark. It requires known true private valuations.
        Historical eBay bids CANNOT be substituted as valuations to claim 'proof' of Nash Equilibrium.
    """
    if n_bidders < 1:
        raise ValueError(f"Number of bidders n must be >= 1, got {n_bidders}")
    if valuation < 0:
        raise ValueError(f"Valuation must be non-negative, got {valuation}")
    if n_bidders == 1:
        return 0.0  # Monopolist bidder with no reserve pays 0
    return ((n_bidders - 1.0) / float(n_bidders)) * valuation


def first_price_expected_revenue(n_bidders: int, v_max: float) -> float:
    """
    Theoretical expected seller revenue in FPSB under Uniform[0, V_max]:
        E[Revenue] = ((n - 1) / (n + 1)) * V_max
    By Revenue Equivalence Theorem, matches SPSB expected revenue under identical IPV conditions.
    """
    if n_bidders < 1 or v_max <= 0:
        raise ValueError("Invalid parameters for expected revenue")
    return ((n_bidders - 1.0) / (n_bidders + 1.0)) * v_max


def calculate_shading_factor(n_bidders: int) -> float:
    """
    Theoretical bid shading ratio b(v)/v = (n - 1) / n in FPSB equilibrium.
    """
    if n_bidders <= 1:
        return 0.0
    return (n_bidders - 1.0) / float(n_bidders)


# ==============================================================================
# MODEL 2: STANDARD SECOND-PRICE SEALED-BID (SPSB / VICKREY) AUCTION
# ==============================================================================

def second_price_dominant_bid(valuation: float) -> float:
    """
    Weakly Dominant Strategy in Second-Price Sealed-Bid Auction:
        b*(v) = v

    Under Independent Private Values (IPV) and absence of externalities or budget constraints,
    bidding one's true private valuation weakly dominates any other bid b_i != v_i.

    Proof Summary:
        Let B = max_{j != i} b_j be the highest competing bid.
        - If bidder submits b_i > v_i:
            * If B >= b_i: bidder loses, utility 0.
            * If B < v_i: bidder wins, utility v_i - B > 0 (same as bidding v_i).
            * If v_i < B < b_i: bidder wins, but utility is v_i - B < 0 (worse than bidding v_i).
        - If bidder submits b_i < v_i:
            * If B <= b_i: bidder wins, utility v_i - B > 0 (same as bidding v_i).
            * If B > v_i: bidder loses, utility 0 (same as bidding v_i).
            * If b_i < B < v_i: bidder loses, utility 0 (worse than bidding v_i where utility is v_i - B > 0).
        Hence, truthful bidding b_i = v_i guarantees the highest possible payoff regardless of B.
    """
    if valuation < 0:
        raise ValueError(f"Valuation must be non-negative, got {valuation}")
    return float(valuation)


def calculate_bidder_utility(valuation: float, payment: float, is_winner: bool) -> float:
    """
    Calculates realized utility / consumer surplus for a bidder:
        u_i = v_i - payment if is_winner else 0.0
    """
    if not is_winner:
        return 0.0
    return valuation - payment


# ==============================================================================
# MECHANISM RESOLUTION ENGINES (FOR REAL INPUT BIDS)
# ==============================================================================

def resolve_first_price_auction(
    bids: List[BidSubmission],
    openbid: float = 0.0,
    tie_break_seed: Optional[int] = None
) -> AuctionResult:
    """
    Resolves a First-Price Auction given submitted bids and an opening/reserve bid.
    Payment rule: Winner pays their own submitted bid.

    Tie-breaking:
        Deterministic: Earliest submission time (bid_time) wins.
        If tie_break_seed is provided, ties with identical bid_time are resolved pseudo-randomly.
    """
    eligible = [b for b in bids if b.bid_amount >= openbid]
    if not eligible:
        return AuctionResult(
            mechanism="FIRST_PRICE",
            winner_id=None,
            winning_bid=0.0,
            payment=0.0,
            second_bid=0.0,
            openbid=openbid,
            is_tied=False,
            tie_break_method="NONE",
            competing_bids_count=0,
            eligible_bids_count=0,
            notes="No eligible bids meeting opening bid."
        )

    # Sort descending by bid_amount, ascending by bid_time (earliest bid takes priority)
    # If tie_break_seed provided and exact same bid amount & time, apply deterministic random seed
    if tie_break_seed is not None:
        rng = np.random.RandomState(tie_break_seed)
        eligible_sorted = sorted(
            eligible,
            key=lambda b: (-b.bid_amount, b.bid_time, rng.random())
        )
    else:
        eligible_sorted = sorted(
            eligible,
            key=lambda b: (-b.bid_amount, b.bid_time)
        )

    top_bid = eligible_sorted[0]
    second_amount = eligible_sorted[1].bid_amount if len(eligible_sorted) > 1 else openbid

    # Check if there is an exact monetary tie for first place
    tied_top = [b for b in eligible_sorted if np.isclose(b.bid_amount, top_bid.bid_amount, atol=1e-5)]
    is_tied = len(tied_top) > 1

    return AuctionResult(
        mechanism="FIRST_PRICE",
        winner_id=top_bid.bidder_id,
        winning_bid=float(top_bid.bid_amount),
        payment=float(top_bid.bid_amount),
        second_bid=float(second_amount),
        openbid=float(openbid),
        is_tied=is_tied,
        tie_break_method="EARLIEST_TIMESTAMP" if not tie_break_seed else f"SEEDED_RANDOM_{tie_break_seed}",
        competing_bids_count=len(bids),
        eligible_bids_count=len(eligible),
        notes="Winner pays highest submitted bid."
    )


def resolve_second_price_auction(
    bids: List[BidSubmission],
    openbid: float = 0.0,
    tie_break_seed: Optional[int] = None
) -> AuctionResult:
    """
    Resolves a Second-Price Auction (Vickrey rule).
    Payment rule:
        Winner is the highest eligible bidder.
        Payment = max(openbid, second_highest_bid) if >= 2 eligible bids from distinct bidders,
        or openbid if only 1 eligible bidder.

    Tie-breaking:
        Deterministic: Earliest submission time (bid_time) wins.
        If tie_break_seed is provided, ties with identical bid_time are resolved pseudo-randomly.
        In a monetary tie for 1st place between different bidders:
        Second bid equals the tied amount, so winner pays the tied bid amount.
    """
    eligible = [b for b in bids if b.bid_amount >= openbid]
    if not eligible:
        return AuctionResult(
            mechanism="SECOND_PRICE",
            winner_id=None,
            winning_bid=0.0,
            payment=0.0,
            second_bid=0.0,
            openbid=openbid,
            is_tied=False,
            tie_break_method="NONE",
            competing_bids_count=0,
            eligible_bids_count=0,
            notes="No eligible bids meeting opening bid."
        )

    if tie_break_seed is not None:
        rng = np.random.RandomState(tie_break_seed)
        eligible_sorted = sorted(
            eligible,
            key=lambda b: (-b.bid_amount, b.bid_time, rng.random())
        )
    else:
        eligible_sorted = sorted(
            eligible,
            key=lambda b: (-b.bid_amount, b.bid_time)
        )

    winner = eligible_sorted[0]
    
    # Identify competing bids from DISTINCT bidders
    other_bidder_bids = [b for b in eligible_sorted if b.bidder_id != winner.bidder_id]
    
    if other_bidder_bids:
        second_highest_competing_bid = other_bidder_bids[0].bid_amount
        payment = max(openbid, second_highest_competing_bid)
    else:
        # Sole bidder: pays openbid/reserve
        second_highest_competing_bid = openbid
        payment = openbid

    # Check ties among top bidders
    tied_top = [b for b in eligible_sorted if np.isclose(b.bid_amount, winner.bid_amount, atol=1e-5)]
    is_tied = len(tied_top) > 1

    return AuctionResult(
        mechanism="SECOND_PRICE",
        winner_id=winner.bidder_id,
        winning_bid=float(winner.bid_amount),
        payment=float(payment),
        second_bid=float(second_highest_competing_bid),
        openbid=float(openbid),
        is_tied=is_tied,
        tie_break_method="EARLIEST_TIMESTAMP" if not tie_break_seed else f"SEEDED_RANDOM_{tie_break_seed}",
        competing_bids_count=len(bids),
        eligible_bids_count=len(eligible),
        notes="Winner pays second-highest eligible competing bid (or openbid if single bidder)."
    )
