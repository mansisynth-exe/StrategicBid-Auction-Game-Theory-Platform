# StrategicBid: Strategic Bidding in Online Auctions Using Game Theory

An end-to-end empirical and game-theoretic platform for analyzing historical online auctions, validating strategic behavior (late-bidding/sniping), and simulating counterfactual payment rules using authentic eBay auction records.

---

## 📌 Project Overview

**StrategicBid** bridges theoretical auction economics and real-world empirical bidding logs. Developed for **Game Theory for Data Science**, this platform uses verified historical records ($N = 10,681$ bids across $N = 628$ unique auctions) to:

1. **Empirically evaluate auction dynamics**: Quantify late bidding (sniping), opening bid reserve relationships, and commodity price distributions across Palm Pilot M515 PDAs, Xbox consoles, and Cartier wristwatches.
2. **Implement formal game-theoretic models**: Bayesian Nash Equilibrium in First-Price Sealed-Bid (FPSB) auctions and Weak Dominance of truthful bidding in Second-Price Sealed-Bid (SPSB / Vickrey) auctions.
3. **Execute counterfactual mechanism replays**: Re-simulate settlement prices under First-Price and Second-Price rules holding actual historical bids fixed, explicitly labeled to prevent confusing counterfactual replays with observed historical outcomes.
4. **Enforce scientific integrity**: Zero synthetic records, no mock fallbacks, transparent exclusion accounting, and deterministic privacy-preserving bidder pseudonymization.

---

## 🏛️ Dataset Citation & Provenance

