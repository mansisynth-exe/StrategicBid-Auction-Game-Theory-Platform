"""
audit_dataset.py: Exhaustive data audit for StrategicBid.
Audits raw auction records from Zenodo record 11259259.
"""

import os
import json
import hashlib
import pandas as pd
import numpy as np

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def run_audit():
    raw_zip = 'data/raw/Online_Auctions_Dataset.zip'
    auction_csv = 'data/raw/extracted/auction.csv'
    swarovski_csv = 'data/raw/extracted/swarovski.csv'

    audit_results = {}

    # File provenance
    audit_results['provenance'] = {
        'source_title': 'Online Auctions Dataset',
        'zenodo_record_url': 'https://zenodo.org/records/11259259',
        'doi': '10.5281/zenodo.11259259',
        'license': 'Creative Commons Attribution 4.0 International (CC-BY-4.0)',
        'original_zip_name': 'Online Auctions Dataset.zip',
        'original_zip_size_bytes': os.path.getsize(raw_zip) if os.path.exists(raw_zip) else None,
        'original_zip_sha256': compute_sha256(raw_zip) if os.path.exists(raw_zip) else None,
        'auction_csv_size_bytes': os.path.getsize(auction_csv) if os.path.exists(auction_csv) else None,
        'auction_csv_sha256': compute_sha256(auction_csv) if os.path.exists(auction_csv) else None,
        'swarovski_csv_size_bytes': os.path.getsize(swarovski_csv) if os.path.exists(swarovski_csv) else None,
        'swarovski_csv_sha256': compute_sha256(swarovski_csv) if os.path.exists(swarovski_csv) else None,
    }

    # Load auction.csv
    df_auc = pd.read_csv(auction_csv)
    audit_results['auction_csv'] = {
        'total_rows': int(len(df_auc)),
        'total_columns': int(len(df_auc.columns)),
        'columns': list(df_auc.columns),
        'dtypes': {col: str(dtype) for col, dtype in df_auc.dtypes.items()},
        'missing_values': {col: int(val) for col, val in df_auc.isnull().sum().items()},
        'exact_duplicates': int(df_auc.duplicated().sum()),
        'unique_auctions': int(df_auc['auctionid'].nunique()),
        'unique_bidders': int(df_auc['bidder'].dropna().nunique()),
        'items': df_auc['item'].value_counts().to_dict(),
        'auction_types': df_auc['auction_type'].value_counts().to_dict(),
    }

    # Analyze groupings
    grouped = df_auc.groupby('auctionid')
    bids_per_auc = grouped.size()
    bidders_per_auc = grouped['bidder'].apply(lambda s: s.dropna().nunique())
    
    # Uniformity of auction-level attributes
    non_uniform_openbid = int((grouped['openbid'].nunique() > 1).sum())
    non_uniform_price = int((grouped['price'].nunique() > 1).sum())
    non_uniform_item = int((grouped['item'].nunique() > 1).sum())
    non_uniform_type = int((grouped['auction_type'].nunique() > 1).sum())

    audit_results['auction_aggregates'] = {
        'bids_per_auction': {
            'mean': float(bids_per_auc.mean()),
            'median': float(bids_per_auc.median()),
            'std': float(bids_per_auc.std()),
            'min': int(bids_per_auc.min()),
            'max': int(bids_per_auc.max()),
            'count_1_bid': int((bids_per_auc == 1).sum()),
            'count_2_bids': int((bids_per_auc == 2).sum()),
            'count_gte_3_bids': int((bids_per_auc >= 3).sum())
        },
        'bidders_per_auction': {
            'mean': float(bidders_per_auc.mean()),
            'median': float(bidders_per_auc.median()),
            'std': float(bidders_per_auc.std()),
            'min': int(bidders_per_auc.min()),
            'max': int(bidders_per_auc.max()),
            'count_1_bidder': int((bidders_per_auc == 1).sum()),
            'count_2_bidders': int((bidders_per_auc == 2).sum()),
            'count_gte_3_bidders': int((bidders_per_auc >= 3).sum())
        },
        'uniformity': {
            'non_uniform_openbid_auctions': non_uniform_openbid,
            'non_uniform_price_auctions': non_uniform_price,
            'non_uniform_item_auctions': non_uniform_item,
            'non_uniform_type_auctions': non_uniform_type
        }
    }

    # Bid values & Price relationships
    max_bids = grouped['bid'].max()
    prices = grouped['price'].first()
    openbids = grouped['openbid'].first()

    price_eq_max_bid = int(np.isclose(prices, max_bids, atol=1e-4).sum())
    price_gt_max_bid = int((prices > max_bids + 1e-4).sum())
    price_lt_max_bid = int((prices < max_bids - 1e-4).sum())
    price_lt_openbid = int((prices < openbids - 1e-4).sum())

    audit_results['pricing_consistency'] = {
        'price_eq_max_bid_count': price_eq_max_bid,
        'price_gt_max_bid_count': price_gt_max_bid,
        'price_lt_max_bid_count': price_lt_max_bid,
        'price_lt_openbid_count': price_lt_openbid,
        'anomalous_auctions': []
    }

    for aid, g in grouped:
        max_b = g['bid'].max()
        p = g['price'].iloc[0]
        ob = g['openbid'].iloc[0]
        if abs(max_b - p) > 1e-4 or g['openbid'].nunique() > 1:
            audit_results['pricing_consistency']['anomalous_auctions'].append({
                'auctionid': int(aid),
                'bids_count': int(len(g)),
                'max_bid': float(max_b),
                'price': float(p),
                'openbid_min': float(g['openbid'].min()),
                'openbid_max': float(g['openbid'].max()),
                'item': str(g['item'].iloc[0])
            })

    # Load swarovski.csv
    df_swar = pd.read_csv(swarovski_csv)
    audit_results['swarovski_csv'] = {
        'total_rows': int(len(df_swar)),
        'total_columns': int(len(df_swar.columns)),
        'columns': list(df_swar.columns),
        'dtypes': {col: str(dtype) for col, dtype in df_swar.dtypes.items()},
        'missing_values': {col: int(val) for col, val in df_swar.isnull().sum().items()},
        'unique_sellers': int(df_swar['Seller'].nunique()),
        'unique_bidders': int(df_swar['Bidder'].nunique()),
        'notes': 'swarovski.csv contains aggregate network/volume transaction data between sellers and bidders, lacking auctionid, individual bids, and timestamps. Therefore, auction.csv is the primary micro-level bidding dataset for game-theoretic analysis.'
    }

    # Save to JSON
    with open('data/metadata/audit_results.json', 'w') as f:
        json.dump(audit_results, f, indent=2)

    print("Data audit completed successfully! Output saved to data/metadata/audit_results.json")
    print(json.dumps(audit_results, indent=2))

if __name__ == '__main__':
    run_audit()
