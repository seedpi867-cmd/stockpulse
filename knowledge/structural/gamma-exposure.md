# Gamma Exposure (GEX): The Invisible Hand of Market Maker Hedging

## What Gamma Exposure Is

Gamma exposure (GEX) measures the total amount of delta hedging that options market makers must do as prices move. When market makers sell options to customers, they must hedge their directional risk by buying or selling the underlying stock. Gamma determines how much their hedge changes for each dollar move in the stock price. Aggregate GEX across all outstanding options tells you whether market maker hedging will amplify or dampen price moves.

This is not theoretical. Market maker hedging flows are estimated at tens of billions of dollars daily. They are among the largest mechanical flows in the equity market, and they operate on an entirely different logic than fundamental or sentiment-driven flows.

## Positive Gamma: The Dampener

When total GEX is positive, market makers are net long gamma. This occurs when customers have bought a lot of call options. As prices rise, market makers must sell stock to maintain their hedge (delta neutral). As prices fall, they must buy stock. This creates a mean-reverting force: market makers sell into rallies and buy into dips, dampening volatility.

This is why markets can grind higher in a steady, low-volatility trend for months at a time — positive gamma from massive call buying creates a structural bid on dips and a structural offer on rips. The market maker is the invisible hand smoothing the ride.

Positive gamma environments are characterised by: low realised volatility, steady grinding rallies, small intraday ranges, and dip-buying that seems to come from nowhere. The "buy the dip" regime from 2017-2019 and 2021 was partly a function of sustained positive gamma.

## Negative Gamma: The Amplifier

When total GEX is negative, market makers are net short gamma. This occurs when customers have bought a lot of put options or when market makers are short calls (as in overwriting strategies). As prices fall, market makers must sell stock to maintain their hedge. As prices rise, they must buy. This amplifies moves in both directions.

In negative gamma, every move is self-reinforcing. A 1% drop triggers market maker selling, which causes another 0.5% drop, which triggers more selling. The market becomes a pinball machine — violent moves in both directions with no dampening. The March 2020 crash, the February 2018 Volmageddon, and several other sharp selloffs featured deeply negative gamma that amplified what might otherwise have been orderly corrections.

Negative gamma environments are characterised by: high realised volatility, violent gap moves, large intraday ranges, failed dip-buys (because market makers are selling into the dip, not buying), and "air pockets" where price drops rapidly through levels with no support.

## The GEX Flip: The Critical Transition

The most important signal is when aggregate GEX flips from positive to negative. This transition changes the market's behaviour from mean-reverting (dips get bought, rallies get sold) to trend-following (moves get amplified). The flip often occurs when the S&P 500 drops below a key level with large open interest in put options, typically around a round number like 4,000 or 4,500.

Tracking GEX requires calculating the gamma across all outstanding options at every strike price. Services like SqueezeMetrics, SpotGamma, and GammaLab publish daily GEX estimates for the S&P 500 and major stocks.

## The Zero Gamma Level

The "zero GEX" level is the price at which aggregate gamma flips from positive to negative. Above this level, the market is in dampened mode. Below it, the market is in amplified mode. SpotGamma and other providers publish this level daily.

Trading implications: when the market is above the zero GEX level, expect low volatility, grinding rallies, and shallow pullbacks. Sell premium. When the market is below the zero GEX level, expect high volatility, sharp moves, and failed bounces. Buy premium. At the zero GEX level itself, expect a fight between the two regimes.

## Quarterly OPEX and Gamma

Options expiration (OPEX) events remove gamma from the system. After monthly or quarterly expiration, the options that were creating positive or negative gamma cease to exist. If the market was being stabilised by positive gamma, that stabilisation vanishes after expiry. Post-OPEX moves can be violent because the mechanical hedging flows that were dampening volatility disappear overnight.

## What the Agent Should Know

GEX is a core market regime indicator. The agent should track aggregate S&P 500 GEX daily to understand whether the current regime is dampened (positive GEX, favour selling volatility and buying dips) or amplified (negative GEX, favour buying volatility and reducing exposure). The zero gamma level is a key tactical level for equity exposure decisions. GEX does not predict direction — it predicts the character of the move.
