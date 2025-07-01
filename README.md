# Trading System - PECES

This repository contains an early implementation of the **PECES** module
condensed into a single script for simplicity.  Each `Pez` represents a
trading agent that operates on different market timeframes:

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
the tail. Once price moves halfway from the entry to the take profit
level, the stop loss is moved from the tail to a new level just 10% of
that distance away from the entry to lock in a small gain. These rules
apply indistintamente para operaciones de **compra** (largas) o **venta**
(cortas). If no exit condition is met before the period ends, the
position is closed at the current market price.

Trade results can be stored in `trade_log` and later exported to an
Excel file using `pandas`.

All of the classes and a small demonstration live inside the single
`example.py` file.  Running it will open a long trade and then a short
trade using the same `Sardina` instance, showing that the rules work
igual para ambos sentidos.

## GUI Demo with MetaTrader 5

The script `sardina_mt5_gui.py` provides a simple Tkinter interface to
start or stop a real-time `Sardina` bot. It connects to MetaTrader 5,
fetches minute data and logs trade events in a text box. When a trade
is opened, it also places a **demo** order on MetaTrader 5 with a small
lote de `0.01`. Use the "Mostrar Operaciones" button to view the
`trade_log` at any time. Ensure the `MetaTrader5` Python package is
installed and that a MetaTrader 5 terminal is available for the
connection to succeed.
