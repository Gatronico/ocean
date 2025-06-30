from datetime import datetime, timedelta


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
        # Actualiza el precio de la vela y gestiona colas y posiciones
        # Determinar si podemos registrar la cola segun el tiempo transcurrido
        elapsed = (current_time - self.open_time).total_seconds()
        if elapsed >= 0.08 * self.timeframe:
            if self.tail_price is None:
                # Primera vez que vemos la cola
                self.tail_price = price
                self.tail_time = current_time
            else:
                # Si el nuevo precio está más lejos del punto de apertura, actualizamos la cola
                if abs(price - self.open_price) > abs(self.tail_price - self.open_price):
                    self.tail_price = price
                    self.tail_time = current_time

        # Comprobamos si abrimos una posición cuando el precio vuelve al punto de apertura
        if self.tail_price is not None and self.position is None:
            if price == self.open_price:
                # Open position opposite to tail direction
                # Calculamos la distancia hasta la cola para definir el take profit
                direction = 1 if self.tail_price < self.open_price else -1
                tp_distance = abs(self.open_price - self.tail_price)
                tp_price = price + direction * tp_distance
                self.position = {
                    "direction": direction,
                    "entry_price": price,
                    "tp_price": tp_price,
                    # Stop loss inicial ubicado en la cola
                    # Indicador para saber si activamos trailing stop
                    "sl_price": self.tail_price,
                    "trail_triggered": False,
                    "status": "open",
                }
        elif self.position and self.position["status"] == "open":
            pos = self.position
            # Gestión de la posición abierta
            tp_distance = pos["tp_price"] - pos["entry_price"]

            # Cuando el precio avance un 50% hacia el take profit, movemos el stop loss
            if not pos["trail_triggered"]:
                # Punto medio entre la entrada y el take profit
                mid_point = pos["entry_price"] + 0.5 * tp_distance
                hit_mid = price >= mid_point if tp_distance > 0 else price <= mid_point
                if hit_mid:
                    # Colocamos el stop loss al 10% de la distancia para asegurar ganancia
                    pos["sl_price"] = pos["entry_price"] + 0.1 * tp_distance
                    pos["trail_triggered"] = True

            # Comprobamos si se alcanza el take profit o el stop loss
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

    def close_position(self, price, reason):
        # Cierra la posición abierta y guarda el resultado de la operación
        """Close any open position at price."""
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
                }
            )
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

# Demonstración en un solo flujo de código usando la misma instancia
if __name__ == "__main__":
    pez = Sardina("EUR/USD")

    # ----- Primera operación: larga -----
    start = datetime.now()
    pez.new_period(open_price=1.1000, open_time=start)

    # El precio baja y regresa al punto de apertura, lo que activa una entrada
    # en largo.
    for i in range(1, 60):
        current = start + timedelta(minutes=i)
        price = 1.1000 + 0.0001 * (i - 30) / 30
        pez.update_price(price, current)

    pez.close_position(1.1020, reason="end_of_period")
    print("Primera operación:", pez.trade_log[-1])

    # ----- Segunda operación: corta -----
    start_short = start + timedelta(hours=1)
    pez.new_period(open_price=1.1000, open_time=start_short)

    # El precio sube por encima de la apertura y luego vuelve, activando una
    # posición corta.
    price_path = [
        1.1010,
        1.1015,
        1.1020,
        1.1010,
        1.1000,
        1.0995,
        1.0990,
        1.0985,
        1.0980,
    ]

    for i, p in enumerate(price_path, 1):
        pez.update_price(p, start_short + timedelta(seconds=i * 300))

    pez.close_position(1.0980, reason="end_of_period")

    # Mostrar el registro completo de operaciones
    print("Segunda operación:", pez.trade_log[-1])
    print("Resumen:", pez.trade_log)
