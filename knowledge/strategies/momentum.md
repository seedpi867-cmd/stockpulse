# Momentum Trading Strategy

## Core Principle

Momentum trading exploits the empirical tendency for assets that have performed well recently to continue performing well in the near term, and for losers to keep losing. This is one of the most robust anomalies in finance, documented by Jegadeesh and Titman (1993) across decades of data and multiple asset classes.

## How It Works

The classic momentum strategy ranks stocks by their returns over the past 3-12 months (the "formation period"), goes long the top decile and short the bottom decile, then holds for 1-6 months (the "holding period"). The sweet spot historically has been a 12-month lookback with a 1-month holding period, excluding the most recent month (which tends to exhibit short-term reversal).

## Key Metrics

- **Relative Strength Index (RSI):** Measures speed and magnitude of price changes. Above 70 signals overbought, below 30 oversold — but in strong momentum regimes, RSI can stay above 70 for weeks.
- **Rate of Change (ROC):** Simple percentage change over N periods. A 10-day ROC above 5% with expanding volume is a momentum confirmation.
- **Moving Average Crossovers:** The 50-day crossing above the 200-day ("golden cross") is a widely watched momentum signal, though by the time it triggers, 30-40% of the move may already be priced in.
- **ADX (Average Directional Index):** Readings above 25 indicate a trending market where momentum strategies thrive. Below 20 suggests range-bound conditions where momentum gets chopped up.

## When Momentum Works

Momentum performs best in trending markets with moderate volatility. It tends to deliver strong returns during the middle portion of bull markets and during sustained selloffs. The strategy struggled most during sharp reversals — the "momentum crash" of 2009 (March reversal) saw the long-short momentum portfolio lose over 40% in three months as beaten-down financials snapped back violently.

## Risk Management

Position sizing is critical. Never allocate more than 2-3% of capital to a single momentum name. Use trailing stops of 2-3x ATR (Average True Range) to protect profits without getting stopped out by normal volatility. Cut losers fast — if a momentum stock drops below its 20-day moving average on heavy volume, the thesis is likely broken.

## Practical Implementation

Screen for stocks making new 52-week highs with relative volume above 1.5x average. Look for orderly pullbacks to the 10 or 21-day EMA as entry points rather than chasing breakouts. The best momentum trades show increasing volume on up days and decreasing volume on pullbacks — this pattern indicates institutional accumulation.

Momentum factor returns have averaged 6-8% annually above market returns since 1927, though with significant drawdown risk during regime changes. The strategy requires discipline to hold winners and cut losers, which runs counter to most traders' natural instincts.
