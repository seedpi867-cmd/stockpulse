# Position Correlation — Five Stocks Is Not Diversification

## The Illusion

A trader holds Apple, Microsoft, NVIDIA, Amazon, and Google. Five different companies. Five different business models. Five positions. Diversified, right?

Wrong. These five stocks share: exposure to the technology sector, sensitivity to interest rates, dependence on digital advertising and cloud spending, high beta to NASDAQ, and extreme correlation to each other during market stress. In a tech sell-off, all five drop together. The trader does not have five positions — they have one large position (long mega-cap tech) wearing five different names.

This is the most common diversification mistake, and it has destroyed more portfolios than any single bad trade.

## Measuring Real Portfolio Risk

Portfolio correlation analysis reveals your actual risk exposure:

1. **Pairwise correlation matrix.** Calculate the rolling 60-day correlation between every pair of positions. If all correlations are above 0.70, your "diversified" portfolio is effectively one concentrated bet.

2. **Portfolio beta decomposition.** How much of your portfolio's daily return is explained by SPY (market beta), QQQ (tech beta), and sector ETFs? If 85% of variance is explained by QQQ, you are running a leveraged tech bet regardless of how many individual stocks you hold.

3. **Factor exposure analysis.** Are all your positions long growth, long momentum, short value? Then a factor rotation (growth to value) will hit every position simultaneously.

4. **Stress test with historical scenarios.** Apply March 2020 returns, Q4 2018 returns, or the 2022 tech drawdown to your current portfolio. If every position drops simultaneously in historical stress scenarios, your diversification is an illusion.

## What Real Diversification Looks Like

True diversification requires positions that respond differently to the same market event:

- **Asset class diversification:** Equities, bonds, commodities, cash. These have structurally different drivers.
- **Sector diversification:** If you must be all-equity, spread across sectors with different economic sensitivities. Energy and tech often move inversely.
- **Factor diversification:** Own some growth and some value. Some momentum and some mean reversion. Some high beta and some low beta.
- **Geographic diversification:** US and international equity markets do not move in lockstep over medium-term periods (they do in crises, see correlation-regimes.md).
- **Time horizon diversification:** Some positions are short-term trades, some are long-term holds. They respond to different catalysts.

## The Correlation Trap in Practice

Real-world examples of hidden correlation:
- **Long 5 bank stocks:** one position — long financials, short credit quality
- **Long tech + long crypto:** one position — long speculation, long liquidity
- **Long REITs + long utilities:** one position — long yield, short interest rates
- **Long oil stocks + short airline stocks:** feels hedged but both are oil price bets with different signs, and the correlation can break
- **Long US growth + long European growth:** looks geographic but the factor exposure is identical

## Risk Multiplier Effect

If you have 5 positions, each sized at 20% of portfolio, and their average pairwise correlation is 0.80, your portfolio risk is approximately equivalent to a SINGLE position sized at 90% of portfolio. The math: portfolio volatility scales with correlation. High correlation means the portfolio behaves like a concentrated bet.

The correction: either reduce correlation by genuinely diversifying, or reduce position sizes to match the actual risk you are running.

## For the Agent

- Calculate portfolio correlation matrix weekly
- Flag any pair of positions with correlation > 0.75 as "redundant risk"
- Calculate the effective number of independent bets (1 / sum of squared portfolio weights adjusted for correlation)
- When adding a new position, calculate its correlation to existing portfolio BEFORE entering
- Reject new positions that increase portfolio correlation above threshold unless there is a compelling reason and position size is reduced accordingly
