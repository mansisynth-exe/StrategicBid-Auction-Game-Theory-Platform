"""
pages/4_Game_Theory.py: Mathematical Foundations, Game-Theoretic Models, and Equilibrium Theory.
Formulates First-Price BNE, Second-Price Weak Dominance, Revenue Equivalence,
and rigorously addresses the research limitations of Reinforcement Learning in observational auction logs.
"""

import streamlit as st
import numpy as np
import plotly.graph_objects as go

from src.ui_helpers import (
    apply_theme,
    render_page_header,
    render_sidebar_metadata,
    apply_plotly_theme,
    NEU_PALETTE
)
from src.auctions import first_price_equilibrium_bid, calculate_shading_factor

st.set_page_config(
    page_title="Game Theory | StrategicBid",
    page_icon="📐",
    layout="wide"
)

apply_theme()
render_sidebar_metadata()

render_page_header(
    title="Game-Theoretic Auction Models & Equilibrium Foundations",
    subtitle="Formal mathematical specifications, equilibrium benchmarks, and theoretical vs. empirical distinctions.",
    tag="Theoretical Foundations"
)

# ==============================================================================
# SECTION 1: METHODOLOGICAL STATUS MATRIX
# ==============================================================================

st.markdown("### 🧭 Epistemological Separation: Theory vs. Empirics")

st.markdown(
    """
    To maintain scientific integrity, the table below delineates what can be mathematically proven,
    what is empirically observed in the eBay records, and what remains unobservable.
    """
)

st.markdown(
    """
    | Category | Description | Status in StrategicBid |
    |---|---|---|
    | **Theoretical Predictions** | Mathematical equilibria derived under axiomatic assumptions (e.g., $b^*(v) = \\frac{n-1}{n} v$). | **Formal Benchmark Only** |
    | **Empirical Observations** | Actual recorded bids, timestamps, feedback ratings, and historical closing prices. | **Directly Loaded Real Data** |
    | **Counterfactual Replays** | Re-simulation of payment rules holding historical bids fixed. | **Mechanical Simulation** |
    | **Unobservable Quantities** | True private valuations $v_i$, secret proxy ceilings, and off-equilibrium counterfactual bids. | **Scientifically Unidentifiable** |
    """
)

st.markdown("---")

# ==============================================================================
# SECTION 2: MODEL 1 - FIRST-PRICE SEALED-BID (FPSB) AUCTION
# ==============================================================================

st.markdown("### 1️⃣ Model 1: First-Price Sealed-Bid (FPSB) Auction")

st.markdown(
    r"""
    #### Mathematical Formulation
    Consider $n \ge 2$ symmetric, risk-neutral bidders competing for an indivisible object.
    Each bidder $i$ privately observes valuation $v_i$ independently drawn from a common prior distribution $F(v)$ on $[0, V]$.
    Bidders simultaneously submit non-negative sealed bids $b_i \ge 0$.

    **Payoff Function**:
    $$u_i(b_i, v_i) = \begin{cases} v_i - b_i & \text{if } b_i > \max_{j \neq i} b_j \\ \frac{v_i - b_i}{k} & \text{if tied with } k-1 \text{ bidders} \\ 0 & \text{if } b_i < \max_{j \neq i} b_j \end{cases}$$

    #### Bayesian Nash Equilibrium (BNE) Benchmark
    Under the standard assumption that valuations are uniformly distributed on $[0, V]$ ($F(v) = v/V$), the unique symmetric Bayesian Nash Equilibrium strategy is:
    $$b^*(v) = \left(\frac{n - 1}{n}\right) v$$
    """
)

# Interactive First-Price Equilibrium Visualizer
st.markdown("#### 🧮 Interactive FPSB Bid Shading Simulator (Theoretical Benchmark)")

sim_c1, sim_c2 = st.columns([1, 2])

