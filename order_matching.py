import pika
import json
from heapq import heappush, heappop

# Initializes order books for multiple stocks
order_books = {
    "AAPL": {"buy_orders": [], "sell_orders": []},
    "TSLA": {"buy_orders": [], "sell_orders": []}
}

def match_orders(stock):
    buy_orders = order_books[stock]["buy_orders"]
    sell_orders = order_books[stock]["sell_orders"]

    while buy_orders and sell_orders:
        # Gets the highest buy order and lowest sell order
        highest_buy = heappop(buy_orders)
        lowest_sell = heappop(sell_orders)

        if -highest_buy["price"] >= lowest_sell["price"]:
            traded_quantity = min(highest_buy["quantity"], lowest_sell["quantity"])
            trade_price = lowest_sell["price"]

            trade = {
                "stock": stock,
                "price": trade_price,
                "quantity": traded_quantity
            }
            publish_trade(trade)

            highest_buy["quantity"] -= traded_quantity
            lowest_sell["quantity"] -= traded_quantity

            if highest_buy["quantity"] > 0:
                heappush(buy_orders, highest_buy)
            if lowest_sell["quantity"] > 0:
                heappush(sell_orders, lowest_sell)
        else:
            # Prices don't match, reinsert orders back into the book and break
            heappush(buy_orders, highest_buy)
            heappush(sell_orders, lowest_sell)
            break

def process_order(order):
    stock = order["stock"]
    if order["type"] == "buy":
        heappush(order_books[stock]["buy_orders"], {
            "price": -order["price"],
            "quantity": order["quantity"],
            "order_id": order.get("id", None)
        })
    elif order["type"] == "sell":
        heappush(order_books[stock]["sell_orders"], {
            "price": order["price"],
            "quantity": order["quantity"],
            "order_id": order.get("id", None)
        })

    match_orders(stock)

def publish_trade(trade):
    print(f"Attempting to publish trade: {trade}")  # Debug print

    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='trades', durable=True)

    channel.basic_publish(exchange='', routing_key='trades', body=json.dumps(trade))
    print(f"Trade published: {trade}")
    connection.close()

def callback(ch, method, properties, body):
    order = json.loads(body.decode())  # Fix: Use json.loads()
    print(f"Received order: {order}")
    process_order(order)

def setup_rabbitmq():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='orders', durable=True)
    channel.basic_consume(queue='orders', on_message_callback=callback, auto_ack=True)
    print("Waiting for orders...")
    channel.start_consuming()

if __name__ == "__main__":
    setup_rabbitmq()


