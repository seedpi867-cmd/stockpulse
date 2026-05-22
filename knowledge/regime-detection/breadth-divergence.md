# Breadth Divergence — When the Generals March Alone

## The Concept

Market breadth measures how many stocks are participating in a market move. When the index rises and the majority of stocks are also rising, the rally has broad participation — it is healthy. When the index rises but fewer and fewer stocks participate, the rally is narrowing. Narrow rallies are built on a fragile foundation and eventually fail.

The advance/decline line is the simplest breadth measure: cumulative sum of (advancing stocks minus declining stocks) each day. When the A/D line makes new highs alongside the index, breadth confirms the trend. When the index makes new highs but the A/D line does not, that is a breadth divergence — and it is one of the most reliable warning signals in technical analysis.

## The 2021 Case Study

The S&P 500 hit all-time highs throughout 2021, powered by a handful of mega-cap tech stocks (Apple, Microsoft, Alphabet, Amazon, NVIDIA, Tesla). Meanwhile:

- By November 2021, over 40% of NASDAQ stocks were already down 20% or more from their 52-week highs — in a bear market — while the index was at all-time highs.
- The percentage of S&P 500 stocks trading above their 200-day moving average peaked in April 2021 at about 95% and had declined to roughly 65% by December 2021, even as the index was higher.
- The Russell 2000 (small caps) peaked in November 2021 and was already declining while the S&P 500 made its final highs in January 2022.

The generals (mega-caps) were marching alone. The soldiers (mid-caps, small-caps, speculative growth) had already retreated. When the generals finally fell, there was nobody left to hold the line.

## Breadth Indicators to Track

1. **Advance/Decline Line** — the foundational measure. New highs in A/D line = healthy. Divergence = warning. Available for NYSE, NASDAQ, and S&P 500 components.

2. **Percentage of stocks above 200-day MA** — a snapshot of how many stocks are in uptrends. Above 80% = strong breadth. Below 50% = deteriorating. Below 30% = oversold (potential contrarian buy).

3. **Percentage of stocks above 50-day MA** — shorter-term version. Useful for detecting breadth deterioration in its early stages.

4. **New Highs minus New Lows** — the number of stocks making 52-week highs minus those making 52-week lows. Persistent positive readings confirm uptrend. Divergence from index is a leading signal.

5. **McClellan Oscillator** — measures the rate of change in advancing vs declining stocks. Readings below -50 suggest oversold breadth. Above +50 suggests overbought. Extreme readings often precede reversals.

6. **Equal-Weight vs Cap-Weight S&P 500** — when the cap-weighted S&P 500 (SPY) outperforms the equal-weight version (RSP), it means large caps are carrying the index. When RSP outperforms SPY, it means the average stock is doing better than the mega-caps — healthier breadth.

## How Divergences Resolve

Breadth divergences resolve in one of two ways:

1. **The index falls to match breadth** — the most common resolution. The narrowing rally eventually collapses as the handful of leaders fail.
2. **Breadth improves to match the index** — less common but possible. New sectors catch a bid, participation broadens, and the rally broadens out. This is the bullish resolution.

The agent cannot know in advance which resolution will occur, but the probability favors the bearish resolution — historically, sustained breadth divergences resolve negatively about 70-80% of the time.

## Implementation

The agent should track:
- Daily A/D line vs S&P 500 price, flagging any period where the index is at or near 52-week highs while A/D is declining for 20+ trading days
- Weekly percentage of S&P 500 stocks above 200-day MA — flag when this drops below 60% while the index is within 5% of its high
- SPY vs RSP relative performance on a rolling 30-day basis — persistent SPY outperformance = narrowing leadership