All historical records derive from the official **Online Auctions Dataset** on Zenodo:
- **Title**: Online Auctions Dataset
- **Repository**: [Zenodo Record 11259259](https://zenodo.org/records/11259259)
- **DOI**: [10.5281/zenodo.11259259](https://doi.org/10.5281/zenodo.11259259)
- **License**: [Creative Commons Attribution 4.0 International (CC-BY-4.0)](https://creativecommons.org/licenses/by/4.0/)
- **Original Source**: Modeling Online Auctions Research Group ([modelingonlineauctions.com](http://www.modelingonlineauctions.com/datasets))
- **Cryptographic Hashes**:
  - `Online Auctions Dataset.zip`: `a25dfdd0c4204d9f1b62983c3991ed5deef18bfdfe10c534852749a242807e4b`
  - `auction.csv`: `c05d10bafd4f33aadb2c70ab562a23937bd11c8d32a7c73244c829c06302486e`
  - `swarovski.csv`: `def9ece464853db6e91c71e7f0eeb54853bec1872ef0da4df3984b1146bc0907`

---

## 🚀 Key Numerical Findings

All statistics derive strictly from authentic loaded records:
- **Sample Size**: 10,681 submitted bids across 628 unique auctions with 3,387 distinct bidders.
- **Closing Prices**: Mean \$348.01, Median \$227.50 (Standard Deviation \$507.03; range \$0.01 to \$5,400.00).
- **Sniping Prevalence**:
  - **14.8%** of all bids (1,585 bids) were submitted in the final 5 minutes of an auction.
  - **47.6%** of all auctions (299 of 628) experienced bids in the final 5 minutes.
  - **43.3%** of all auctions were won by bids submitted in the final 5 minutes.
- **Opening Bid Association**:
  - Pearson correlation $r = 0.584$ ($p < 0.001$), Spearman $\rho = 0.518$ ($p < 0.001$).
  - OLS regression slope: $\beta_1 = 0.814$ (95% CI: $[0.725, 0.903]$). Observational only; does not establish causality due to endogenous reserve setting.
- **Counterfactual Mechanism Replay ($N = 627$ eligible auctions)**:
  - Total Historical Observed Revenue: \$218,201.16 (Mean: \$348.01).
  - Total Counterfactual First-Price Revenue: \$218,218.16 (Mean: \$348.04).
  - Total Counterfactual Second-Price Revenue: \$210,531.61 (Mean: \$335.78).
  - Mean Payment Differential ($p_{FP} - p_{SP}$): +\$12.26 per auction (Median: +\$2.50).
  - Winner Alignment: 100.0% identical winners across mechanisms on real bids.
  - Exclusions: Exactly 1 auction (`3016587753`) excluded due to price (\$255.00) exceeding max recorded bid (\$5.00).

---

## 🏗️ Project Architecture

```
StrategicBid/
├── app.py                     # Streamlit Main Application & Overview Dashboard
├── requirements.txt           # Project Dependencies
├── README.md                  # Comprehensive Documentation
├── .gitignore                 # Version Control Ignore Rules
├── data/
│   ├── raw/                   # Immutable Raw Datasets (Online_Auctions_Dataset.zip)
│   ├── processed/             # Clean Processed Tables (clean_bids.csv, clean_auctions.csv)
│   └── metadata/              # Data Dictionary & Audit Results JSON
├── src/
│   ├── __init__.py            # Package Init
│   ├── data_loader.py         # Zenodo Ingestion & Integrity Verification
│   ├── data_validation.py     # Schema, Domain, and Pricing Validation
│   ├── preprocessing.py       # Salted SHA-256 Pseudonymization & Timing Calculations
│   ├── auctions.py            # Game-Theoretic Models & Mechanism Resolution Engines
│   ├── counterfactual_replay.py # Replay Logic & Differential Accounting
│   ├── empirical_analysis.py  # Statistical Regressions, Timing & Sniping Distributions
│   ├── metrics.py             # Presentation Formatting & KPI Helpers
│   ├── ui_helpers.py          # Streamlit UI Theme & Cached Data Loaders
│   └── reporting.py           # Automated Markdown Report Generator
├── pages/
│   ├── 1_Data_Explorer.py     # Interactive Filtering & Bid Sequence Inspection
│   ├── 2_Historical_Analysis.py # Empirical Visualizations & Sniping Dynamics
│   ├── 3_Auction_Mechanism_Lab.py # Single & Batch Mechanism Replay Simulator
│   ├── 4_Game_Theory.py       # Formal Mathematical Formulations & RL Feasibility
│   └── 5_Data_Quality.py      # Provenance, SHA-256 Hashes & Exclusion Case Study
├── tests/
│   ├── test_auctions.py       # Mechanism Resolution & Theoretical Benchmark Tests
│   ├── test_counterfactual_replay.py # Replay & Exclusion Accounting Tests
│   ├── test_data_validation.py # Schema & Anomaly Detection Tests
│   ├── test_empirical_analysis.py # Statistical & Missing-Data Error Handling Tests
│   └── test_preprocessing.py  # Pseudonymization & Timing Metric Tests
└── reports/
    └── project_report.md      # Auto-Generated Scientific Project Report
```

---

## ⚡ Installation & Quick Start

### 1. Prerequisites
- Python 3.10+ (Tested on Python 3.13)
- Windows, macOS, or Linux

### 2. Environment Setup
```bash
# Clone or navigate to the repository
cd StrategicBid

# Install dependencies
pip install -r requirements.txt
```

### 3. Run Automated Tests
Execute the full test suite (covers all 16 required verification cases):
```bash
python -m pytest tests/ -v
```
*Expected Result*: `26 passed in ~17s` (100% pass rate).

### 4. Launch Interactive Streamlit Dashboard
```bash
python -m streamlit run app.py
```
*(Or `streamlit run app.py` if your Python Scripts folder is added to `PATH`)*

Open your browser at `http://localhost:8501`.

---

## 🖥️ Dashboard Page Walkthrough

1. **Overview (`app.py`)**: Top-level genuine metrics, executive summary, commodity and auction coverage bar charts, and navigation overview.
2. **Data Explorer (`pages/1_Data_Explorer.py`)**: Multidimensional filtering by category, duration, and eligibility; auction summary tables; deep-dive chronological bid sequences with privacy-safe pseudonyms (`Bidder-XXXXXXXX`); CSV dataset export.
3. **Historical Analysis (`pages/2_Historical_Analysis.py`)**: Bid timing histograms, late-bidding (sniping) analysis in the final 5 minutes and 1 hour, opening bid vs. closing price OLS regression with confidence intervals and non-causal notice, and bidder participation intensity.
4. **Auction Mechanism Lab (`pages/3_Auction_Mechanism_Lab.py`)**: Batch mechanism comparison across 627 eligible auctions, interactive single-auction simulator displaying historical price vs. First-Price replay vs. Second-Price replay, and payment differential distributions.
5. **Game Theory (`pages/4_Game_Theory.py`)**: Formal mathematical formulations of First-Price BNE, Second-Price Weak Dominance proof matrix, Revenue Equivalence conditions, and a rigorous research-extension audit explaining why RL cannot be trained on observational logs without fabricating reward signals.
6. **Data Quality & Provenance (`pages/5_Data_Quality.py`)**: Cryptographic SHA-256 checksums, Zenodo metadata, complete 9-variable data dictionary, and detailed case study of anomalous auction `3016587753`.

---

## 🔒 Bidder Privacy & Deterministic Pseudonymization

Real eBay usernames are present in the raw data. To comply with ethical guidelines and privacy requirements:
- Raw usernames are **never** displayed in dashboard tables or exported files.
- Each username is deterministically hashed using salted SHA-256:
  $$\text{Pseudonym} = \text{"Bidder-"} + \text{SHA256}(\text{Salt} + \text{username})[0:8]$$
- This produces 3,387 unique 8-character hex identifiers with **zero collisions**, allowing cross-auction tracking while keeping usernames non-reversible.

---

## 🧪 Scientific Disclaimer

> **Counterfactual Replay Notice**:  
> Counterfactual replays calculate settlement amounts using static observed historical bid records. This is **not** an observed outcome under that mechanism. If an actual first-price mechanism had been in place, rational bidders would have shaded their bids, resulting in different submitted amounts.
