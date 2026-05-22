# Correlation Regimes — When Everything Moves Together, Run

## The Normal State

In healthy, functioning markets, individual stocks and sectors move semi-independently. Technology can rise while energy falls. Banks can rally while utilities lag. This independent movement is what makes diversification work — owning assets that do not move in lockstep reduces portfolio volatility.

The average pairwise correlation among S&P 500 stocks in normal markets is around 0.25-0.35. This means individual stocks share about 25-35% of their movement with each other, and the rest is driven by company-specific factors.

## When Correlations Spike

During market stress, correlations surge toward 1.0. In the 2008 financial crisis, average pairwise correlations among S&P 500 stocks exceeded 0.80. During the March 2020 COVID crash, correlations hit similar extremes within days.

When correlations go to 1, several things break simultaneously:

1. **Diversification fails.** Your "diversified" portfolio of tech, healthcare, industrials, and consumer stocks drops in unison. The portfolio you thought had independent bets turns out to be one bet: long equities.

2. **Risk models break.** VaR (Value at Risk) and similar models assume historical correlation structures. When correlations spike, actual risk is 2-5x what models predicted.

3. **Liquidity disappears.** In a correlated sell-off, everyone is selling everything simultaneously. Bid-ask spreads widen. Market makers step back. The stocks you want to sell cannot be sold at reasonable prices.

4. **Only genuine hedges work.** Long puts, short futures, long volatility positions — instruments with negative correlation to equities — are the only things that offset losses. Sector rotation does not help when everything is falling together.

## Correlation Structures as Regime Indicators

The current correlation structure tells you what regime the market is in:

- **Low correlation, mixed sector performance:** Normal, stock-picker's market. Individual analysis and position selection matter most.
- **Rising correlation, everything going up:** Euphoria. Money is flooding in indiscriminately. Quality and junk rally together. This is the late-cycle melt-up. Easy money but dangerous — when it reverses, it reverses hard.
- **High correlation, everything going down:** Crisis mode. Preserve capital. The only question is whether to hedge, raise cash, or wait it out.
- **Falling correlation from high levels:** Recovery. The market is starting to differentiate again. Early movers begin outperforming. Stock selection starts to matter again.
- **Unusual sector divergence (growth vs value splitting):** Thematic regime. The market has a strong narrative driving one group while another languishes. Track which side of the divergence has fundamental support.

## Measuring Correlation

For the agent:
- Calculate rolling 20-day pairwise correlation among sector ETFs (XLK, XLF, XLE, XLV, XLU, etc.). This is computationally simpler than individual stock correlations and captures the regime signal.
- Track the CBOE Implied Correlation Index (ICJ for S&P 500, JCJ for DJIA). These measure the correlation implied by index options vs individual stock options.
- Monitor the spread between index implied volatility and average single-stock implied volatility. When index IV is high relative to single-stock IV, the market is pricing in correlated movement.

## The Dispersion Trade

When correlations are high and you believe they will decline (crisis is resolving), the professional trade is "selling correlation" — going long individual stock options and short index options. This profits from the return to normal dispersion. It is complex to implement but understanding the concept helps the agent identify when diversification is about to start working again.

## Key Threshold

Average sector correlation above 0.70 = defensive mode. Below 0.40 = stock-picker mode. Between 0.40-0.70 = normal. Track the direction, not just the level.
