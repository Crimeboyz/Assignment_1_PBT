import pika
import json

def place_order(order_type, stock, price, quantitiy):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='orders', durable=True)

    order = {
        "type": order_type,
        "stock": stock,
        "price": price,
        "quantity": quantitiy
    }
    channel.basic_publish(exchange='', routing_key='orders', body=json.dumps(order))
    print(f"Order placed: {order}")
    connection.close()

while True:
    order_type = input("Enter order type (buy/sell): ")
    stock = input("Enter stock symbol (e.g., AAPL, TSLA): ")
    price = float(input("Enter price: "))
    quantity = int(input("Enter quantity: "))
    place_order(order_type, stock, price, quantity)
