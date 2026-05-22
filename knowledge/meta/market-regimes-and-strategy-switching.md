# Market Regimes and Strategy Switching — The Meta-Strategy

## The Core Problem

No single trading strategy works in all market environments. Momentum strategies print money in trending markets and get slaughtered in range-bound markets. Mean reversion strategies thrive in ranges and get destroyed in trends. Volatility selling works in calm markets and blows up accounts when vol spikes. Defensive strategies preserve capital in crashes but massively underperform in rallies.

Every strategy has a regime where it excels and a regime where it fails. The naive approach — picking one strategy and sticking with it — guarantees periods of severe underperformance or drawdown when the regime shifts. The professional approach is the meta-strategy: detect the current regime, deploy the strategy that works in that regime, and switch when the regime changes.

## The Regime Framework

Combining the indicators from the regime-detection knowledge files, the agent should classify markets into these operating regimes:

### Regime 1: Bull Trend (Low Vol)
**Detection:** VIX below 18, ADX above 25 (trending), S&P 500 above rising 50-day and 200-day MA, breadth confirming (A/D line at highs), net liquidity expanding or stable.

**Strategy:** Momentum / trend following. Buy strength. Add to winners. Trail stops. Maintain 80-100% equity exposure. Favor sectors with strongest relative strength.

**Risk:** Complacency. This regime feels safe and can end suddenly. The transition to Regime 3 or 4 is the most dangerous because traders are fully invested and psychologically unprepared.

### Regime 2: Bull Trend (High Vol)
**Detection:** VIX 20-35, ADX above 25, S&P 500 above 200-day MA but swinging violently, liquidity neutral or mildly positive.

**Strategy:** Reduced momentum. Maintain directional exposure but reduce position sizes by 30-50%. Wider stops to avoid being shaken out. Focus on highest-quality names (strong balance sheets, earnings beats + raises). Avoid leverage.

**Risk:** Drawdowns within the uptrend. Daily swings of 2-3% are normal in this regime. Position sizing must account for this or stops will be triggered constantly.

### Regime 3: Bear Trend (High Vol)
**Detection:** VIX above 25, ADX above 25 (trending down), S&P 500 below declining 50-day and 200-day MA, breadth deteriorating, net liquidity contracting.

**Strategy:** Defensive / cash-heavy. Reduce equity exposure to 20-40%. Raise cash. If the agent can go short, selective short positions in the weakest sectors. Long positions only in traditional safe havens (Treasuries, utilities, consumer staples) or genuine hedges (put options, VIX calls). No buying the dip — the dip is the trend.

**Risk:** Bear market rallies. Bear markets produce violent short-covering rallies (5-15% in days) that can devastate short positions and trick traders into thinking the bottom is in. Maintain discipline.

### Regime 4: Range-Bound (Low Vol)
**Detection:** VIX 12-18, ADX below 20 (no trend), S&P 500 oscillating between defined support and resistance, mixed breadth signals.

**Strategy:** Mean reversion. Buy near range support, sell near range resistance. Sell premium (covered calls, cash-secured puts). Pairs trades. Position sizes can be moderate because volatility is low, but directional conviction should be low.

**Risk:** Breakout. Ranges eventually break, and mean reversion traders who have been trained by the range to sell strength and buy weakness get caught on the wrong side of the breakout. Set alerts at range boundaries.

### Regime 5: Range-Bound (High Vol)
**Detection:** VIX above 25, ADX below 20, S&P 500 swinging wildly within a range, correlations elevated, conflicting signals.

**Strategy:** Cash. This is the most dangerous regime. Both trend following and mean reversion fail because the market whipsaws violently without establishing direction. Reduce exposure to 10-20%. Only take trades with exceptional setups and tight risk. Accept that sitting in cash during this regime is not underperformance — it is survival.

**Risk:** Opportunity cost. This regime can persist for weeks or months. The pressure to "do something" is enormous (see when-to-do-nothing.md). Resist it.

## The Transition Problem

The hardest part of regime-based strategy switching is managing transitions. Regimes do not change with a clear announcement. They morph gradually, and the detection is always lagging.

Solutions:
1. **Use a confirmation period.** Do not switch strategies on the first signal of regime change. Require 5-10 trading days of consistent regime-change signals before adjusting.
2. **Gradual transitions.** Do not go from 100% trending strategy to 100% mean reversion overnight. Shift allocation: 80/20, then 60/40, then 40/60 as confidence in the new regime grows.
3. **Maintain a core allocation.** Keep 20-30% of the portfolio in regime-neutral positions (high-quality dividend stocks, short-term bonds) that perform acceptably across all regimes.

## For the Agent

- Run regime classification daily
- Maintain a regime history log — track how long the current regime has persisted and what the previous regime was
- Execute strategy switches gradually over 5-10 trading days
- Track performance by regime — which strategies worked in which regimes?
- The meta-metric: regime detection accuracy. If the agent correctly identifies regimes 65%+ of the time, the strategy switching framework will outperform any single strategy significantly
- Accept that some transitions will be detected late and some regime classifications will be wrong. The framework does not need to be perfect — it needs to be right more often than wrong and avoid catastrophic losses during regime 3 and regime 5
