class Pez:
    """Base class for trading modules."""

    timeframe = None  # seconds
    start_offset = 0  # seconds from start of timeframe to trade

    def __init__(self, symbol):
        self.symbol = symbol
        self.position = None
        self.trade_log = []

    def new_period(self, open_price, open_time):
        """Initialize new period with open price and time."""
        self.open_price = open_price
        self.open_time = open_time
        self.tail_price = None
        self.tail_time = None
        self.position = None

    def update_price(self, price, current_time):
        """Update price during the period."""
        # Determine if we can record tail
        elapsed = (current_time - self.open_time).total_seconds()
        if elapsed >= 0.08 * self.timeframe:
            if self.tail_price is None:
                self.tail_price = price
                self.tail_time = current_time
            else:
                # Update tail if further from open
                if abs(price - self.open_price) > abs(self.tail_price - self.open_price):
                    self.tail_price = price
                    self.tail_time = current_time

        # Check if we open position when price returns to open
        if self.tail_price is not None and self.position is None:
            if price == self.open_price:
                # Open position opposite to tail direction
                direction = 1 if self.tail_price < self.open_price else -1
                self.position = {
                    "direction": direction,
                    "entry_price": price,
                    "tp": abs(self.open_price - self.tail_price),
                    "sl": self.tail_price,
                    "status": "open",
                }

    def close_position(self, price, reason):
        """Close any open position at price."""
        if self.position and self.position["status"] == "open":
            pnl = (price - self.position["entry_price"]) * self.position["direction"]
            self.trade_log.append({
                "symbol": self.symbol,
                "direction": self.position["direction"],
                "entry": self.position["entry_price"],
                "exit": price,
                "pnl": pnl,
                "reason": reason,
            })
            self.position["status"] = "closed"


class Sardina(Pez):
    timeframe = 60 * 60
    start_offset = 0


class Atun(Pez):
    timeframe = 60 * 60 * 24
    start_offset = 16 * 60 * 60  # 4pm local time


class Tiburon(Pez):
    timeframe = 60 * 60 * 24 * 7
    start_offset = 0


class Ballena(Pez):
    timeframe = 60 * 60 * 24 * 30  # approximate month
    start_offset = 0

