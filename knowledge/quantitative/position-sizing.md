# Position Sizing Methods

## Why Position Sizing Matters More Than Entry

Most traders obsess over entries and neglect position sizing, yet research consistently shows that position sizing has a greater impact on long-term returns than entry timing. Van Tharp demonstrated that random entries combined with proper position sizing and exits can be profitable. The key insight: you cannot control whether a trade wins or loses, but you can control how much you risk on each trade.

## The 1% Rule (Fixed Fractional)

The most common and practical position sizing method: risk no more than 1% of total account equity on any single trade. This does not mean allocating 1% of your portfolio to a position — it means the maximum loss if your stop is hit should be 1% of equity.

Example: Account size is 100,000 dollars. You want to buy a stock at 50 dollars with a stop at 47 dollars (3 dollar risk per share). Maximum risk per trade = 1,000 dollars. Position size = 1,000 / 3 = 333 shares, or roughly 16,650 dollars (16.65% of account). The position is larger than 1%, but the risk is exactly 1%.

This approach scales naturally — after a winning streak, your account grows and position sizes increase. After losses, positions automatically shrink, protecting remaining capital during drawdowns.

## Kelly Criterion

Developed by mathematician John Kelly in 1956 for information theory, adapted for trading. The formula determines the mathematically optimal fraction of capital to risk:

Kelly % = W - ((1 - W) / R)

Where W = win rate (probability of winning) and R = win/loss ratio (average win divided by average loss).

Example: A strategy with 55% win rate and 1.5:1 reward/risk ratio: Kelly = 0.55 - (0.45 / 1.5) = 0.55 - 0.30 = 0.25, or 25% of capital per trade.

In practice, full Kelly sizing is extremely aggressive and leads to massive drawdowns. Most professional traders use half-Kelly or quarter-Kelly. Even at half-Kelly (12.5% in the example above), drawdowns can exceed 30%. Quarter-Kelly (6.25%) provides a smoother equity curve with 75% of the long-term growth rate.

## Volatility-Based Sizing (ATR Method)

Position size is inversely proportional to the stock volatility. Use the Average True Range (ATR) to normalize risk across different stocks:

Position size = (Account risk) / (N x ATR)

Where N is a multiplier (typically 2-3). A volatile stock with a 5 dollar ATR gets a smaller position than a stable stock with a 1 dollar ATR, equalizing the dollar risk.

This method is used by trend-following CTAs and was popularized by the Turtle Traders. It prevents the common mistake of sizing all positions equally in dollars, which overweights volatile names and underweights stable ones in risk terms.

## Portfolio Heat

Total portfolio risk should not exceed 6-8% at any time. If you risk 1% per trade and have 8 open positions, your portfolio heat is 8%. Adding a 9th position would push total risk to 9%, which is too high. Either close a position or reduce sizes. During high-correlation periods (everything moving together), reduce maximum portfolio heat to 4-5% because diversification benefit is reduced.

## Anti-Martingale Principle

Always increase position sizes after wins and decrease after losses. This is the opposite of gambling instinct (doubling down after losses). The math is simple: if you risk the same dollar amount on every trade, a 50% drawdown requires a 100% gain to recover. If you reduce size during drawdowns, the hole is shallower and recovery is faster.
