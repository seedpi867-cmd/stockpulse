# Mean Reversion Strategy

## Core Principle

Mean reversion is built on the statistical tendency for prices to return to their long-term average after extreme moves. When a stock drops 3 standard deviations below its 50-day mean, the probability of a bounce within 5 days exceeds 70% historically. The challenge is distinguishing temporary dislocations from permanent repricing.

## The Statistical Foundation

Markets exhibit mean-reverting behavior across multiple timeframes but the effect is strongest at extremes. Research by DeBondt and Thaler (1985) showed that stocks with the worst 3-year returns subsequently outperformed the best performers by an average of 25% over the next 3 years. At shorter timeframes, Connors and Alvarez demonstrated that buying stocks with RSI(2) below 5 and selling above 95 generated consistent edge from 2001-2012.

## Entry Signals

- **Bollinger Band Extremes:** Price touching or penetrating the lower band (2 standard deviations below 20-day SMA) while the band width is expanding signals potential mean reversion. The key is waiting for a close back inside the bands before entering.
- **RSI(2) Below 10:** Short-term RSI at extreme oversold levels in stocks that are above their 200-day moving average — this filters for temporary pullbacks in uptrending stocks rather than falling knives.
- **Z-Score:** Calculate the z-score of current price vs. 50-day mean. Entries below -2.0 with a catalyst for recovery (earnings not involved, sector not in structural decline) offer the best risk/reward.

## When It Fails

Mean reversion is devastating during regime changes. Buying "cheap" bank stocks in September 2008, oil stocks in 2014, or retail stocks in 2020 based on historical mean reversion signals would have compounded losses. The key filter is fundamental: is the business model intact? If revenue is structurally impaired, there is no mean to revert to.

## Position Management

Scale into mean reversion trades — enter 1/3 position at first signal, add 1/3 if price drops another standard deviation, final 1/3 at extreme. This gives a better average entry while capping total risk. Set stops 1.5x ATR below the lowest entry point. Take profits when price returns to the 20-day moving average (partial) and the 50-day (remainder).

## Pairs Trading Variant

A market-neutral version: identify two correlated stocks (correlation > 0.80 over 60 days), calculate the spread, and trade when the spread exceeds 2 standard deviations from its mean. Go long the underperformer, short the outperformer. This removes market direction risk and isolates the reversion signal. Classic pairs include XOM/CVX, JPM/BAC, GOOGL/META.

## Key Statistics

Mean reversion strategies typically show win rates of 60-70% with modest per-trade gains (1-3%) and tight stops. The edge compounds through volume of trades. Drawdowns tend to be sharper but shorter than momentum strategies. Annual returns of 8-15% with Sharpe ratios above 1.0 are achievable for well-filtered implementations.
