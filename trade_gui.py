import tkinter as tk
import sqlite3
import threading
import time

def fetch_latest_trade(stock):
    connection = sqlite3.connect('trading.db') # Connects to SQLite database

    cursor = connection.cursor()
    query = "SELECT price from trades where stock = ? Order by id Desc Limit 1"
    cursor.execute(query, (stock,))
    result = cursor.fetchone()
    connection.close()
    return result[0] if result else "No Trades Yet"

def update_price():
    stock = stock_entry.get().upper()

    if stock not in ["AAPL", "TSLA"]:
        price_label.config(text="Invalid stock symbol. Please use AAPL or TSLA.")
        return
    
    latest_price = fetch_latest_trade(stock)

    price_label.config(text=f"Latest price for {stock}: ${latest_price}")

    root.after(5000, update_price)

# GUI Setup
root = tk.Tk()
root.title("Latest Trade Price Viewer")
root.geometry("800x400")

tk.Label(root, text="Enter Stock Symbol (e.g., AAPL or TSLA): ").pack(pady=10)

stock_entry = tk.Entry(root, font=("Arial", 16))
stock_entry.pack(pady=5)

tk.Button(root, text="Fetch latest price", command=update_price, font=("Arial", 14)).pack(pady=10)

price_label = tk.Label(root, text="", font=("Arial", 20), fg="green")
price_label.pack(pady=10)

root.mainloop()
