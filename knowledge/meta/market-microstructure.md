# Market Microstructure Basics

## How Orders Actually Work

Understanding market microstructure — the mechanics of how orders are matched, executed, and reported — gives traders an informational advantage over those who treat the market as a black box. The modern US equity market is a fragmented, electronic system where your order may be routed to over a dozen different venues before execution.

## Order Types That Matter

**Market orders:** Execute immediately at the best available price. In liquid large-cap stocks, slippage is minimal (0.01-0.03%). In small-caps or during volatility, slippage can be 0.1-0.5% or more. Never use market orders on illiquid stocks or during the opening auction.

**Limit orders:** Execute only at your specified price or better. Limit orders provide price certainty but not execution certainty — you may not get filled. They add liquidity to the market (you become the maker) and often receive better execution through rebates on certain exchanges.

**Stop orders:** Become market orders when the stop price is touched. Critical nuance: in a fast market, the execution price can be far worse than the stop price (slippage). During the August 2015 flash crash, stop orders on blue-chip stocks like Apple executed 10-20% below the stop price because the order book was empty.

**Stop-limit orders:** Become limit orders at the limit price when the stop is triggered. Safer than stop-market orders (no wild slippage) but risk non-execution if the price gaps through the limit.

## Venue Fragmentation

US equities trade across 16 registered exchanges (NYSE, NASDAQ, CBOE, IEX, etc.) plus approximately 40 dark pools and numerous alternative trading systems. Your broker routes your order to the venue that provides best execution (legally required under Regulation NMS), but the definition of best execution involves tradeoffs between speed, price, and probability of fill.

**Payment for order flow (PFOF):** Brokers like Robinhood route retail orders to wholesale market makers (Citadel Securities, Virtu Financial) who pay for the privilege of executing those orders. The market maker provides price improvement (fractionally better than the displayed quote) while profiting from the spread. This is legal and common — roughly 90% of retail market orders go through PFOF. The debate about whether this is good or bad for retail traders remains active.

**Dark pools:** Private venues where large institutional orders can execute without displaying to the public order book. This prevents information leakage — if a pension fund wants to buy 5 million shares of Microsoft, displaying that order on a public exchange would move the price against them. Dark pools execute roughly 15-18% of US equity volume.

## The NBBO and Spread

The National Best Bid and Offer (NBBO) is the best available bid and ask across all exchanges at any given moment. The difference between them — the spread — is the cost of immediacy. For large-cap stocks like Apple or Microsoft, the spread is typically one cent (0.01% of stock price). For small-caps, it can be 0.5-2.0%.

The spread is a real cost that compounds with trading frequency. A day trader making 20 round trips per day in a stock with a 0.05% spread loses 2% daily to the spread alone — 500% annualized. This is why high-frequency trading requires sub-penny edge and extreme volume, and why retail traders should minimize transaction frequency.

## Practical Implications

Use limit orders for entries and exits in all but the most liquid names. Route orders through IEX if your broker allows it — IEX has a speed bump that protects against high-frequency traders picking off stale quotes. Be aware that large orders (over 1% of average daily volume) will move the market; use TWAP or VWAP algorithms to slice large orders over time. And understand that the displayed order book represents only 30-40% of available liquidity — the rest sits in dark pools and undisplayed reserve orders.
