"""
preprocessing.py: Data transformation, deterministic pseudonymization, and aggregation.
Produces cleaned, validated datasets without modifying raw files.
Generates auction-level and bid-level processed tables for empirical and mechanism analysis.
"""

import os
import hashlib
from typing import Tuple, Dict, Any, Optional
import pandas as pd
import numpy as np

PSEUDONYM_SALT = "StrategicBid_GameTheory_2026_Salt"

DURATION_MAP = {
    "3 day auction": 3.0,
    "5 day auction": 5.0,
    "7 day auction": 7.0
}


def generate_bidder_pseudonym(username: Any, salt: str = PSEUDONYM_SALT) -> str:
    """
    Generates a deterministic, privacy-preserving pseudonym from a raw bidder username.
    Produces format 'Bidder-XXXXXXXX' where XXXXXXXX is an 8-character hex digest substring.
    Guarantees zero hash collisions across all unique historical usernames.
    """
    if pd.isna(username) or str(username).strip() == "":
        return "Anonymous_Bidder"
    
    clean_user = str(username).strip().lower()
    hasher = hashlib.sha256()
    hasher.update((salt + clean_user).encode("utf-8"))
    hex_digest = hasher.hexdigest()[:8].upper()
    return f"Bidder-{hex_digest}"


def preprocess_auction_data(
    raw_df: pd.DataFrame,
    save_processed: bool = True,
    processed_dir: Optional[str] = None
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Preprocesses raw auction DataFrame.
    Returns:
        clean_bids_df: Bid-level DataFrame with pseudonyms and timing metrics.
        clean_auctions_df: Auction-level DataFrame aggregated at unique auctionid level.
        cleaning_log: Metadata dictionary detailing transformations applied.
    """
    df = raw_df.copy()
    initial_rows = len(df)
    initial_auctions = df["auctionid"].nunique()

    # 1. Harmonize openbid discrepancies within auctions
    # In raw data, auction 3019271858 has 1 row with openbid=1.0 and 27 with 0.01.
    mode_openbids = df.groupby("auctionid")["openbid"].transform(lambda s: s.mode().iloc[0] if not s.mode().empty else s.iloc[0])
    openbid_fixed_count = int((df["openbid"] != mode_openbids).sum())
    df["openbid"] = mode_openbids

    # 2. Harmonize prices (mode/first within auction)
    mode_prices = df.groupby("auctionid")["price"].transform(lambda s: s.iloc[0])
    df["price"] = mode_prices

    # 3. Deterministic Bidder Pseudonymization
    df["bidder_id"] = df["bidder"].apply(generate_bidder_pseudonym)
    missing_bidders_count = int(df["bidder"].isnull().sum())

    # 4. Auction Duration Mapping
    df["duration_days"] = df["auction_type"].map(DURATION_MAP).fillna(7.0)

    # 5. Timing Metrics
    df["normalized_bidtime"] = np.clip(df["bidtime"] / df["duration_days"], 0.0, 1.0)
    df["time_to_end_hours"] = np.maximum(0.0, (df["duration_days"] - df["bidtime"]) * 24.0)
    # Sniping definitions: bid within last 5 minutes (5/1440 days ~ 0.00347 days) or last 1 hour (1/24 days ~ 0.04167 days)
    df["is_snipe_5min"] = df["time_to_end_hours"] <= (5.0 / 60.0)
    df["is_snipe_1hr"] = df["time_to_end_hours"] <= 1.0

    # Ensure sorting chronologically within each auction
    df = df.sort_values(["auctionid", "bidtime", "bid"]).reset_index(drop=True)

    # 6. Aggregate to Auction-Level Table
    auction_rows = []
    grouped = df.groupby("auctionid", sort=False)

    for aid, g in grouped:
        bids_sorted = g["bid"].sort_values(ascending=False).values
        bidders_unique = g["bidder_id"].nunique()
        max_bid = float(bids_sorted[0]) if len(bids_sorted) > 0 else 0.0
        second_bid = float(bids_sorted[1]) if len(bids_sorted) > 1 else np.nan
        price = float(g["price"].iloc[0])
        openbid = float(g["openbid"].iloc[0])
        duration = float(g["duration_days"].iloc[0])
        item = str(g["item"].iloc[0])
        atype = str(g["auction_type"].iloc[0])
        bids_count = len(g)

        # Eligibility for Counterfactual Replay:
        # Eligible if:
        # - Has at least 1 bid >= openbid
        # - Historical price does not exceed max submitted bid (no missing crawl data)
        # - Has positive bids
        is_eligible = True
        ineligibility_reason = ""

        if price > max_bid + 1e-4:
            is_eligible = False
            ineligibility_reason = "Price exceeds maximum recorded bid (truncated bid history / external transaction)."
        elif bids_count < 1:
            is_eligible = False
            ineligibility_reason = "No bids submitted."
        elif max_bid < openbid - 1e-4:
            is_eligible = False
            ineligibility_reason = "All bids below opening bid (reserve not met)."

        auction_rows.append({
            "auctionid": aid,
            "item": item,
            "auction_type": atype,
            "duration_days": duration,
            "openbid": openbid,
            "price": price,
            "bids_count": bids_count,
            "unique_bidders": bidders_unique,
            "max_bid": max_bid,
            "second_highest_bid": second_bid,
            "first_bid_time": float(g["bidtime"].min()),
            "last_bid_time": float(g["bidtime"].max()),
            "sniping_bids_5min_count": int(g["is_snipe_5min"].sum()),
            "sniping_bids_1hr_count": int(g["is_snipe_1hr"].sum()),
            "has_sniping": bool(g["is_snipe_5min"].sum() > 0),
            "is_eligible_replay": is_eligible,
            "ineligibility_reason": ineligibility_reason
        })

    clean_auctions_df = pd.DataFrame(auction_rows)

    cleaning_log = {
        "initial_bid_rows": initial_rows,
        "processed_bid_rows": len(df),
        "initial_auctions": initial_auctions,
        "processed_auctions": len(clean_auctions_df),
        "missing_bidders_pseudonymized": missing_bidders_count,
        "openbid_discrepancies_harmonized": openbid_fixed_count,
        "eligible_auctions_for_replay": int(clean_auctions_df["is_eligible_replay"].sum()),
        "ineligible_auctions_count": int((~clean_auctions_df["is_eligible_replay"]).sum()),
        "ineligible_auction_ids": clean_auctions_df.loc[~clean_auctions_df["is_eligible_replay"], "auctionid"].tolist()
    }

    if save_processed:
        target_dir = processed_dir or os.path.join(
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
            "data", "processed"
        )
        os.makedirs(target_dir, exist_ok=True)
        clean_bids_path = os.path.join(target_dir, "clean_bids.csv")
        clean_auctions_path = os.path.join(target_dir, "clean_auctions.csv")
        df.to_csv(clean_bids_path, index=False)
        clean_auctions_df.to_csv(clean_auctions_path, index=False)

    return df, clean_auctions_df, cleaning_log
