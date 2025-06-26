from datetime import datetime, timedelta

from peces.peces import Sardina

# Example usage of the Sardina module
if __name__ == "__main__":
    pez = Sardina("EUR/USD")

    start = datetime.now()
    pez.new_period(open_price=1.1000, open_time=start)

    # Simulate price movement within an hour candle
    for i in range(1, 60):
        current = start + timedelta(minutes=i)
        # Example price oscillation
        price = 1.1000 + 0.0001 * (i - 30) / 30
        pez.update_price(price, current)

    # Close at end of period
    end_price = 1.1020
    pez.close_position(end_price, reason="end_of_period")

    print(pez.trade_log)
