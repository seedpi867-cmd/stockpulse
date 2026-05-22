# Risk Management Failures: Lessons from Blown-Up Traders

## The Common Thread

Every legendary trading blowup shares the same root cause: a trader who was right for a long time, became overconfident, sized too large, and then encountered the one scenario they believed was impossible. The market does not care about track records — it only cares about current positioning.

## Bill Hwang / Archegos Capital (2021)

Bill Hwang ran Archegos Capital Management as a family office, which exempted him from hedge fund disclosure requirements. Using total return swaps (synthetic leverage), he built concentrated positions of 5-10x leverage in a handful of stocks including ViacomCBS, Discovery, Baidu, and Tencent Music. At peak, Archegos controlled an estimated 100 billion dollars in exposure on roughly 10 billion in capital.

When ViacomCBS announced a secondary stock offering in March 2021, the stock dropped 9% and triggered margin calls across all positions simultaneously. Archegos could not meet the calls, forcing prime brokers to liquidate. Goldman Sachs and Morgan Stanley sold early and limited losses. Credit Suisse delayed and lost 5.5 billion dollars — a loss so severe it contributed to the eventual forced merger with UBS.

**Lesson:** Concentration plus leverage is terminal. Any single-name position above 20% of portfolio is speculation, not investing. Leverage above 2x turns manageable drawdowns into account-ending events.

## Long-Term Capital Management (1998)

LTCM was run by Nobel laureates Myron Scholes and Robert Merton, with former Salomon Brothers head John Meriwether. Their models identified small mispricings between related bonds and used 25:1 leverage to make the tiny edge profitable. From 1994-1997, they earned 21%, 43%, 41%, and 17% annually.

In August 1998, Russia defaulted on its government bonds, triggering a global flight to quality. Every correlated spread that LTCM held moved against them simultaneously — their models assumed correlations would remain stable, but in a crisis, all correlations go to 1.0. LTCM lost 4.6 billion dollars in four months. The Fed orchestrated a 3.6 billion dollar bailout by 14 banks to prevent systemic contagion.

**Lesson:** Models that assume stable correlations will fail during the exact conditions when risk management matters most. Crises cause correlation spikes that invalidate diversification assumptions. Stress test your portfolio for the scenario where everything moves against you at once.

## Nick Leeson / Barings Bank (1995)

Leeson was a derivatives trader at Barings Bank in Singapore who concealed losses in a hidden error account (88888). Rather than reporting losses, he doubled down, selling options straddles on the Nikkei 225 — betting that the index would remain stable. The 1995 Kobe earthquake caused the Nikkei to plunge, destroying his short volatility positions. Total losses reached 1.3 billion dollars, more than twice the bank entire capital. Barings, the oldest merchant bank in Britain (233 years old), was bankrupted.

**Lesson:** Doubling down on a losing position is the single most destructive behavior in trading. Every dollar added to a losing trade has a lower expected return than the first dollar, because the thesis that justified the original trade has been weakened by the adverse price action. Cut losses mechanically.

## Common Patterns

Every blowup features at least three of these elements:
1. Excessive leverage (typically 5x or higher)
2. Concentrated positions (fewer than 5 names representing more than 70% of exposure)
3. Short volatility or short tail risk (profitable most of the time, catastrophic when wrong)
4. Refusal to cut losses (doubling down instead of reducing)
5. Assumption that historical correlations persist in a crisis
