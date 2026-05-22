# Spoofing and Layering

## What Spoofing Is

Spoofing is the illegal practice of placing large orders with the intent to cancel them before execution, creating a false impression of supply or demand. The spoofer places visible orders on one side of the order book to move the price, then executes their real trade on the other side, and immediately cancels the fake orders. It was explicitly banned by the Dodd-Frank Act in 2010.

## How It Works in Practice

A spoofer wanting to buy stock at a lower price might place large sell orders (say, 50,000 shares) above the current ask price. Other market participants see this wall of selling and interpret it as distribution — bearish. Algorithmic traders detect the large sell-side imbalance and begin selling, pushing the price down. The spoofer then buys at the artificially depressed price and immediately cancels the fake sell orders. The process takes seconds.

**Layering** is a variant where the spoofer places multiple orders at different price levels, creating the appearance of deep supply or demand across several ticks. This is harder to detect because each individual order may look legitimate.

## Notable Cases

**Navinder Sarao (2015):** A British trader operating from his parents house in Hounslow was accused of contributing to the May 6, 2010 Flash Crash, during which the Dow Jones dropped nearly 1,000 points in minutes. Sarao used a modified trading program to place and rapidly cancel E-mini S&P 500 futures contracts worth hundreds of millions. He was arrested in 2015 and ultimately sentenced to one year of home detention and a 12.87 million dollar fine after cooperating with authorities.

**JPMorgan (2020):** The DOJ charged JPMorgan Chase with spoofing in precious metals and Treasury futures markets over an eight-year period (2008-2016). The bank paid 920 million dollars in fines — the largest spoofing settlement in history. Multiple traders, including the head of the precious metals desk, were criminally charged.

**Deutsche Bank, Bank of America, and others** have also paid significant fines for spoofing in various markets, establishing that the practice was endemic in institutional trading desks throughout the 2000s and 2010s.

## How to Detect Spoofing

Retail traders cannot see the full order book in real time, but certain patterns suggest spoofing:

- **Repeated appearance and disappearance of large orders:** A 10,000-share bid that appears at a key support level, pulls a breakout, then vanishes moments later. Level 2 data shows these flickers.
- **Order book imbalance that does not result in trades:** Heavy sell-side orders that never actually execute — they disappear before being hit.
- **Price movement on no real volume:** The stock moves 0.5% on thin actual volume while the order book showed heavy one-sided depth. The depth was fake.

## Defensive Strategies

Never place market orders during volatile conditions — you are most vulnerable to spoofing when using market orders that sweep through the order book. Use limit orders exclusively. Be skeptical of sudden order book imbalances, especially in mid-cap and small-cap names where spoofing is most prevalent (large-caps have enough natural flow to absorb spoofing). If you see a large wall of orders at a support or resistance level that seems too convenient, wait to see if it holds through actual trading rather than treating it as confirmation of the level.
