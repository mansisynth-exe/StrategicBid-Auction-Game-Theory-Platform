"""
data_validation.py: Rigorous schema, domain, and consistency validation for auction data.
Enforces data integrity, identifies missing columns, invalid numerical values,
pricing anomalies, and non-uniform auction attributes without modifying raw records.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Set
import numpy as np
import pandas as pd

REQUIRED_AUCTION_COLUMNS = [
    "auctionid",
    "bid",
    "bidtime",
    "bidder",
    "bidderrate",
    "openbid",
    "price",
    "item",
    "auction_type"
]

VALID_AUCTION_TYPES = {
    "3 day auction": 3.0,
    "5 day auction": 5.0,
    "7 day auction": 7.0
}


@dataclass
class ValidationReport:
    """Structured report detailing validation findings."""
    is_valid: bool
    total_rows: int
    unique_auctions: int
    unique_bidders: int
    missing_columns: List[str] = field(default_factory=list)
    null_counts: Dict[str, int] = field(default_factory=dict)
    duplicate_rows_count: int = 0
    negative_bid_count: int = 0
    negative_openbid_count: int = 0
    negative_price_count: int = 0
    timing_violations_count: int = 0
    non_uniform_auctions: Dict[str, List[int]] = field(default_factory=dict)
    anomalous_pricing_auctions: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def summary_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "total_rows": self.total_rows,
            "unique_auctions": self.unique_auctions,
            "unique_bidders": self.unique_bidders,
            "missing_columns": self.missing_columns,
            "null_counts": self.null_counts,
            "duplicate_rows": self.duplicate_rows_count,
            "negative_bids": self.negative_bid_count,
            "anomalous_pricing_count": len(self.anomalous_pricing_auctions),
            "error_count": len(self.errors),
            "warning_count": len(self.warnings)
        }


def validate_raw_auction_dataframe(df: pd.DataFrame) -> ValidationReport:
    """
    Validates a raw DataFrame against the auction schema and consistency rules.
    Does not mutate input DataFrame.
    """
    errors: List[str] = []
    warnings: List[str] = []

    # 1. Check Required Columns
    missing_cols = [col for col in REQUIRED_AUCTION_COLUMNS if col not in df.columns]
    if missing_cols:
        errors.append(f"Missing required columns: {missing_cols}")
        return ValidationReport(
            is_valid=False,
            total_rows=len(df),
            unique_auctions=0,
            unique_bidders=0,
            missing_columns=missing_cols,
            errors=errors
        )

    total_rows = len(df)
    unique_auctions = int(df["auctionid"].nunique())
    unique_bidders = int(df["bidder"].dropna().nunique())

    # 2. Null Checks
    null_counts = {col: int(df[col].isnull().sum()) for col in REQUIRED_AUCTION_COLUMNS}
    if null_counts["auctionid"] > 0:
        errors.append(f"Found {null_counts['auctionid']} null auctionid values.")
    if null_counts["bid"] > 0:
        errors.append(f"Found {null_counts['bid']} null bid values.")
    if null_counts["price"] > 0:
        errors.append(f"Found {null_counts['price']} null price values.")
    if null_counts["openbid"] > 0:
        errors.append(f"Found {null_counts['openbid']} null openbid values.")
    if null_counts["bidder"] > 0:
        warnings.append(f"Found {null_counts['bidder']} rows with missing bidder username.")
    if null_counts["bidderrate"] > 0:
        warnings.append(f"Found {null_counts['bidderrate']} rows with missing bidderrate.")

    # 3. Duplicate Records
    exact_dups = int(df.duplicated().sum())
    if exact_dups > 0:
        warnings.append(f"Found {exact_dups} exact duplicate rows.")

    # 4. Domain & Range Checks (Positive amounts)
    neg_bids = int((df["bid"] <= 0).sum())
    if neg_bids > 0:
        errors.append(f"Found {neg_bids} bids with non-positive values (<= 0).")

    neg_openbids = int((df["openbid"] < 0).sum())
    if neg_openbids > 0:
        errors.append(f"Found {neg_openbids} negative openbid values.")

    neg_prices = int((df["price"] <= 0).sum())
    if neg_prices > 0:
        errors.append(f"Found {neg_prices} non-positive closing prices.")

    # 5. Timing validation
    timing_violations = 0
    for atype, max_days in VALID_AUCTION_TYPES.items():
        type_mask = df["auction_type"] == atype
        viol = ((df.loc[type_mask, "bidtime"] < 0) | (df.loc[type_mask, "bidtime"] > max_days + 0.1)).sum()
        timing_violations += int(viol)
    if timing_violations > 0:
        warnings.append(f"Found {timing_violations} bids placed outside nominal auction duration.")

    # 6. Auction Grouping & Attribute Uniformity
    grouped = df.groupby("auctionid")
    non_uniform: Dict[str, List[int]] = {}
    for col in ["price", "item", "auction_type", "openbid"]:
        nunique_per_auc = grouped[col].nunique()
        bad_aucs = nunique_per_auc[nunique_per_auc > 1].index.tolist()
        if bad_aucs:
            non_uniform[col] = [int(x) for x in bad_aucs]
            warnings.append(f"Auctions with non-uniform '{col}': {len(bad_aucs)} auctions.")

    # 7. Pricing Anomalies
    anomalous_pricing = []
    for aid, g in grouped:
        max_b = g["bid"].max()
        p = g["price"].iloc[0]
        ob = g["openbid"].min()

        # Case A: Closing price exceeds highest recorded submitted bid
        if p > max_b + 1e-4:
            anomalous_pricing.append({
                "auctionid": int(aid),
                "type": "PRICE_EXCEEDS_MAX_BID",
                "price": float(p),
                "max_bid": float(max_b),
                "bid_count": len(g),
                "detail": f"Closing price ${p:.2f} exceeds highest observed bid ${max_b:.2f}."
            })
        # Case B: Closing price is lower than openbid
        elif p < ob - 1e-4:
            anomalous_pricing.append({
                "auctionid": int(aid),
                "type": "PRICE_BELOW_OPENBID",
                "price": float(p),
                "openbid": float(ob),
                "bid_count": len(g),
                "detail": f"Closing price ${p:.2f} is below opening bid ${ob:.2f}."
            })

    if anomalous_pricing:
        warnings.append(f"Identified {len(anomalous_pricing)} auctions with anomalous pricing/bid relations.")

    is_valid = len(errors) == 0

    return ValidationReport(
        is_valid=is_valid,
        total_rows=total_rows,
        unique_auctions=unique_auctions,
        unique_bidders=unique_bidders,
        missing_columns=[],
        null_counts=null_counts,
        duplicate_rows_count=exact_dups,
        negative_bid_count=neg_bids,
        negative_openbid_count=neg_openbids,
        negative_price_count=neg_prices,
        timing_violations_count=timing_violations,
        non_uniform_auctions=non_uniform,
        anomalous_pricing_auctions=anomalous_pricing,
        errors=errors,
        warnings=warnings
    )
