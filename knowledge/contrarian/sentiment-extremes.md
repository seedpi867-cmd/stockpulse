# Trading Sentiment Extremes

## The Contrarian Edge

Sentiment indicators measure the collective mood of market participants. At extremes, they become powerful contrarian signals because extreme bullishness means most potential buyers have already bought (limiting further upside), and extreme bearishness means most potential sellers have already sold (limiting further downside). The edge is not in being contrarian for its own sake but in identifying measurable exhaustion of one side.

## Key Sentiment Indicators

**AAII Sentiment Survey:** The American Association of Individual Investors has surveyed members weekly since 1987, asking whether they are bullish, bearish, or neutral on the stock market over the next six months.

Historical averages: bullish 37.5%, neutral 31.5%, bearish 31.0%. When bearish sentiment exceeds 50% (roughly 2 standard deviations above mean), the S&P 500 has averaged a 15.3% gain over the next 12 months. When bullish sentiment exceeds 55%, subsequent 12-month returns have averaged only 4.2%. The indicator is not precise on timing but excellent on direction over 6-12 month horizons.

**CNN Fear and Greed Index:** Combines seven sub-indicators (stock price momentum, stock price strength, stock price breadth, put/call ratio, junk bond demand, market volatility, safe haven demand) into a single 0-100 score. Readings below 20 (extreme fear) have preceded average 3-month returns of 8.5% for the S&P 500. Readings above 80 (extreme greed) have preceded average 3-month returns of -1.2%.

**Put/Call Ratio:** The CBOE equity put/call ratio measures the volume of puts traded relative to calls. The historical average is 0.65-0.70. Readings above 1.0 indicate extreme fear (more puts than calls being purchased), which is contrarian bullish. Readings below 0.50 indicate extreme complacency, which is contrarian bearish. The 10-day moving average smooths out daily noise.

**Investors Intelligence Survey:** Surveys professional newsletter writers. The bull-bear spread (% bulls minus % bears) at extremes is a reliable contrarian signal. A spread below -15% (more bears than bulls) has preceded positive 6-month returns 94% of the time since 1970.

## Combining Sentiment Indicators

A single indicator at an extreme is worth noting. Three or more indicators simultaneously at extremes is a high-conviction signal. In March 2020: AAII bearish at 52.1%, CNN Fear and Greed at 2 (out of 100), put/call ratio at 1.42, VIX at 82. All four screamed extreme fear simultaneously. The S&P 500 bottomed within days and gained 70% over the next 12 months.

The same alignment at euphoria extremes occurred in January 2018 (AAII bullish at 59.8%, CNN at 87, put/call at 0.49, VIX at 9) — a 12% correction followed within 2 weeks.

## Implementation Framework

Create a composite sentiment score that averages the z-scores of 4-5 sentiment indicators. When the composite falls below -1.5 standard deviations (extreme fear), begin scaling into long positions — do not try to time the exact bottom. When the composite exceeds +1.5 standard deviations (extreme greed), begin reducing exposure and raising cash. The middle ground (-1 to +1 standard deviations) is noise — sentiment does not provide actionable information in the normal range.

## Critical Caveat

Sentiment indicators fail during secular regime changes. Bearish sentiment was extreme throughout 2008 but the market kept falling for months. The reason: in a genuine financial crisis, sentiment correctly reflects deteriorating fundamentals rather than emotional overreaction. Use sentiment extremes only when the underlying fundamental and credit picture is not in structural deterioration. If credit spreads are blowing out and earnings are collapsing, extreme bearish sentiment may be rational, not contrarian.