with sim_c1:
    n_input = st.slider("Number of Symmetric Bidders (n):", min_value=2, max_value=20, value=5, step=1)
    v_input = st.slider("Hypothetical Private Valuation ($v):", min_value=10.0, max_value=1000.0, value=250.0, step=10.0)
    
    b_star = first_price_equilibrium_bid(v_input, n_input)
    shading_ratio = calculate_shading_factor(n_input)
    bidder_surplus = v_input - b_star

    st.markdown(
        f"""
        <div class="info-box">
            <strong>Equilibrium Values:</strong><br><br>
            • <strong>Equilibrium Bid b*(v)</strong>: ${b_star:.2f}<br>
            • <strong>Bid Shading Ratio</strong>: {shading_ratio:.3f} ({(1-shading_ratio)*100:.1f}% shaded)<br>
            • <strong>Expected Surplus</strong>: ${bidder_surplus:.2f}<br>
            • <strong>Formula</strong>: b = ({n_input}-1)/{n_input} × {v_input:.0f}
        </div>
        """,
        unsafe_allow_html=True
    )

with sim_c2:
    v_range = np.linspace(0, 500, 100)
    fig_bne = go.Figure()

    # Truthful line (45 degrees)
    fig_bne.add_trace(go.Scatter(
        x=v_range, y=v_range,
        mode="lines", name="Truthful Valuation Line (b = v)",
        line=dict(color="#6B7280", dash="dash")
    ))

    # Equilibrium curves for different n using Neumorphic Palette
    for comp_n, col in [(2, NEU_PALETTE[2]), (n_input, NEU_PALETTE[0]), (10, NEU_PALETTE[1])]:
        b_curve = ((comp_n - 1) / comp_n) * v_range
        fig_bne.add_trace(go.Scatter(
            x=v_range, y=b_curve,
            mode="lines",
            name=f"BNE Strategy (n = {comp_n})",
            line=dict(color=col, width=3 if comp_n == n_input else 1.5)
        ))

    fig_bne.update_layout(
        title="Theoretical First-Price Bid Functions vs. Valuation",
        xaxis_title="Private Valuation v ($)",
        yaxis_title="Equilibrium Submitted Bid b(v) ($)",
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
    )
    fig_bne = apply_plotly_theme(fig_bne)
    st.plotly_chart(fig_bne, use_container_width=True)

st.markdown(
    """
    > **⚠️ Scientific Boundary**:  
    > In the historical eBay dataset, true private valuations are unobserved.
    > Substituting eBay proxy bids into the FPSB equilibrium formula and claiming to 'test' or 'validate'
    > Nash Equilibrium is mathematically fallacious and scientifically invalid.
    """
)

st.markdown("---")

# ==============================================================================
# SECTION 3: MODEL 2 - SECOND-PRICE SEALED-BID (SPSB / VICKREY) AUCTION
# ==============================================================================

st.markdown("### 2️⃣ Model 2: Second-Price Sealed-Bid (SPSB / Vickrey) Auction")

st.markdown(
    r"""
    #### Mathematical Formulation
    In a standard Second-Price Sealed-Bid auction, the highest bidder wins the object, but pays a price equal to the second-highest submitted bid:
    $$p = \max_{j \neq i} b_j$$

    **Payoff Function for Bidder $i$**:
    $$u_i(b_i, v_i) = \begin{cases} v_i - \max_{j \neq i} b_j & \text{if } b_i > \max_{j \neq i} b_j \\ 0 & \text{if } b_i < \max_{j \neq i} b_j \end{cases}$$

    #### Proof of Weak Dominance of Truthful Bidding
    Let $B = \max_{j \neq i} b_j$ denote the highest competing bid from other players.
    Regardless of $B$ (which bidder $i$ does not control):

    | Case | Bidder Submits $b_i = v_i$ | Bidder Over-bids $b_i > v_i$ | Bidder Under-bids $b_i < v_i$ |
    |---|---|---|---|
    | **$B < v_i$** | Wins, payoff $v_i - B > 0$ | Wins, payoff $v_i - B > 0$ (Identical) | If $B < b_i$: wins, payoff $v_i - B > 0$.<br>If $B > b_i$: **loses, payoff $0$ (Worse)** |
    | **$B = v_i$** | Tied / zero surplus ($0$) | Tied / zero surplus ($0$) | Loses, zero surplus ($0$) |
    | **$B > v_i$** | Loses, payoff $0$ | If $B > b_i$: loses, payoff $0$.<br>If $B < b_i$: **wins, payoff $v_i - B < 0$ (Worse)** | Loses, payoff $0$ (Identical) |

    **Conclusion**: Truthful bidding $b_i = v_i$ weakly dominates any deviating bid $b_i \neq v_i$ in all states of the world under IPV.
    """
)

