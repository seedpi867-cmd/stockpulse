# Simulation vs Reality — Backtests Lie, and They Lie Consistently

## The Gap

Every backtest produces results that are better than live trading. This is not a possibility — it is a certainty. The gap between simulated and actual performance has destroyed more quant funds and systematic traders than any single market event.

A strategy that backtests at 60% win rate and 2:1 reward-to-risk will likely deliver 48-52% win rate and 1.5-1.7:1 reward-to-risk in live trading. This may not sound catastrophic, but for a strategy designed to be marginally profitable at 60%/2:1, the real-world numbers often mean net losses after costs.

## Why Backtests Overstate

### 1. Survivorship Bias
Your universe of stocks includes only those that exist today. Companies that went bankrupt, were delisted, or were acquired are often excluded from historical databases. This means your backtest never encounters the worst-case scenarios — the stocks that went to zero. You only test against survivors.

Impact: overstates returns by 1-3% annually, depending on time period and universe.

### 2. Look-Ahead Bias
Subtle and pernicious. Your backtest "knows" that a company's earnings were eventually restated, that a data revision occurred, or that a stock split happened. Real-time data is messier, delayed, and sometimes wrong. Point-in-time databases exist to address this but are expensive and imperfect.

Impact: variable but can be enormous for fundamental strategies that rely on financial data.

### 3. Slippage
The backtest assumes you buy at the close price or the mid-price. In reality, you buy at the ask (or worse, you move the ask by placing a large order). The difference between theoretical execution and actual execution is slippage. For liquid large-caps, slippage is small (1-5 basis points). For small-caps, illiquid names, or volatile markets, slippage can be 20-100+ basis points per trade.

Impact: proportional to turnover. A strategy that trades weekly with 50bps round-trip slippage loses 26% annually to execution costs alone.

### 4. Market Impact
Your backtest trades have zero market impact — they execute at historical prices without moving them. In reality, a $100,000 buy order in a stock that trades $500,000 daily will move the price against you. Larger funds face this problem severely — a $10 million order in a mid-cap stock can take days to fill and moves the stock 1-2% during execution.

Impact: proportional to position size relative to average daily volume. The backtest scales perfectly; reality does not.

### 5. Transaction Costs
Commissions, exchange fees, regulatory fees, and borrowing costs for short positions. Many backtests use zero or understated transaction costs. Even in the era of "zero commission" retail trading, there are indirect costs through payment for order flow and wider spreads for retail orders.

Impact: 0.5-2% annually depending on turnover and trade size.

### 6. Overfitting
The most dangerous bias. By testing many variations of a strategy and selecting the one with the best backtest results, you are fitting to noise rather than signal. A strategy with 20 parameters tested across 1,000 combinations will produce impressive backtests — but the "optimal" parameters are tuned to historical noise that will not repeat.

Impact: potentially total. An overfit strategy can have zero or negative real edge despite stunning backtest returns.

### 7. Regime Changes
The past is not the future. A strategy optimized for 2010-2020 (low rates, low vol, QE-supported markets) may perform poorly in a different regime (rising rates, high vol, quantitative tightening). The backtest shows what DID work, not what WILL work.

## The Pessimism Margin

Build an explicit pessimism adjustment into every backtest:

| Metric | Backtest | Expected Live (adjustment) |
|--------|----------|---------------------------|
| Win Rate | 60% | 50-54% (-10-15% relative) |
| Avg Win/Avg Loss | 2.0 | 1.5-1.7 (-15-25% relative) |
| Max Drawdown | -15% | -20 to -25% (1.5-1.7x worse) |
| Annual Return | 20% | 10-14% (50-70% of backtest) |
| Sharpe Ratio | 1.5 | 0.8-1.1 (50-70% of backtest) |

If the strategy is not profitable AFTER applying the pessimism margin, it is not a real edge — it is a backtest artifact.

## For the Agent

- Apply the pessimism margin to ALL strategy evaluations before deployment
- Track live vs backtest performance divergence. If live consistently underperforms backtest by more than the expected margin, the strategy may be overfit or the edge may have decayed
- Minimize the number of tunable parameters to reduce overfitting risk
- Use out-of-sample testing: develop on data through 2020, validate on 2021-2023, paper trade on current data
- Prefer simple strategies with fewer parameters over complex strategies with better backtests — simplicity is robustness
