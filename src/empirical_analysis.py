"""
empirical_analysis.py: Rigorous historical auction analysis on genuine observed records.
Computes descriptive statistics, distributions, bid timing, sniping behavior,
and category comparisons strictly at the defensible unit of analysis (auction-level or bid-level).
Avoids causal claims from observational correlations.
"""

from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from scipy import stats


def compute_auction_level_statistics(auctions_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Computes summary statistics aggregated at the unique auction level (N=628).
    Prevents pseudo-replication from repeating auction-level variables across bids.
    """
    df = auctions_df.copy()
    
    def get_stats(series: pd.Series) -> Dict[str, float]:
        clean = series.dropna()
        if len(clean) == 0:
            return {"count": 0, "mean": 0.0, "median": 0.0, "std": 0.0, "iqr": 0.0, "min": 0.0, "max": 0.0}
        q25, q75 = clean.quantile(0.25), clean.quantile(0.75)
        return {
            "count": int(len(clean)),
            "mean": float(clean.mean()),
            "median": float(clean.median()),
            "std": float(clean.std()),
            "iqr": float(q75 - q25),
            "min": float(clean.min()),
            "max": float(clean.max())
        }

    overall = {
        "price": get_stats(df["price"]),
        "openbid": get_stats(df["openbid"]),
        "bids_count": get_stats(df["bids_count"]),
        "unique_bidders": get_stats(df["unique_bidders"])
    }

    # Breakdown by Item
    by_item = {}
    for item_name, g in df.groupby("item"):
        by_item[item_name] = {
            "sample_size": int(len(g)),
            "price": get_stats(g["price"]),
            "openbid": get_stats(g["openbid"]),
            "bids_count": get_stats(g["bids_count"]),
            "unique_bidders": get_stats(g["unique_bidders"])
        }

    # Breakdown by Duration (auction_type)
    by_duration = {}
    for dtype, g in df.groupby("auction_type"):
        by_duration[dtype] = {
            "sample_size": int(len(g)),
            "duration_days": float(g["duration_days"].iloc[0]),
            "price": get_stats(g["price"]),
            "bids_count": get_stats(g["bids_count"]),
            "unique_bidders": get_stats(g["unique_bidders"])
        }

    return {
        "total_auctions": len(df),
        "overall": overall,
        "by_item": by_item,
        "by_duration": by_duration
    }


def analyze_openbid_vs_price(auctions_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Computes statistical association between opening bid and closing price.
    Includes sample size, correlation coefficients, linear regression, and p-values.
    Includes non-causal disclaimer.
    """
    clean = auctions_df[["openbid", "price", "item"]].dropna()
    x = clean["openbid"].values
    y = clean["price"].values
    n = len(x)

    if n < 3:
        return {"error": "Insufficient sample size"}

    # Pearson and Spearman correlations
    pearson_r, pearson_p = stats.pearsonr(x, y)
    spearman_r, spearman_p = stats.spearmanr(x, y)

    # OLS Regression
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

    # 95% Confidence interval for slope
    t_crit = stats.t.ppf(0.975, df=n - 2)
    slope_ci_lower = slope - t_crit * std_err
    slope_ci_upper = slope + t_crit * std_err

    # By-item correlation
    by_item_corr = {}
    for item_name, g in clean.groupby("item"):
        if len(g) >= 3:
            pr, pp = stats.pearsonr(g["openbid"], g["price"])
            sr, sp = stats.spearmanr(g["openbid"], g["price"])
            by_item_corr[item_name] = {
                "sample_size": len(g),
                "pearson_r": float(pr),
                "pearson_p": float(pp),
                "spearman_r": float(sr),
                "spearman_p": float(sp)
            }

    return {
        "sample_size": n,
        "pearson_correlation": float(pearson_r),
        "pearson_p_value": float(pearson_p),
        "spearman_correlation": float(spearman_r),
        "spearman_p_value": float(spearman_p),
        "ols_slope": float(slope),
        "ols_slope_ci_95": [float(slope_ci_lower), float(slope_ci_upper)],
        "ols_intercept": float(intercept),
        "r_squared": float(r_value ** 2),
        "p_value": float(p_value),
        "std_err": float(std_err),
        "by_item_correlation": by_item_corr,
        "disclaimer": (
            "Observational correlation only. Opening bid selection is endogenous and non-random; "
            "these statistics do not establish causal effects on closing prices."
        )
    }


def analyze_bid_timing_and_sniping(bids_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyzes historical bid submission timing and late bidding ('sniping') patterns.
    Evaluates bids placed in the final 5 minutes, 15 minutes, 1 hour, and 24 hours.
    """
    df = bids_df.copy()
    total_bids = len(df)
    
    # Check if timing metrics exist; if not, calculate
    if "time_to_end_hours" not in df.columns:
        dur = df["auction_type"].map({"3 day auction": 3.0, "5 day auction": 5.0, "7 day auction": 7.0}).fillna(7.0)
        df["time_to_end_hours"] = np.maximum(0.0, (dur - df["bidtime"]) * 24.0)
        df["normalized_bidtime"] = np.clip(df["bidtime"] / dur, 0.0, 1.0)

    # Windows
    bids_last_5min = int((df["time_to_end_hours"] <= (5.0 / 60.0)).sum())
    bids_last_15min = int((df["time_to_end_hours"] <= (15.0 / 60.0)).sum())
    bids_last_1hr = int((df["time_to_end_hours"] <= 1.0).sum())
    bids_last_24hr = int((df["time_to_end_hours"] <= 24.0).sum())

    # Auction-level sniping incidence
    sniping_auctions_5min = int(df.groupby("auctionid")["time_to_end_hours"].apply(lambda s: (s <= (5.0 / 60.0)).any()).sum())
    sniping_auctions_1hr = int(df.groupby("auctionid")["time_to_end_hours"].apply(lambda s: (s <= 1.0).any()).sum())
    total_unique_auctions = int(df["auctionid"].nunique())

    # Winning bids timing (last recorded bid per auction)
    winning_bids = df.sort_values("bidtime").groupby("auctionid").last()
    winning_bids_5min = int((winning_bids["time_to_end_hours"] <= (5.0 / 60.0)).sum())
    winning_bids_1hr = int((winning_bids["time_to_end_hours"] <= 1.0).sum())

    return {
        "total_bids_analyzed": total_bids,
        "total_auctions_analyzed": total_unique_auctions,
        "bids_last_5min": {
            "count": bids_last_5min,
            "percentage": float((bids_last_5min / total_bids) * 100.0)
        },
        "bids_last_15min": {
            "count": bids_last_15min,
            "percentage": float((bids_last_15min / total_bids) * 100.0)
        },
        "bids_last_1hr": {
            "count": bids_last_1hr,
            "percentage": float((bids_last_1hr / total_bids) * 100.0)
        },
        "bids_last_24hr": {
            "count": bids_last_24hr,
            "percentage": float((bids_last_24hr / total_bids) * 100.0)
        },
        "auctions_with_sniping_5min": {
            "count": sniping_auctions_5min,
            "percentage": float((sniping_auctions_5min / total_unique_auctions) * 100.0)
        },
        "auctions_with_sniping_1hr": {
            "count": sniping_auctions_1hr,
            "percentage": float((sniping_auctions_1hr / total_unique_auctions) * 100.0)
        },
        "winning_bids_in_last_5min": {
            "count": winning_bids_5min,
            "percentage": float((winning_bids_5min / total_unique_auctions) * 100.0)
        },
        "winning_bids_in_last_1hr": {
            "count": winning_bids_1hr,
            "percentage": float((winning_bids_1hr / total_unique_auctions) * 100.0)
        }
    }


def analyze_bidder_participation(bids_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyzes bidder participation, bidding intensity, and repeated bidder activity.
    Respects privacy by using pseudonymized identifiers.
    """
    df = bids_df.copy()
    bidder_col = "bidder_id" if "bidder_id" in df.columns else "bidder"
    
    # Filter out anonymous placeholders to calculate true distinct bidder statistics
    valid_mask = (df[bidder_col] != "Anonymous_Bidder") & (df[bidder_col].notnull())
    valid_bids = df[valid_mask]

    bidder_counts = valid_bids[bidder_col].value_counts()
    auctions_per_bidder = valid_bids.groupby(bidder_col)["auctionid"].nunique()

    return {
        "distinct_bidders": int(len(bidder_counts)),
        "anonymous_bids_count": int((~valid_mask).sum()),
        "single_bid_bidders_count": int((bidder_counts == 1).sum()),
        "single_bid_bidders_percentage": float(((bidder_counts == 1).sum() / len(bidder_counts)) * 100.0) if len(bidder_counts) > 0 else 0.0,
        "multi_bid_bidders_count": int((bidder_counts > 1).sum()),
        "multi_bid_bidders_percentage": float(((bidder_counts > 1).sum() / len(bidder_counts)) * 100.0) if len(bidder_counts) > 0 else 0.0,
        "max_bids_by_single_bidder": int(bidder_counts.max()) if len(bidder_counts) > 0 else 0,
        "mean_bids_per_bidder": float(bidder_counts.mean()) if len(bidder_counts) > 0 else 0.0,
        "median_bids_per_bidder": float(bidder_counts.median()) if len(bidder_counts) > 0 else 0.0,
        "bidders_in_multiple_auctions": int((auctions_per_bidder > 1).sum()),
        "bidders_in_multiple_auctions_pct": float(((auctions_per_bidder > 1).sum() / len(auctions_per_bidder)) * 100.0) if len(auctions_per_bidder) > 0 else 0.0,
        "max_auctions_participated_by_one_bidder": int(auctions_per_bidder.max()) if len(auctions_per_bidder) > 0 else 0
    }
