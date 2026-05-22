# Post-Earnings Announcement Drift — The Move After the Move

## The Anomaly

Post-Earnings Announcement Drift (PEAD) is one of the oldest and most persistent anomalies in financial markets. First documented by Ball and Brown in 1968, it describes the tendency for stocks to continue moving in the direction of their earnings surprise for 60-90 days after the announcement.

A stock that beats earnings tends to drift higher for weeks. A stock that misses tends to drift lower for weeks. The initial earnings reaction — the gap up or gap down — captures only about half of the total move. The drift is the other half.

## Why It Persists

PEAD should not exist in an efficient market. If the earnings surprise is informative, the price should adjust immediately and fully. But it does not, for several reasons:

1. **Underreaction bias.** Investors anchor to prior beliefs and adjust slowly. A beat does not fully update expectations because people discount new information.
2. **Information diffusion.** Not all market participants process earnings simultaneously. Institutional algorithms react in milliseconds. Fundamental analysts take days. Retail investors take weeks. The staggered processing creates a gradual price adjustment.
3. **Analyst revision lag.** As discussed in earnings-revision-momentum.md, analysts update estimates slowly after earnings. Each revision triggers another round of buying/selling, extending the drift.
4. **Institutional rebalancing.** Large funds cannot adjust positions instantly — they take days or weeks to build or unwind. Their gradual buying/selling after earnings contributes to the drift.

## Measuring the Surprise

The drift magnitude correlates with the size of the surprise. A stock that beats by 20% will drift more than one that beats by 2%. The standard metric is SUE (Standardized Unexpected Earnings): actual EPS minus consensus estimate, divided by the standard deviation of past surprises for that stock.

High SUE stocks (top decile) historically outperform low SUE stocks (bottom decile) by 4-8% over the following quarter. This premium has been documented across markets, time periods, and market caps.

## Trading the Drift

The naive implementation: buy stocks that beat earnings, hold for 60 days. This works but can be refined:

1. **Enter after the initial gap, not before.** The first day reaction is chaotic and gap-heavy. Entering on day 2-5 after the earnings reaction has settled captures the drift while avoiding the earnings event risk.
2. **Filter for quality surprises.** Revenue beats combined with earnings beats produce stronger drifts than earnings-only beats (which might be driven by cost-cutting or buybacks rather than genuine growth).
3. **Combine with guidance.** Beat + raise guidance produces the strongest drift (see guidance-vs-beat.md). Beat + lower guidance produces negative drift even after a positive initial reaction.
4. **Size by conviction.** The drift is a probability, not a certainty. Size positions appropriately — this is a statistical edge, not a guaranteed outcome.
5. **Exit discipline.** The drift fades over 60-90 days. Do not overstay. Set a time-based exit, not just a price target.

## When Drift Fails

- **Macro shocks override drift.** A stock that beat earnings will still decline if the broad market enters a correction.
- **Sector rotation.** If the market is rotating away from a sector, individual earnings beats within that sector may not produce drift.
- **High-short-interest names.** Heavily shorted stocks that beat can see short squeezes that front-load the entire move into day one, leaving no drift.
- **Already-extended stocks.** A stock that has already run 30% into earnings and then beats may have already priced in the improvement. The drift is weaker or absent.

For the agent: flag earnings surprises with SUE > 1.0 as drift candidates, cross-reference with guidance direction, and track 60-day drift performance for backtesting.
