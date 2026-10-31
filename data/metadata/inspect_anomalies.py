import pandas as pd
import numpy as np

df = pd.read_csv('data/raw/extracted/auction.csv')

print("Total rows:", len(df))
print("Total auctions:", df['auctionid'].nunique())

grouped = df.groupby('auctionid')

for aid, g in grouped:
    max_b = g['bid'].max()
    p = g['price'].iloc[0]
    if abs(max_b - p) > 1e-4:
        print(f"\nAuction {aid}: max_bid={max_b}, price={p}, openbid={g['openbid'].iloc[0]}")
        print(g[['bid', 'bidder', 'bidtime', 'openbid', 'price']])

for aid, g in grouped:
    if g['openbid'].nunique() > 1:
        print(f"\nNon-uniform openbid auction {aid}:")
        print(g[['bid', 'bidder', 'bidtime', 'openbid', 'price']])
