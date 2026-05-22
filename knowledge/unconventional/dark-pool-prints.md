# Dark Pool Prints: What Institutions Are Hiding in Plain Sight

## What Dark Pools Are

Dark pools are private trading venues where institutional investors execute large orders without displaying them on public exchanges. They exist because a pension fund selling 10 million shares of Microsoft on the NYSE would move the price against itself — every market participant would see the order and front-run it. Dark pools allow the trade to execute without revealing the intent until after completion.

There are roughly 40-50 active dark pools in the US, operated by major banks (Goldman Sachs's Sigma X, Morgan Stanley's MS Pool, JP Morgan's JPM-X), independent operators (IEX), and broker-dealers. Dark pool volume consistently represents 35-45% of all US equity trading volume — nearly half of all stock trading happens off the public exchanges.

## How Dark Pool Data Becomes Visible

Dark pool trades are not reported in real-time on the public order book. But they are reported to the consolidated tape (the record of all trades) after execution, typically within 10 seconds. The prints show up as trades executed at prices that may not match the current bid-ask spread on public exchanges, and they are tagged with specific identifiers showing they occurred off-exchange.

This creates an information asymmetry: the intent is hidden, but the execution is visible. You cannot see the dark pool order book, but you can see what traded and at what price after the fact.

## Reading the Prints

Several patterns in dark pool activity are informative:

Block trades at prices away from the current market: a large trade (10,000+ shares) executing at a price significantly above or below the current bid-ask suggests aggressive positioning. A block bought at the ask or above indicates urgency — the buyer wanted the shares enough to pay a premium. A block sold at the bid or below indicates urgency to sell.

Dark pool volume spikes: when dark pool volume as a percentage of total volume rises significantly above the stock's average, institutions are actively positioning. Whether they are buying or selling can be inferred from subsequent price action and the print prices relative to the current market.

DIX (Dark Pool Indicator): SqueezeMetrics created the DIX, which measures the aggregate dark pool buying pressure across the S&P 500. When DIX is high (above 45%), institutions are buying in dark pools — historically a bullish signal. When DIX is low (below 40%), institutions are selling — bearish. The DIX has had a better track record than the VIX for predicting S&P 500 direction over 5-20 day windows.

## GEX and Dark Pool Interaction

Dark pool data combined with gamma exposure (GEX) data creates a powerful composite signal. When dark pools show heavy buying (high DIX) and gamma exposure is positive (market makers dampening moves), the conditions favour a grind higher. When dark pools show selling (low DIX) and gamma is negative (market makers amplifying moves), the conditions favour a sharp selloff.

## Data Sources

FINRA publishes weekly dark pool volume data by security (ATS Transparency Data), available free but with a two-week lag. Real-time dark pool print data is available from commercial providers including SqueezeMetrics (DIX/GEX), FlowAlgo, BlackBox Stocks, and Unusual Whales.

The FINRA data is useful for longer-term analysis — tracking which stocks are seeing elevated dark pool activity over weeks. Real-time print data is more useful for tactical positioning.

## Limitations

Dark pool prints do not tell you the direction of the trade. A reported trade at the ask price suggests a buyer, but the trade could be part of a larger hedging operation where the directional intent is opposite. Institutions also use VWAP and TWAP algorithms that spread orders across dark pools and lit exchanges, making it difficult to reconstruct the full picture from dark pool prints alone.

## What the Agent Should Know

Monitor DIX as a core sentiment indicator — it represents what institutions are actually doing with real money, as opposed to what they say in media appearances. Track dark pool volume as a percentage of total volume for watchlist stocks. Spikes in dark pool volume, particularly combined with price levels near key technical levels, suggest institutional accumulation or distribution before a move. The prints cannot be hidden forever — they always show up on the tape.
