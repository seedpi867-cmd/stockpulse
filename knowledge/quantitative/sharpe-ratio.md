# Sharpe Ratio and Risk-Adjusted Performance

## Definition

The Sharpe ratio, developed by Nobel laureate William Sharpe in 1966, measures return per unit of risk. It is the most widely used metric for comparing investment strategies on a risk-adjusted basis.

Formula: Sharpe = (Rp - Rf) / StdDev(Rp)

Where Rp = portfolio return, Rf = risk-free rate, and StdDev(Rp) = standard deviation of portfolio returns. A higher Sharpe ratio means better risk-adjusted performance.

## Interpreting Sharpe Ratios

**Below 0.5:** Poor risk-adjusted returns. The strategy is not adequately compensating for the volatility it generates. Many retail traders fall here because large losses create high standard deviation even if average returns are positive.

**0.5 to 1.0:** Acceptable. The S&P 500 has historically delivered a Sharpe ratio of approximately 0.4-0.6 over most rolling 10-year periods. A strategy in this range is roughly matching the market on a risk-adjusted basis.

**1.0 to 2.0:** Good to excellent. Most successful hedge funds target Sharpe ratios of 1.0-1.5. Renaissance Technologies Medallion Fund, widely considered the most successful fund in history, reportedly achieved Sharpe ratios above 2.0 net of fees over decades.

**Above 2.0:** Exceptional and rare. Sustained Sharpe ratios above 2.0 are extremely difficult to achieve and often indicate either overfitting to historical data, survivorship bias, or a genuinely exceptional strategy. Be skeptical of backtests showing Sharpe above 3.0 — they almost certainly do not hold out of sample.

## Limitations

**Assumes normal distribution:** The Sharpe ratio treats upside and downside volatility equally. A strategy that has occasional large gains and consistent small losses may have the same Sharpe as one with consistent small gains and occasional large losses — but these have very different risk profiles. The Sortino ratio (which only penalizes downside deviation) addresses this.

**Sensitive to timeframe:** A strategy can show a Sharpe of 2.0 over one year and 0.8 over five years. Always evaluate over multiple timeframes and at least 3-5 years of data. Monthly Sharpe ratios (annualized by multiplying by the square root of 12) can differ significantly from daily Sharpe ratios (annualized by the square root of 252) due to serial correlation effects.

**Ignores tail risk:** A strategy selling far out-of-the-money options (like the infamous short volatility trade) can show a high Sharpe ratio for years — until a tail event causes catastrophic losses. XIV, the inverse VIX ETN, had an excellent Sharpe ratio from 2012 to February 2018 when it lost 96% in a single day during Volmageddon.

## Practical Use for Traders

Use the Sharpe ratio to compare your strategies against each other and against benchmarks. Track your rolling 3-month and 12-month Sharpe ratio. If your 12-month Sharpe drops below 0.5, re-evaluate whether the strategy still has edge or if market conditions have changed.

When allocating capital between multiple strategies, weight allocation proportionally to each strategy Sharpe ratio (this is the basis of mean-variance optimization). A strategy with Sharpe 1.5 should receive more capital than one with Sharpe 0.8.

For portfolio construction, combining uncorrelated strategies (each with modest individual Sharpe ratios of 0.7-1.0) can produce a combined portfolio Sharpe of 1.5 or higher. This diversification benefit is why professional firms run multiple strategies simultaneously rather than concentrating capital in their best single strategy.
