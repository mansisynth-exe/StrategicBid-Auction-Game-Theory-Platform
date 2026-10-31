# StrategicBid Data Dictionary & Cleaning Specification

## 1. Provenance & Source Metadata

- **Dataset Title**: Online Auctions Dataset
- **Official Repository**: Zenodo Record 11259259
- **DOI**: [10.5281/zenodo.11259259](https://doi.org/10.5281/zenodo.11259259)
- **License**: Creative Commons Attribution 4.0 International (CC-BY-4.0)
- **Original Archive**: `Online Auctions Dataset.zip` (140,435 bytes, SHA256: `a25dfdd0c4204d9f1b62983c3991ed5deef18bfdfe10c534852749a242807e4b`)
- **Primary Source File**: `auction.csv` (1,043,530 bytes, 10,681 rows, SHA256: `c05d10bafd4f33aadb2c70ab562a23937bd11c8d32a7c73244c829c06302486e`)
- **Supplementary File**: `swarovski.csv` (5,827 bytes, 200 rows, SHA256: `def9ece464853db6e91c71e7f0eeb54853bec1872ef0da4df3984b1146bc0907`)
- **Original Source Acknowledgment**: Modeling Online Auctions research repository ([modelingonlineauctions.com](http://www.modelingonlineauctions.com/datasets))

---

## 2. Raw Schema: `auction.csv`

| Column Name | Raw Dtype | Description | Observed Domain / Range | Missing Values |
|---|---|---|---|---|
| `auctionid` | `int64` | Unique identifier of an auction | 628 distinct IDs | 0 |
| `bid` | `float64` | Submitted bid value recorded in USD | $0.01 to $5,400.00 | 0 |
| `bidtime` | `float64` | Time of bid placement in elapsed days from auction launch | 0.000012 to 6.999988 days | 0 |
| `bidder` | `object` | Historical eBay username | 3,387 distinct usernames | 16 (0.15%) |
| `bidderrate` | `float64` | eBay feedback score/rating of the bidder at time of bidding | -4.0 to 30,192.0 | 11 (0.10%) |
| `openbid` | `float64` | Opening / starting bid set by the seller | $0.01 to $5,000.00 | 0 |
| `price` | `float64` | Recorded closing/settlement price of the auction | $0.01 to $5,400.00 | 0 |
| `item` | `object` | Item category name | 3 items: Palm Pilot M515 PDA, Xbox game console, Cartier wristwatch | 0 |
| `auction_type` | `object` | Duration category of the auction on eBay | 3 types: '3 day auction', '5 day auction', '7 day auction' | 0 |

---

## 3. Supplementary Schema: `swarovski.csv`

| Column Name | Raw Dtype | Description | Notes |
|---|---|---|---|
| `Seller` | `int64` | Pseudonymous integer ID for seller | 49 unique sellers |
| `Bidder` | `int64` | Pseudonymous integer ID for bidder | 191 unique bidders |
| `Weight` | `int64` | Number of interactions/transactions | Range: 1 to 14 |
| `Bidder.Volume` | `int64` | Total transaction volume of bidder | Range: 1 to 32 |
| `Seller.Volume` | `int64` | Total transaction volume of seller | Range: 1 to 4,681 |

*Note*: `swarovski.csv` is an aggregated bipartite network of seller-bidder transactions without auction IDs, bid timestamps, or individual bid amounts. Hence, micro-level game-theoretic mechanism replays are conducted strictly on `auction.csv`.

---

## 4. Empirical Realities & Interpretability Constraints

1. **Meaning of `auction_type`**:
   - `auction_type` corresponds strictly to **auction duration** (3 days, 5 days, or 7 days).
   - It **does NOT** distinguish between auction pricing mechanisms (e.g., First-Price vs. Second-Price). All auctions are historical eBay ascending auctions conducted via automated proxy bidding.
   - Counterfactual First-Price and Second-Price models are distinct re-simulations and must never be portrayed as historical mechanisms.

2. **Repetition of Auction-Level Attributes**:
   - `price`, `openbid`, `item`, and `auction_type` are repeated across all bid rows belonging to the same `auctionid`.
   - In 1 auction (`3019271858`), a single row lists `openbid=1.0` while 27 other rows list `openbid=0.01`. In preprocessing, auction-level attributes are normalized by resolving to the consensus/mode opening bid.
   - In statistical summaries of auction prices, aggregation must occur at the **auction level** ($N=628$), never at the bid level ($N=10,681$), to prevent severe sample inflation and pseudo-replication.

3. **Nature of Recorded Bids and Proxy Dynamics**:
   - In eBay's historical interface, the final recorded bid of the winning bidder is displayed as equal to the closing price (the second-highest bid plus the applicable bid increment).
   - The true maximum valuation of the winning bidder is unobserved if it exceeded the closing price.
   - Losing bidders' bids reflect their submitted proxy ceilings.
   - In 626 of 628 auctions, `max(bid) == price`.
   - In 1 auction (`3016587753`), `price=255.0` while only 1 bid of `5.0` is present in the record (missing crawl records or Buy-It-Now). This auction is marked **ineligible** for replay.

4. **Bidder Privacy & Pseudonymization**:
   - Real eBay usernames are present in `bidder`.
   - Section 1 & Section 6 mandate that individual usernames are **never displayed directly** in UI tables or analytical exports.
   - Preprocessing applies salted deterministic SHA-256 pseudonymization: mapping usernames to consistent tokens like `Bidder-7A3F`. Missing usernames are encoded as `Anonymous_Bidder`.

---

## 5. Cleaning & Exclusion Rules

| Code | Rule Description | Action Taken | Rationale |
|---|---|---|---|
| `RULE-CLEAN-01` | Preserve Raw Files | Stored read-only in `data/raw/` | Source preservation |
| `RULE-CLEAN-02` | Pseudonymize Bidders | Generate `bidder_id` from salted hash | Compliance with privacy standards |
| `RULE-CLEAN-03` | Impute Missing Bidder Labels | Assign deterministic token `Anonymous_<hash>` | 16 rows lack usernames; prevents drop while preserving grouping |
| `RULE-CLEAN-04` | Harmonize Non-Uniform `openbid` | Group by `auctionid` and take first valid mode | Resolves 1-row data entry artifact |
| `RULE-EXCL-01` | Zero or Single-Bid Auctions | Flag as ineligible for Second-Price Replay | A second-price replay requires at least 2 distinct eligible submitted bids or explicit reserve price handling |
| `RULE-EXCL-02` | Missing Competing Bid Anomalies | Flag as ineligible if `price > max_bid + 1e-4` | Auction `3016587753` has truncated bid history |
| `RULE-EXCL-03` | Negative or Malformed Bids | Reject rows where `bid <= 0` or `openbid < 0` | Economic validity (none observed in raw data) |
