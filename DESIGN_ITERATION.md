# Design Iteration History

This document records the evolution of the Stock Analysis System from v1 prototype to the current v2 release.

## v1: The "Black Box" Prototype
**Goal**: Build a basic technical analysis tool that aggregates multiple indicators into a single score.

### Features
*   **Data Fetching**: Retrieves stock data from Yahoo Finance.
*   **Basic Indicators**: Calculates MACD, RSI, and Bollinger Bands.
*   **Simple Scoring**: Returns a single number (0-10) based on the average of technical signals.
    *   *Algorithm*: `Score = Average(Technical_Signals) * 10`
    *   Bullish = 1, Bearish = -1, Neutral = 0.

### 🛑 User Feedback & Pain Points (Research Phase)
After conducting user testing with 5 alpha testers, we received the following feedback:

1.  **"It's a Black Box"**: Users saw a score of "6.5" but didn't trust it. They asked: *"Why is it 6.5? Is it because of the trend or the volume?"*
    *   *Insight*: Users need **transparency** and **explainability**.
2.  **"Market Context Missing"**: One user bought a high-scoring stock during a market crash and lost money. They complained: *"The stock was fine, but the market was terrible. The score didn't warn me."*
    *   *Insight*: The scoring algorithm must account for **Market Environment (Bull/Bear Regime)**.
3.  **"Too Much Text"**: The initial analysis was just a wall of text.
    *   *Insight*: Need structured visualization (tables, colored tags).

---

## v2: The "Transparent AI" Update (Current)
**Goal**: Address user feedback by adding granular breakdowns, market context, and better visualization.

### Key Improvements (Based on Feedback)

#### 1. Explainable AI Scoring (Addressing "Black Box")
*   **Change**: Decomposed the single score into 6 distinct dimensions:
    *   Trend Score (33%)
    *   Technical Score (28%)
    *   Pattern Score (18%)
    *   Market Environment (9%)
    *   Trend Position (7%)
    *   Volume Modifier (5%)
*   **UI Update**: Added a **Radar Chart** (Spider Web) to visualize strengths and weaknesses.
*   **UI Update**: Added a "Score Breakdown" table showing exactly how points were calculated.

#### 2. Market Environment Correction (Addressing "Market Context")
*   **Change**: Introduced `calculate_market_environment_score()`.
*   **Logic**:
    *   If Market is **Bearish**: Penalty factor applied to all long scores.
    *   If Market is **Bullish**: Bonus factor applied.
*   **Impact**: A stock with good technicals (8.0) might be downgraded to (6.5) if the broader market index (S&P 500 / CSI 300) is crashing.

#### 3. Structured Visuals
*   **Change**: Replaced raw text summaries with structured tables for "Support/Resistance", "Candlestick Patterns", and "Technical Signals".
*   **UI**: Used color coding (Green/Red) for Bullish/Bearish signals instantly.

---

### How to Compare
*   **v1 (Legacy Branch)**: Simple average score, no market context, no breakdown.
*   **v2 (Main Branch)**: Weighted multi-factor score, market regime analysis, radar charts, and detailed explainability.