st.markdown("---")

# ==============================================================================
# SECTION 4: REVENUE EQUIVALENCE THEOREM
# ==============================================================================

st.markdown("### 3️⃣ Revenue Equivalence Theorem (RET)")

st.markdown(
    r"""
    Under the following four benchmark conditions:
    1. **Risk Neutrality**: Bidders and seller are risk-neutral.
    2. **Independent Private Values (IPV)**: Bidders' valuations are drawn i.i.d. from a strictly increasing continuous distribution.
    3. **Symmetry**: Bidders draw from identical priors and use symmetric equilibrium strategies.
    4. **Zero Surplus at Bottom**: The lowest possible valuation type expects zero surplus.

    **Theorem (Vickrey, 1961; Riley & Samuelson, 1981)**:
    $$\mathbb{E}[R_{FPSB}] = \mathbb{E}[R_{SPSB}] = \left(\frac{n-1}{n+1}\right) V$$

    #### Why RET Does Not Hold in Empirical Online Auctions:
    - **Dynamic Timing & Sniping**: eBay auctions are not one-shot sealed-bid games. They are ascending proxy auctions where information arrives sequentially over days.
    - **Common Value Elements**: Electronics and collectibles have affiliated resale values, introducing the Winner's Curse.
    - **Risk Aversion**: Bidders are frequently risk-averse, bidding higher in first-price auctions than the risk-neutral benchmark.
    - **Discretionary Minimum Increments & Reserve Prices**: Non-zero reserve prices and platform increments distort mechanical equivalence.
    """
)

st.markdown("---")

# ==============================================================================
# SECTION 5: MODEL 4 - RESEARCH EXTENSION: REINFORCEMENT LEARNING LIMITATIONS
# ==============================================================================

st.markdown("### 4️⃣ Model 4 (Research Extension): Feasibility of Adaptive / RL Bidding")

st.markdown(
    """
    <div class="disclaimer-banner">
        <strong>⚠️ SCIENTIFIC BOUNDARY & RL FEASIBILITY AUDIT:</strong><br>
        In accordance with strict empirical requirements, an artificial reinforcement learning agent
        has <strong>NOT</strong> been trained on fabricated rewards or synthetic utility signals.
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    #### Why Reinforcement Learning Cannot Be Scientifically Identified From Observational Bidding Logs:
    1. **Absence of True Reward Signal**: In reinforcement learning, an agent optimizes cumulative reward:
       $$R_t = u(v, b, p) = (v - p) \cdot \mathbb{I}(\text{win})$$
       In historical auction logs, private valuation $v$ is strictly unobservable. Inventing an arbitrary valuation
       or assuming $v = \text{closing\_price}$ converts the experiment into an artificial tautology.
    2. **Counterfactual Action Indeterminacy (Off-Policy Evaluation)**:
       If an agent chooses an action $b' \neq b_{\text{observed}}$, the historical competitors would have received
       different feedback and placed different counter-bids. A static log cannot simulate dynamic multi-agent reactions.
    3. **Partial Information in Proxy Records**:
       The dataset records proxy bids and the winning price ($second + increment$). It does not observe
       bidders who intended to bid but refrained after observing the current high price.

    #### Requirements for a Legitimate Future RL Bidding Environment:
    - **Agent-Based Market Simulation**: An explicitly simulated multi-agent environment where valuation distributions $F(v)$ are controlled and known.
    - **Interactive Bidding Environment**: An OpenAI Gym / PettingZoo environment with explicit step dynamics, state spaces $[t, \text{current\_price}, \text{bid\_count}]$, and action spaces $[\text{submit\_bid}(amount)]$.
    - **Ablation Baseline**: Comparing adaptive Q-learning / PPO against formal theoretical benchmarks ($b^*(v) = \frac{n-1}{n} v$ and $b^*(v) = v$).
    """
)
