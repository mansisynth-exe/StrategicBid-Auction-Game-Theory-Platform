"""
tests/test_empirical_analysis.py: Unit tests for empirical statistics, sniping calculations,
non-causal regressions, and missing data behavior (Cases 15 & 16).
"""

import pytest
import pandas as pd
import numpy as np

from src.empirical_analysis import (
    compute_auction_level_statistics,
    analyze_openbid_vs_price,
    analyze_bid_timing_and_sniping,
    analyze_bidder_participation
)
from src.data_loader import load_raw_auction_data, DataAcquisitionError
from src.preprocessing import preprocess_auction_data


def test_empirical_unit_of_analysis_and_aggregates():
    """Verify that auction-level statistics aggregate at N=628, not N=10,681."""
    df_raw = load_raw_auction_data()
    clean_bids, clean_auctions, _ = preprocess_auction_data(df_raw, save_processed=False)

    stats = compute_auction_level_statistics(clean_auctions)
    assert stats["total_auctions"] == 628
    assert stats["overall"]["price"]["count"] == 628

    # Commodities present
    expected_items = {"Palm Pilot M515 PDA", "Xbox game console", "Cartier wristwatch"}
    assert set(stats["by_item"].keys()) == expected_items

    # Verify that Cartier wristwatch has higher mean price than Palm Pilot
    cartier_mean = stats["by_item"]["Cartier wristwatch"]["price"]["mean"]
    palm_mean = stats["by_item"]["Palm Pilot M515 PDA"]["price"]["mean"]
    assert cartier_mean > palm_mean


def test_openbid_vs_price_statistics():
    """Verify regression and correlation between openbid and price."""
    df_raw = load_raw_auction_data()
    clean_bids, clean_auctions, _ = preprocess_auction_data(df_raw, save_processed=False)

    res = analyze_openbid_vs_price(clean_auctions)
    assert res["sample_size"] == 628
    assert -1.0 <= res["pearson_correlation"] <= 1.0
    assert -1.0 <= res["spearman_correlation"] <= 1.0
    assert "disclaimer" in res
    assert "Observational" in res["disclaimer"]


def test_sniping_timing_analysis():
    """Verify calculation of sniping metrics in authentic dataset."""
    df_raw = load_raw_auction_data()
    clean_bids, clean_auctions, _ = preprocess_auction_data(df_raw, save_processed=False)

    timing = analyze_bid_timing_and_sniping(clean_bids)
    assert timing["total_bids_analyzed"] == 10681
    assert timing["total_auctions_analyzed"] == 628
    assert timing["bids_last_5min"]["count"] > 0
    assert timing["bids_last_1hr"]["count"] >= timing["bids_last_5min"]["count"]
    assert 0.0 < timing["bids_last_5min"]["percentage"] < 100.0


def test_bidder_participation_statistics():
    """Verify bidder intensity and participation."""
    df_raw = load_raw_auction_data()
    clean_bids, _, _ = preprocess_auction_data(df_raw, save_processed=False)

    part = analyze_bidder_participation(clean_bids)
    assert part["distinct_bidders"] == 3387
    assert part["single_bid_bidders_count"] > 0
    assert part["multi_bid_bidders_count"] > 0
    assert part["single_bid_bidders_count"] + part["multi_bid_bidders_count"] == 3387


def test_no_fake_metrics_when_loading_fails(tmp_path, monkeypatch):
    """Case 15 & 16: Ensure system raises DataAcquisitionError and never manufactures fake metrics."""
    # Monkeypatch paths to point to an empty directory
    import src.data_loader as dl
    monkeypatch.setattr(dl, "RAW_ZIP_PATH", str(tmp_path / "non_existent.zip"))
    monkeypatch.setattr(dl, "AUCTION_CSV_PATH", str(tmp_path / "non_existent.csv"))
    monkeypatch.setattr(dl, "ZENODO_FILE_URL", "https://invalid-domain-1234567.org/bad.zip")

    with pytest.raises(DataAcquisitionError) as exc_info:
        dl.load_raw_auction_data()

    assert "FATAL: Failed to retrieve authentic Online Auctions Dataset" in str(exc_info.value)
    assert "MANUAL RETRIEVAL INSTRUCTIONS" in str(exc_info.value)
