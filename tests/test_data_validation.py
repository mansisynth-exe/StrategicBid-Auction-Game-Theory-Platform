"""
tests/test_data_validation.py: Automated tests for data validation, schema enforcement,
and integrity checking under both authentic and anomalous fixture conditions.
"""

import pytest
import pandas as pd
import numpy as np

from src.data_validation import validate_raw_auction_dataframe, REQUIRED_AUCTION_COLUMNS
from src.data_loader import load_raw_auction_data, DataAcquisitionError


def test_authentic_dataset_validation():
    """Case 1: Correct parsing and validation of authentic dataset."""
    df_raw = load_raw_auction_data()
    assert df_raw is not None
    assert len(df_raw) == 10681
    assert df_raw["auctionid"].nunique() == 628

    report = validate_raw_auction_dataframe(df_raw)
    assert report.is_valid is True
    assert len(report.errors) == 0
    assert report.total_rows == 10681
    assert report.unique_auctions == 628
    assert report.unique_bidders == 3387


def test_missing_required_columns():
    """Case 2: Missing required columns must trigger validation error."""
    df_raw = load_raw_auction_data().copy()
    
    # Drop 'bid' column
    df_missing_bid = df_raw.drop(columns=["bid"])
    rep = validate_raw_auction_dataframe(df_missing_bid)
    assert rep.is_valid is False
    assert any("Missing required columns" in err for err in rep.errors)
    assert "bid" in rep.missing_columns

    # Drop multiple columns
    df_missing_multi = df_raw.drop(columns=["auctionid", "price"])
    rep_multi = validate_raw_auction_dataframe(df_missing_multi)
    assert rep_multi.is_valid is False
    assert "auctionid" in rep_multi.missing_columns
    assert "price" in rep_multi.missing_columns


def test_invalid_and_negative_bid_values():
    """Case 3: Invalid and negative bid values must be detected."""
    fixture = pd.DataFrame({
        "auctionid": [1, 1],
        "bid": [-10.0, 50.0],
        "bidtime": [1.0, 2.0],
        "bidder": ["Alice", "Bob"],
        "bidderrate": [10.0, 5.0],
        "openbid": [1.0, 1.0],
        "price": [50.0, 50.0],
        "item": ["Xbox game console", "Xbox game console"],
        "auction_type": ["3 day auction", "3 day auction"]
    })
    rep = validate_raw_auction_dataframe(fixture)
    assert rep.is_valid is False
    assert rep.negative_bid_count == 1
    assert any("non-positive values" in err for err in rep.errors)


def test_negative_openbid_and_price():
    """Verify detection of negative openbid or price."""
    fixture = pd.DataFrame({
        "auctionid": [1, 1],
        "bid": [10.0, 20.0],
        "bidtime": [1.0, 2.0],
        "bidder": ["Alice", "Bob"],
        "bidderrate": [10.0, 5.0],
        "openbid": [-5.0, -5.0],
        "price": [-20.0, -20.0],
        "item": ["Xbox game console", "Xbox game console"],
        "auction_type": ["3 day auction", "3 day auction"]
    })
    rep = validate_raw_auction_dataframe(fixture)
    assert rep.is_valid is False
    assert rep.negative_openbid_count == 2
    assert rep.negative_price_count == 2


def test_duplicate_records_detection():
    """Case 4: Detection of duplicate records."""
    fixture = pd.DataFrame({
        "auctionid": [1, 1, 1],
        "bid": [10.0, 10.0, 20.0],
        "bidtime": [1.0, 1.0, 2.0],
        "bidder": ["Alice", "Alice", "Bob"],
        "bidderrate": [5.0, 5.0, 10.0],
        "openbid": [1.0, 1.0, 1.0],
        "price": [20.0, 20.0, 20.0],
        "item": ["Xbox game console", "Xbox game console", "Xbox game console"],
        "auction_type": ["3 day auction", "3 day auction", "3 day auction"]
    })
    rep = validate_raw_auction_dataframe(fixture)
    assert rep.duplicate_rows_count == 1
    assert any("duplicate" in w.lower() for w in rep.warnings)


def test_auction_grouping_and_attribute_uniformity():
    """Case 5: Verification of auction grouping and non-uniform attributes."""
    fixture = pd.DataFrame({
        "auctionid": [1, 1],
        "bid": [10.0, 20.0],
        "bidtime": [1.0, 2.0],
        "bidder": ["Alice", "Bob"],
        "bidderrate": [5.0, 10.0],
        "openbid": [1.0, 5.0],  # Non-uniform openbid
        "price": [20.0, 25.0],  # Non-uniform price
        "item": ["Xbox game console", "Cartier wristwatch"],  # Non-uniform item
        "auction_type": ["3 day auction", "3 day auction"]
    })
    rep = validate_raw_auction_dataframe(fixture)
    assert "openbid" in rep.non_uniform_auctions
    assert "price" in rep.non_uniform_auctions
    assert "item" in rep.non_uniform_auctions


def test_distinct_bidder_counts():
    """Case 6: Verification of distinct bidder counts and handling of missing usernames."""
    fixture = pd.DataFrame({
        "auctionid": [1, 1, 1, 2],
        "bid": [10.0, 20.0, 30.0, 40.0],
        "bidtime": [0.5, 1.0, 1.5, 0.5],
        "bidder": ["Alice", "Bob", np.nan, "Alice"],
        "bidderrate": [1.0, 2.0, np.nan, 1.0],
        "openbid": [1.0, 1.0, 1.0, 5.0],
        "price": [30.0, 30.0, 30.0, 40.0],
        "item": ["Xbox game console", "Xbox game console", "Xbox game console", "Xbox game console"],
        "auction_type": ["3 day auction", "3 day auction", "3 day auction", "3 day auction"]
    })
    rep = validate_raw_auction_dataframe(fixture)
    # Distinct non-null bidders: Alice, Bob -> 2
    assert rep.unique_bidders == 2
    assert rep.null_counts["bidder"] == 1


def test_pricing_anomaly_detection():
    """Detection of price exceeding highest recorded bid."""
    fixture = pd.DataFrame({
        "auctionid": [100],
        "bid": [50.0],
        "bidtime": [1.0],
        "bidder": ["Alice"],
        "bidderrate": [1.0],
        "openbid": [1.0],
        "price": [200.0],  # price > max bid
        "item": ["Xbox game console"],
        "auction_type": ["3 day auction"]
    })
    rep = validate_raw_auction_dataframe(fixture)
    assert len(rep.anomalous_pricing_auctions) == 1
    assert rep.anomalous_pricing_auctions[0]["type"] == "PRICE_EXCEEDS_MAX_BID"
