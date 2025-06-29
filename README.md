# Trading System - PECES

This repository contains an early implementation of the **PECES** module.
Each `Pez` represents a trading agent that operates on different
market timeframes:

- **Sardina** – 1 hour candles
- **Atun** – daily candles (executed at 4pm, Monday to Saturday)
- **Tiburon** – weekly candles
- **Ballena** – monthly candles

The shared trading logic is encapsulated in the base class `Pez`.
Trading periods begin with the open price. Once a valid tail is
identified (after at least 8% of the candle duration has elapsed) and
the price returns to the open, a position is opened in the opposite
direction.

Positions include a take profit and stop loss based on the distance to
the tail. If no exit condition is met before the period ends, the
position is closed at the current market price.

Trade results can be stored in `trade_log` and later exported to an
Excel file using `pandas`.
