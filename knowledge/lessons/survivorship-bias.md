# Survivorship Bias in Trading

## The Invisible Graveyard

Survivorship bias is the logical error of focusing on successful outcomes while ignoring failures that are no longer visible. In financial markets, this bias distorts almost everything: fund performance, stock returns, strategy backtests, and the careers of famous traders. If you do not explicitly account for it, your decisions are built on a systematically skewed picture of reality.

## How It Distorts Fund Performance

When you see that the average equity mutual fund returned 10% over the past decade, that number only includes funds that survived the full decade. Funds that performed poorly were closed or merged into better-performing funds, removing their bad returns from the historical record. Research by Elton, Gruber, and Blake (1996) found that survivorship bias inflates reported mutual fund returns by 0.9% to 1.5% annually. The true average fund return is significantly worse than published statistics suggest.

Hedge fund databases are even more distorted. Funds that blow up simply stop reporting. The HFRI hedge fund index has estimated survivorship bias of 2-3% per year. This means the average hedge fund performance you see in databases overstates reality by roughly 20-30% over a decade.

## Impact on Stock Market Returns

The often-cited statistic that the stock market returns 10% per year is based on the US stock market, which was the best-performing major market of the 20th century. This is survivorship bias at the country level — you are looking at the winner. The Japanese Nikkei 225 peaked at 38,957 in December 1989 and took 34 years to recover that level (finally surpassing it in February 2024). The Shanghai Composite, German DAX in the 1920s-1940s, and Russian stock market (which went to zero in 1917) tell very different stories about long-term equity returns.

Within the US market, the S&P 500 continuously replaces failing companies with successful ones. When a company declines to insignificance, it is removed from the index and replaced by a growing company. The index thus automatically benefits from survivorship bias — it always holds the winners.

## Backtesting Traps

Strategy backtests are particularly vulnerable. If you backtest a momentum strategy by selecting stocks that exist today and looking at their historical returns, you are only testing stocks that survived. Companies that went bankrupt, were delisted, or were acquired at depressed prices are absent from your dataset. This inflates backtest returns, sometimes dramatically.

Proper backtests must use point-in-time data that includes all stocks that existed during the test period, including those that subsequently failed. Databases like CRSP (Center for Research in Security Prices) include delisted stocks, but many free data sources do not.

## The Trader Survivorship Problem

For every successful trader profiled in Market Wizards, thousands of equally confident traders blew up and left the industry. The traders who survive long enough to be interviewed are, by definition, the lucky subset who avoided the ruin scenario. Their advice may be valid, but it is filtered through the lens of someone who happened to be on the right side of the distributions tail events.

This creates a dangerous false confidence: following the exact strategy of a famous trader does not guarantee similar results because you do not know how much of their success came from skill versus survivorship in specific market conditions.

## Practical Defense

Always ask: what am I not seeing? When evaluating a strategy, fund, or market statistic, explicitly consider the failures that were removed from the dataset. Use delisting-adjusted returns in backtests. Discount reported fund performance by 1-2% for survivorship bias. And remember that the past 100 years of US stock market returns represent one path out of many possible outcomes — not a guaranteed future.
