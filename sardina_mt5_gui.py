from datetime import datetime
import MetaTrader5 as mt5
import tkinter as tk
from threading import Thread
import time


def enviar_orden(symbol: str, direction: int, volume: float = 0.01):
    """Send a real order to MetaTrader 5."""
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        print("❌ No se pudo obtener el tick de", symbol)
        return

    price = tick.ask if direction == 1 else tick.bid
    order_type = mt5.ORDER_TYPE_BUY if direction == 1 else mt5.ORDER_TYPE_SELL

    result = mt5.order_send(
        {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": order_type,
            "price": price,
            "deviation": 10,
            "magic": 123456,
            "comment": "Bot Python",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
    )

    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print("❌ Error al enviar orden:", result)
    else:
        print("✅ Orden ejecutada:", result)


class Pez:
    """Base class for trading bots."""

    timeframe = None  # seconds
    start_offset = 0

    def __init__(self, symbol: str):
        self.symbol = symbol
        self.position = None
        self.trade_log = []
        self.running = False
        self.open_time = None
        self.open_price = None
        self.tail_price = None
        self.tail_time = None

    def new_period(self, open_price: float, open_time: datetime):
        """Start a new trading period."""
        self.open_price = open_price
        self.open_time = open_time
        self.tail_price = None
        self.tail_time = None
        self.position = None

    def update_price(self, price: float, current_time: datetime):
        """Process price updates within the current period."""
        if self.open_time is None:
            return

        elapsed = (current_time - self.open_time).total_seconds()
        if elapsed >= 0.08 * self.timeframe:
            if self.tail_price is None:
                self.tail_price = price
                self.tail_time = current_time
            else:
                if abs(price - self.open_price) > abs(self.tail_price - self.open_price):
                    self.tail_price = price
                    self.tail_time = current_time

        if self.tail_price is not None and self.position is None:
            if price == self.open_price:
                direction = 1 if self.tail_price < self.open_price else -1
                tp_distance = abs(self.open_price - self.tail_price)
                tp_price = price + direction * tp_distance
                self.position = {
                    "direction": direction,
                    "entry_price": price,
                    "tp_price": tp_price,
                    "sl_price": self.tail_price,
                    "trail_triggered": False,
                    "status": "open",
                }
                enviar_orden(self.symbol, direction, volume=0.01)
        elif self.position and self.position["status"] == "open":
            pos = self.position
            tp_distance = pos["tp_price"] - pos["entry_price"]

            if not pos["trail_triggered"]:
                mid_point = pos["entry_price"] + 0.5 * tp_distance
                hit_mid = price >= mid_point if tp_distance > 0 else price <= mid_point
                if hit_mid:
                    pos["sl_price"] = pos["entry_price"] + 0.1 * tp_distance
                    pos["trail_triggered"] = True

            if pos["direction"] == 1:
                if price >= pos["tp_price"]:
                    self.close_position(pos["tp_price"], reason="take_profit")
                elif price <= pos["sl_price"]:
                    self.close_position(pos["sl_price"], reason="stop_loss")
            else:
                if price <= pos["tp_price"]:
                    self.close_position(pos["tp_price"], reason="take_profit")
                elif price >= pos["sl_price"]:
                    self.close_position(pos["sl_price"], reason="stop_loss")

    def close_position(self, price: float, reason: str):
        """Close the current position and record the trade result."""
        if self.position and self.position["status"] == "open":
            pnl = (price - self.position["entry_price"]) * self.position["direction"]
            self.trade_log.append(
                {
                    "symbol": self.symbol,
                    "direction": self.position["direction"],
                    "entry": self.position["entry_price"],
                    "exit": price,
                    "pnl": pnl,
                    "reason": reason,
                    "status": "closed",
                }
            )
            self.position["status"] = "closed"


class Sardina(Pez):
    """Hourly trading bot."""

    timeframe = 60 * 60
    start_offset = 0


class BotApp:
    """Simple Tkinter UI to start/stop the Sardina bot."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Panel de Control del Bot")
        self.symbol_var = tk.StringVar(value="EURUSD")

        tk.Label(root, text="Símbolo:").pack()
        tk.Entry(root, textvariable=self.symbol_var).pack(pady=5)

        self.status = tk.Label(root, text="Estado: Inactivo", fg="red")
        self.status.pack(pady=5)

        self.start_btn = tk.Button(root, text="Iniciar Bot", command=self.start_bot)
        self.start_btn.pack(pady=5)

        self.stop_btn = tk.Button(root, text="Detener Bot", command=self.stop_bot, state="disabled")
        self.stop_btn.pack(pady=5)

        self.log_btn = tk.Button(root, text="Mostrar Operaciones", command=self.show_log)
        self.log_btn.pack(pady=5)

        self.log_text = tk.Text(root, height=10, width=60)
        self.log_text.pack(pady=10)

        self.bot = None
        self.thread = None

    def start_bot(self):
        symbol = self.symbol_var.get()
        self.bot = Sardina(symbol)
        self.bot.running = True
        self.thread = Thread(target=self.run_bot, daemon=True)
        self.thread.start()
        self.status.config(text="Estado: Ejecutando", fg="green")
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")

    def stop_bot(self):
        if self.bot:
            self.bot.running = False
            self.status.config(text="Estado: Detenido", fg="red")
            self.start_btn.config(state="normal")
            self.stop_btn.config(state="disabled")

    def show_log(self):
        if not self.bot:
            return
        win = tk.Toplevel(self.root)
        win.title("Historial de Operaciones")
        text = tk.Text(win, height=15, width=70)
        text.pack()
        for trade in self.bot.trade_log:
            text.insert(tk.END, f"{trade}\n")

    def run_bot(self):
        if not mt5.initialize():
            self.log_text.insert(tk.END, "Error al conectar con MetaTrader 5\n")
            return

        pez = self.bot
        last_period_time = None

        while pez.running:
            rates = mt5.copy_rates_from_pos(pez.symbol, mt5.TIMEFRAME_M1, 0, 1)
            if rates is None or len(rates) == 0:
                time.sleep(1)
                continue

            current_rate = rates[0]
            current_time = datetime.fromtimestamp(current_rate["time"])
            current_price = current_rate["close"]

            if current_time.minute == 0 and current_time.second == 0:
                if last_period_time is None or current_time > last_period_time:
                    pez.new_period(open_price=current_price, open_time=current_time)
                    last_period_time = current_time
                    self.log_text.insert(
                        tk.END,
                        f"\nNuevo período exacto: {current_time} | Precio: {current_price}",
                    )

            pez.update_price(current_price, current_time)

            if pez.trade_log and pez.trade_log[-1]["status"] == "closed":
                self.log_text.insert(tk.END, f"\nTrade cerrado: {pez.trade_log[-1]}")

            self.log_text.see(tk.END)
            time.sleep(10)

        mt5.shutdown()
        self.log_text.insert(tk.END, "\nBot detenido y conexión cerrada.\n")
        self.log_text.see(tk.END)


if __name__ == "__main__":
    root = tk.Tk()
    app = BotApp(root)
    root.mainloop()
