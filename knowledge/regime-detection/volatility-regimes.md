# Volatility Regimes — The Market Has Different Personalities

## The Four Regimes

Markets do not behave the same way all the time. They cycle through distinct volatility regimes, each requiring a completely different approach:

### 1. Low Volatility, Trending (VIX 10-15, clear direction)
The easiest environment to trade. Stocks drift higher with small pullbacks. Buy-the-dip works. Trend following works. Selling premium works. This regime rewards complacency — which is why it eventually kills you when it ends. Examples: 2017, most of 2019, much of 2021.

### 2. High Volatility, Trending (VIX 20-35, clear direction)
Hard but tradeable. The market is moving strongly in one direction but with violent swings along the way. Position sizing must shrink because daily ranges are 2-3x normal. Trend following still works but requires wider stops. Selling premium is dangerous because the swings can blow through strike prices. Examples: March-April 2020 (down), November 2020-February 2021 (up).

### 3. Low Volatility, Range-Bound (VIX 12-18, no direction)
Choppy and frustrating. The market goes nowhere but grinds in both directions. Trend followers get whipsawed. Mean reversion works well. Selling premium works because options decay faster than the market moves. The danger: this regime often precedes a breakout that trend followers miss because they have been beaten into submission. Examples: most of 2015, mid-2018.

### 4. High Volatility, Range-Bound (VIX 25-40+, no direction)
The most dangerous regime. Wild swings in both directions without sustained trend. Both trend following AND mean reversion fail. The correct strategy is to reduce size dramatically or sit in cash. This regime appears during genuine crises when the market cannot decide between recovery and further collapse. Examples: August-October 2011, Q4 2018, parts of 2022.

## Detecting the Current Regime

The agent should classify the current regime using:

1. **VIX level and trend.** VIX below 15 = low vol. Above 20 = elevated. Above 30 = high. But the TREND of VIX matters more than the level — VIX declining from 25 to 20 is very different from VIX rising from 15 to 20.

2. **Realized vs implied volatility.** When realized vol is lower than implied vol (VIX), the market is overpricing fear — this usually resolves by VIX declining. When realized vol exceeds implied vol, the market is underpricing risk — danger ahead.

3. **Average True Range (ATR) trends.** A 14-day ATR on SPY that is expanding signals volatility regime shift. Contracting ATR signals calming.

4. **Directional movement.** ADX above 25 suggests trending. Below 20 suggests range-bound. Combine with VIX classification for the four-quadrant regime map.

## Why Regime Detection Beats Indicator Optimization

Most traders spend their time optimizing indicators: should I use a 20-period or 50-period moving average? Should RSI be 14 or 21? This is the wrong question. The RIGHT question is: what regime am I in, and which strategy class works in this regime?

A 20-period MA crossover system will make money in a trending regime and lose money in a range-bound regime, regardless of the period length. No amount of parameter optimization fixes a strategy being deployed in the wrong regime.

## Strategy Mapping

| Regime | Works | Fails |
|--------|-------|-------|
| Low Vol Trend | Momentum, buy-the-dip, premium selling | Mean reversion (too early), tail hedging (bleeds) |
| High Vol Trend | Momentum (reduced size), breakouts | Premium selling (gamma risk), counter-trend |
| Low Vol Range | Mean reversion, premium selling, pairs | Momentum, breakouts (whipsaw) |
| High Vol Range | Cash, very selective pairs | Almost everything |

The agent should re-evaluate regime classification weekly and adjust strategy selection accordingly. Regime persistence (how long the current regime has lasted) is also informative — regimes tend to persist for months but end suddenly.
