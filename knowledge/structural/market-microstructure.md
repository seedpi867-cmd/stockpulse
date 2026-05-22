# Market Microstructure: How the Plumbing Actually Works

## The Market Is Not Fair

The popular image of the stock market — a place where buyers and sellers meet at a fair price — is a fiction. The modern market is a complex, fragmented, and in many ways adversarial system where informational and speed advantages are monetised at the expense of less-informed participants. Understanding the plumbing reveals why retail stops get hit, why orders fill at worse prices than expected, and who profits from the gap.

## Payment for Order Flow (PFOF)

When you place an order through a retail broker (Robinhood, Schwab, E-Trade, etc.), your order does not go to the NYSE or Nasdaq. It is sold to a wholesale market maker — primarily Citadel Securities, Virtu Financial, or G1X (formerly Two Sigma Securities). The market maker pays the broker for the right to execute your order. This is payment for order flow.

The market maker profits because it can see your order before executing it. If you place a market buy order for 100 shares of Apple, the market maker sees the order, evaluates the current market conditions in microseconds, and fills you at a price that is profitable for them. They are required to match or beat the National Best Bid and Offer (NBBO), but the NBBO is itself a stale quote that may not reflect the true real-time price.

Citadel Securities alone handles roughly 25-40% of all US retail equity order flow. They see retail positioning in real-time across millions of accounts, giving them an aggregate view of retail sentiment that no other market participant has.

## Latency Arbitrage

High-frequency trading firms (HFTs) co-locate their servers in the same data centres as the exchanges, connected by the shortest possible fibre optic or microwave links. This gives them a speed advantage measured in microseconds — enough to see a quote change on one exchange and trade ahead of it on another.

When you place an order, it takes milliseconds to reach the exchange. In that time, an HFT can detect your order (or the market impact of your order), adjust prices on other exchanges, and profit from the price difference. This is not illegal — it is a structural feature of the market. Michael Lewis described it in "Flash Boys" (2014), and while IEX was created to combat it with a speed bump, latency arbitrage remains a multi-billion-dollar industry.

## How Retail Stops Get Hit

Retail stop-loss orders are visible to market makers who receive the order flow. When a large number of stop-loss orders cluster at a round number (say, $50 on a stock trading at $52), the concentration creates a target. A brief price dip to $50 triggers a cascade of stop orders, which become market sell orders, which push the price below $50, which triggers more stops. The market maker (or other informed participants) then buys at the depressed price, and the stock recovers.

This is called "stop hunting" and it is particularly common in less liquid stocks and during low-volume periods (pre-market, after-hours, overnight futures). The solution is not to eliminate stop losses but to place them at non-obvious levels (not round numbers, not at visible technical levels) or use mental stops with limit orders rather than stop-market orders.

## The Consolidated Tape and the Illusion of a Single Price

There is no single "stock market" in the US. There are 16 lit exchanges (NYSE, Nasdaq, CBOE, IEX, etc.), roughly 40 dark pools, and hundreds of broker-dealer internalisers. Each venue has its own order book with potentially different prices. The "last price" you see on your screen is from the consolidated tape — a merged feed that may not reflect the best available price across all venues.

This fragmentation creates opportunities for sophisticated participants and disadvantages for retail. Professional firms use smart order routers that scan all venues for the best price. Retail orders go wherever the broker's PFOF arrangement sends them, which may not be the best venue.

## Maker-Taker Model

Exchanges charge and rebate fees based on whether you add liquidity (post a limit order that sits on the book — the "maker") or remove liquidity (execute against an existing order — the "taker"). Makers receive a rebate (typically $0.20-0.30 per 100 shares). Takers pay a fee ($0.25-0.30 per 100 shares). This creates a complex incentive structure where HFTs post and cancel orders rapidly to capture rebates, adding noise to the order book.

## What the Agent Should Know

The market structure is designed to extract value from less-informed participants. The agent should use limit orders (not market orders), avoid obvious stop-loss levels, be aware that retail order flow is visible to market makers, and understand that the displayed price may not be the best available price. In practical terms, avoid chasing prints, use patient limit orders, and assume that large visible orders on the book may be spoofed or cancelled before execution.
