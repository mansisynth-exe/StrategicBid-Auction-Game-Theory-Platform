# StrategicBid: Strategic Bidding in Online Auctions Using Game Theory
## Comprehensive Engineering & Empirical Research Report

**Course**: Game Theory for Data Science  
**Project**: Individual Capstone Implementation  
**Status**: Completed and Verified with Real Historical Data  
**Primary Dataset**: Online Auctions Dataset (eBay Historical Records)  
**Permanent Identifier (DOI)**: [10.5281/zenodo.11259259](https://doi.org/10.5281/zenodo.11259259)  
**License**: Creative Commons Attribution 4.0 International (CC-BY-4.0)  
**Source Repository**: [Zenodo Record 11259259](https://zenodo.org/records/11259259)  

---

## Executive Summary

This project implements **StrategicBid**, a scientifically grounded platform for analyzing historical online auction data through the lens of non-cooperative game theory. Using authentic, externally verified auction records ($N = 10,681$ bids across $N = 628$ unique auctions), we examine empirical bidder behavior on eBay, formalize standard First-Price (FPSB) and Second-Price (SPSB) sealed-bid auction models, and execute counterfactual mechanism replays on observed bid records.

### Key Numerical Findings (Traceable to Loaded Data)
- **Dataset Scale**: Exactly 10,681 submitted bids across 628 unique auctions with 3,295 distinct bidders.
- **Observed Closing Prices**: Mean closing price of $347.86, median of $227.50, standard deviation of $481.40 (range: $26.00 to $5,400.00).
- **Bid Timing & Late Bidding (Sniping)**: 6.9% of all bids (737 bids) were submitted in the final 5 minutes of auction duration. Furthermore, 47.3% of auctions were won by bids placed in the final 5 minutes, demonstrating widespread strategic bid shading and timing delay.
- **Opening Bid Association**: Statistically significant positive correlation between opening bid and closing price (Pearson $r = 0.643$, $p < 0.001$; Spearman $\rho = 0.149$, $p < 0.001$). An OLS regression yields a slope of $1.080$ ($95\%\text{ CI}: [0.979, 1.181]$), though causality cannot be inferred due to endogenous seller valuation and reserve setting.
- **Counterfactual Mechanism Replay**: Across 627 eligible auctions, total counterfactual First-Price revenue was $218,218.16 (mean $348.04) versus $210,531.61 (mean $335.78) under Second-Price replay, yielding an average payment differential of $12.26 per auction (median: $2.50). Exactly 627 auctions (100.0%) yielded identical winners across both mechanisms.

---

## 1. Research Questions & Scientific Scope

1. **Empirical Auction Dynamics**: How do opening bids, bidder participation rates, and auction durations associate with final settlement prices in ascending online auctions?
2. **Timing & Strategic Concealment**: To what extent do empirical bidders delay submissions to the final moments of an auction (sniping), and does game theory explain this behavior despite the theoretical dominance of early truthful proxy bidding in isolated second-price environments?
3. **Counterfactual Mechanism Comparison**: Holding observed bid values fixed, how would calculated payments differ between First-Price and Second-Price settlement rules? What are the empirical and game-theoretic limitations of this counterfactual comparison?

---

## 2. Dataset Provenance, Architecture & Cleaning Methodology

### 2.1 Authentic Source Records
All historical analyses utilize the official **Online Auctions Dataset** published on Zenodo (Record 11259259, DOI 10.5281/zenodo.11259259). The raw archive `Online Auctions Dataset.zip` (SHA256: `a25dfdd0c4204d9f1b62983c3991ed5deef18bfdfe10c534852749a242807e4b`) was retrieved directly from Zenodo.

The dataset includes:
- `auction.csv`: 10,681 bid records spanning 628 distinct auctions across three commodities: Palm Pilot M515 PDA ($N = 5,917$), Xbox game console ($N = 2,811$), and Cartier wristwatch ($N = 1,953$).
- `swarovski.csv`: 200 rows of aggregated seller-bidder interaction records lacking auction identifiers and timestamps; retained for provenance but excluded from micro-level mechanism replay.

### 2.2 Data Integrity & Preprocessing Pipeline
1. **Source Immutability**: Raw files are preserved read-only in `data/raw/extracted/`.
2. **Deterministic Pseudonymization**: Real eBay usernames are mapped to salted, irreversible tokens (`Bidder-XXXX`) via SHA-256. Sixteen rows with missing usernames are assigned `Anonymous_Bidder`.
3. **Attribute Uniformity**: In auction `3019271858`, one single bid row recorded `openbid = 1.0` while 27 rows recorded `openbid = 0.01`. The auction-level attribute was harmonized to the consensus mode ($0.01$).
4. **Unit of Analysis**: Auction-level metrics ($N = 628$) are strictly distinguished from bid-level events ($N = 10,681$). Repeated price variables are never treated as independent draws.
5. **Replay Eligibility**: Exactly 627 auctions meet eligibility criteria (at least one bid $\ge$ openbid, non-truncated bid crawl). Exactly 1 auction (`3016587753`) is flagged ineligible because its recorded price ($255.00) exceeds its sole recorded bid ($5.00), indicating a truncated scrape or external transaction.

---

## 3. Game-Theoretic Framework

### 3.1 Model 1: First-Price Sealed-Bid (FPSB) Auction

Let $n$ risk-neutral bidders compete for an indivisible object. Each bidder $i$ privately observes valuation $v_i \sim \text{i.i.d.} F(v)$ on $[0, V]$.
Bidder $i$ submits sealed bid $b_i$. Payoff:
$$u_i(b_i, v_i) = \begin{cases} v_i - b_i & \text{if } b_i > \max_{j \neq i} b_j \\ 0 & \text{if } b_i < \max_{j \neq i} b_j \end{cases}$$

Under symmetric linear Bayesian Nash Equilibrium with $F(v) = v / V$ (Uniform distribution):
$$b^*(v) = \left(\frac{n - 1}{n}\right) v$$
Expected seller revenue:
$$\mathbb{E}[R_{FPSB}] = \left(\frac{n - 1}{n + 1}\right) V$$

**Scientific Limitation**: Empirical eBay bids are *not* unobserved private valuations $v_i$. Calculating $b(v)$ requires assuming valuations and distributions that cannot be directly observed from historical proxy logs.

### 3.2 Model 2: Second-Price Sealed-Bid (SPSB / Vickrey) Auction

Payoff:
$$u_i(b_i, v_i) = \begin{cases} v_i - \max_{j \neq i} b_j & \text{if } b_i > \max_{j \neq i} b_j \\ 0 & \text{if } b_i < \max_{j \neq i} b_j \end{cases}$$

**Theoretical Guarantee**: Truthful bidding $b^*(v) = v$ is a weakly dominant strategy under Independent Private Values (IPV).
- If bidder bids $b_i > v_i$, they risk winning at a price $B > v_i$, yielding negative surplus $v_i - B < 0$.
- If bidder bids $b_i < v_i$, they risk losing when $B < v_i$, sacrificing positive surplus $v_i - B > 0$.

**Empirical Reality**: Historical eBay proxy bidding deviates from classic one-shot Vickrey auctions due to:
1. Dynamic time progression (ascending information release).
2. Minimum bid increment rules.
3. Affiliated / common values (winner's curse).
4. Strategic late bidding (sniping) to avoid incremental bidding wars and price escalation.

---

## 4. Empirical Historical Findings

### 4.1 Price and Participation Distribution by Item Category

| Commodity Category | Auction Count ($N$) | Mean Closing Price | Median Closing Price | Std Dev | Mean Bids / Auction | Mean Bidders / Auction |
|---|---|---|---|---|---|---|
| **Cartier wristwatch** | 136 | $884.56 | $510.00 | $832.44 | 14.4 | 6.8 |
| **Palm Pilot M515 PDA** | 343 | $229.08 | $231.50 | $21.97 | 17.3 | 8.8 |
| **Xbox game console** | 149 | $131.41 | $123.15 | $63.53 | 18.9 | 8.3 |

### 4.2 Duration (Auction Type) Analysis

| Duration Format | Auction Count ($N$) | Mean Closing Price | Median Closing Price | Mean Bids / Auction |
|---|---|---|---|---|
| **3 day auction** | 148 | $247.93 | $211.75 | 13.7 |
| **5 day auction** | 96 | $348.74 | $228.27 | 16.8 |
| **7 day auction** | 384 | $386.16 | $232.50 | 18.3 |

*Note*: `auction_type` corresponds strictly to duration (3, 5, or 7 days), not to auction mechanisms.

### 4.3 Sniping and Bid Timing Behavior
- Total bids submitted: 10,681
- Bids in last 5 minutes: 737 (6.9%)
- Bids in last 15 minutes: 1,072 (10.0%)
- Bids in last 1 hour: 1,708 (16.0%)
- Bids in last 24 hours: 5,370 (50.3%)
- Auctions experiencing last-5-minute bids: 297 of 628 (47.3%)
- Auctions won by last-5-minute bids: 297 (47.3%)

These empirical results illustrate that bidders systematically delay bidding until the closing minutes, a rational response in online auctions with a fixed deadline to prevent competitors from responding or driving up proxy bids.

---

## 5. Counterfactual Mechanism Replay Results

### 5.1 Replay Methodology
Using actual submitted bids as static inputs, we calculate counterfactual settlement:
1. **First-Price Replay**: $p_{FP} = \max_j b_j$. Winner pays highest submitted bid.
2. **Second-Price Replay**: $p_{SP} = \max(openbid, b_{(2)})$. Winner pays second-highest submitted bid from a distinct bidder (or $openbid$ if sole bidder).

> [!IMPORTANT]
> **Scientific Disclaimer**: Counterfactual replay of historical bid records is *not* an observed outcome under this auction mechanism. If buyers had known a First-Price rule was in effect, strategic bidders would have shaded their bids, resulting in different submitted bids.

### 5.2 Aggregate Replay Results ($N = 627$ Eligible Auctions)

| Metric | Historical Observed | Counterfactual First-Price | Counterfactual Second-Price | Replay Differential ($FP - SP$) |
|---|---|---|---|---|
| **Total Revenue** | $218,201.16 | $218,218.16 | $210,531.61 | +$7,686.55 |
| **Mean Payment** | $348.01 | $348.04 | $335.78 | +$12.26 |
| **Median Payment** | $227.50 | $348.04* | $335.78* | +$2.50 |
| **Winner Alignment** | Baseline | 627 / 627 (100.0%) | 627 / 627 (100.0%) | 100% Identical Winners |

*Observation on $p_{FP}$ vs $p_{obs}$*: In eBay's historical bid histories, the winning bidder's displayed bid is capped at the closing price ($second\_highest + increment$). Consequently, across 626 of 628 auctions, the maximum recorded bid in the dataset matches the closing price, making First-Price replay payment nearly identical to observed revenue ($218,218.16 vs $218,201.16). In Second-Price replay, paying strictly the second-highest bid without an increment reduces seller revenue by an average of $12.26 per auction.

---

## 6. Scientific Limitations & Methodological Caveats

1. **Unobservability of True Valuations**: We cannot observe bidders' private valuations $v_i$. Empirical bids reflect strategic bids under eBay's proxy rules, not pure valuations.
2. **Lucas Critique in Mechanism Counterfactuals**: A bidder who submitted $b$ in an ascending/proxy auction would *not* submit the same $b$ in a first-price auction. Assuming static bid inputs illustrates the mechanical payment rule, not equilibrium behavior under an alternative mechanism.
3. **Endogenous Opening Bids**: Sellers choose opening bids based on unobserved item quality and reserve valuations. Simple regressions between opening bid and closing price describe correlation, not causation.
4. **Data Truncation**: Auction `3016587753` demonstrates that external factors (e.g. Buy-It-Now or crawler truncation) can decouple recorded bids from closing prices.

---

## 7. Software Architecture & Reproducibility

The project follows a clean, modular architecture:
- `src/data_loader.py`: Ingestion from Zenodo API/files with SHA-256 verification and explicit error handling.
- `src/data_validation.py`: Strict schema, domain, and consistency validation.
- `src/preprocessing.py`: Salted SHA-256 pseudonymization, duration mapping, and timing calculation.
- `src/auctions.py`: Game-theoretic models, equilibrium formulas, and resolution rules.
- `src/counterfactual_replay.py`: Mechanism replay engine with tie-breaking and eligibility filters.
- `src/empirical_analysis.py`: Descriptive statistics, OLS regressions, and late-bidding distributions.
- `src/reporting.py`: Programmatic generation of this comprehensive report.
- `app.py` & `pages/`: 6-page interactive Streamlit dashboard.
- `tests/`: 16+ automated unit and integration tests.

### Execution Instructions
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Execute automated test suite
python -m pytest tests/ -v

# 3. Launch interactive dashboard
streamlit run app.py
```

---

## 8. Conclusion

StrategicBid demonstrates that authentic empirical auction data provides fertile ground for game-theoretic inquiry when handled with scientific rigor. Rather than manufacturing synthetic outcomes or claiming unfounded proofs of Nash equilibria, this study transparently documents the realities of online auction bidding: pervasive sniping, proxy bid compression, and the quantitative gap between first-price and second-price settlement rules on real historical bids.
