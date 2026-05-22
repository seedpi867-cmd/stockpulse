# Gamma Exposure (GEX) and Dealer Hedging

## Why Gamma Exposure Matters

Gamma exposure (GEX) has become one of the most important structural forces in modern markets. Market makers who sell options to investors must continuously hedge their positions by buying or selling the underlying stock. The aggregate gamma exposure of all outstanding options determines whether dealer hedging suppresses or amplifies market volatility.

## Positive vs. Negative GEX

**Positive GEX (dealers are long gamma):** When the market is above a key strike level where significant call open interest sits, dealers are effectively long gamma. This means: when the stock rises, dealers sell (because their delta increases and they need to reduce exposure), and when the stock falls, dealers buy. This creates a dampening effect — dealer hedging acts as a natural shock absorber. Positive GEX regimes produce low volatility, narrow ranges, and mean-reverting behavior. The market feels sticky and choppy.

**Negative GEX (dealers are short gamma):** When the market drops below key put strike levels, or when put open interest dominates, dealers become short gamma. Now the dynamic reverses: when the stock falls, dealers must sell more (their delta exposure increases on the short side), and when it rises, they must buy. This creates a positive feedback loop that amplifies moves in both directions. Negative GEX regimes produce wide daily ranges, gap moves, and trending behavior. The March 2020 crash saw extreme negative GEX as put buying overwhelmed all other positioning.

## The GEX Flip Point

SpotGamma and other analytics providers calculate the price level where aggregate GEX flips from positive to negative. This level acts as a critical threshold:

- Above the flip point: expect low volatility, sideways chop, mean reversion. Sell premium, use mean reversion entries.
- Below the flip point: expect high volatility, trending moves, expanded ranges. Buy premium for directional bets, avoid mean reversion.

The flip point for the S&P 500 is typically near a round number (4000, 4500, 5000) where large volumes of options are concentrated.

## Zero-DTE Options and Intraday GEX

The explosion of zero days to expiration (0DTE) options — options expiring the same day — has massively increased intraday gamma effects. Daily options volume on the S&P 500 now exceeds 40% of total volume. These 0DTE options have extreme gamma because they are hours from expiration, meaning dealers must hedge aggressively throughout the day.

The practical effect: intraday moves are increasingly mechanical rather than fundamental. A morning selloff triggers 0DTE put buying, which forces dealer selling, which accelerates the decline. Conversely, an afternoon bounce triggers call buying and dealer buying. The last hour of trading on days with heavy 0DTE volume often sees violent reversals as gamma effects peak near the close.

## Trading with GEX

Track aggregate GEX data from SpotGamma, Menthor Q, or similar services. In positive GEX regimes:
- Sell iron condors and strangles (betting on range-bound behavior)
- Buy pullbacks to support because dealer buying will cushion declines
- Expect the VIX to compress

In negative GEX regimes:
- Buy directional options (puts in a decline, calls on a recovery)
- Do not fade the move — dealer hedging will extend it
- Use wider stops because intraday ranges expand 50-100%

The GEX framework does not predict direction but does predict the character of the market — whether it will chop or trend — which is equally valuable for strategy selection.
