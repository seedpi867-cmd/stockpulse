# Failure to Deliver Patterns: Forced Buying on a Schedule

## What FTDs Are

A Failure to Deliver (FTD) occurs when a seller of a security does not deliver the shares to the buyer within the standard settlement period. In the US equity market, settlement is T+1 (trade date plus one business day, changed from T+2 in May 2024). When a short seller cannot locate shares to deliver, or when operational failures prevent delivery, the trade is marked as a Failure to Deliver.

The SEC publishes FTD data twice monthly, with a roughly two-week lag. The data shows every security with outstanding fails, the number of shares that failed to deliver, and the closing price on that date.

## Why FTDs Matter

FTDs create future buying pressure. Under Regulation SHO, broker-dealers are required to close out fail-to-deliver positions. For short sales, the close-out requirement kicks in at T+3 (three settlement days after the settlement date). Market makers have an extended timeframe of up to T+6 under certain exemptions. This creates predictable forced buying at known intervals after large FTD events.

The T+35 calendar day rule is the outer limit. If shares are not delivered within 35 calendar days, the broker-dealer must immediately purchase shares to close the position. This is not optional — it is a regulatory requirement. Large accumulations of FTDs therefore create a future date on which buying pressure will mechanically appear.

## The GameStop Example

GameStop in late 2020 and early 2021 demonstrated FTD dynamics at scale. The stock had persistent, large FTD positions — sometimes millions of shares — while short interest exceeded 100% of float. The forced buying from FTD close-outs, combined with retail buying and short covering, created the conditions for the historic squeeze.

Researchers tracking FTD data noticed cyclical patterns in GameStop price spikes that correlated with T+35 settlement deadlines from large FTD events. The cycles were not perfect but they were statistically significant.

## How to Track FTD Cycles

Download FTD data from the SEC website (sec.gov/data/foiadocsfailsdatahtm). The files are plain text, updated twice monthly. For each security with FTDs, note the date and quantity. Add 35 calendar days to find the forced close-out deadline.

Key signals: a stock with persistently high FTDs (relative to daily volume) has ongoing delivery problems, which means shorts are struggling to locate shares. A sudden spike in FTDs after a large short-selling day signals that the shorts could not find real shares to deliver. Large FTDs at low prices followed by price increases suggest covering pressure is building.

Services like Fintel, SECfailures.com, and Chartexchange aggregate and visualise FTD data, making pattern recognition easier than parsing raw SEC files.

## Important Caveats

FTDs can result from operational errors, not just naked shorting. A processing glitch or miscommunication between broker-dealers creates fails that are promptly resolved. The signal is in persistent, large FTD positions — not one-off fails.

The SEC has also allowed certain FTDs to be rolled forward through complex options strategies (buy-write trades, married puts), which can reset the clock without actually delivering shares. This is controversial and has been the subject of regulatory scrutiny.

## What the Agent Should Know

FTD data is public, free, and actionable. Monitor stocks with high and persistent FTDs relative to float and daily volume. Calculate T+35 deadlines from large FTD spikes. When FTD forced buying coincides with other bullish signals (high short interest, rising borrow costs, positive catalysts), the probability of a significant upward move increases substantially. The data has a lag, so the edge is in tracking cycles and anticipating the next close-out window.
