# Earnings Revision Momentum — The Signal That Keeps Giving

## The Core Insight

Stocks whose earnings estimates are being revised upward systematically outperform stocks whose estimates are being revised downward. This is not about the earnings themselves — it is about the DIRECTION of analyst revisions. An analyst raising their estimate from $2.00 to $2.20 is a stronger predictive signal than the eventual actual earnings print.

This is one of the most robust and well-documented anomalies in quantitative finance, first identified in academic research in the 1980s and still effective decades later.

## Why It Works

Analysts revise estimates when they receive new information: management guidance updates, channel checks, industry data, customer surveys. A revision is a distilled signal — an analyst has processed complex information and decided the outlook has changed enough to update their published number.

But analysts revise SLOWLY. Behavioral biases — anchoring to prior estimates, herding (not wanting to be too far from consensus), career risk (bold estimates attract scrutiny) — mean that revisions understate the true magnitude of change. If the business environment has improved enough to warrant a $0.20 raise, the actual improvement is often $0.30-0.40. The first revision is just the beginning.

This is why revision momentum works: a revision signals that reality is better (or worse) than expected, and the analyst has only partially adjusted. Future revisions in the same direction are likely to follow.

## The Signal Hierarchy

Not all revisions are equal:

1. **Multiple analysts revising in the same direction** — strongest signal. If 3 out of 5 covering analysts raise estimates in the same month, something real is happening.
2. **Revision magnitude** — a 10% raise matters more than a 1% raise. Large revisions indicate significant new information.
3. **Revision breadth across line items** — revenue AND margin revisions together are stronger than either alone. Revenue revisions alone could be unsustainable. Margin revisions alone could be one-time.
4. **Recency** — a revision from this week matters more than one from six weeks ago.
5. **Analyst track record** — a revision from an analyst who is historically accurate for that company carries more weight.

## Implementing the Signal

The Earnings Estimate Revisions Index (ERI) is a simple metric: (number of upward revisions minus number of downward revisions) divided by total revisions over the trailing 30-90 days. An ERI above +0.5 indicates strong upward momentum. Below -0.5 indicates strong downward momentum.

For the agent:
- Track consensus estimate changes weekly for all positions and watchlist stocks
- Flag any stock where 2+ analysts revise in the same direction within 30 days
- Calculate 30-day and 90-day ERI scores
- Combine with price momentum: upward estimate revisions + positive price momentum = strongest signal
- Watch for estimate revisions that CONTRADICT price action — estimates rising while stock falls could signal an upcoming catch-up move

## What Can Go Wrong

- **One-time items:** An analyst might raise estimates based on a non-recurring event (asset sale, tax benefit). These revisions do not indicate improving business fundamentals.
- **Industry-wide revisions:** If all energy analysts raise estimates because oil spiked, that is a commodity call, not a stock-specific signal. Distinguish company-specific revisions from sector-wide adjustments.
- **Late-cycle revisions:** Near the end of an economic expansion, revisions tend to be most positive just before the cycle turns. The signal works until the macro environment shifts.
