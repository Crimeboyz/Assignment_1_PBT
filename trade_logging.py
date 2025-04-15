import pika
import json
import sqlite3

# Function to save trades in SQLite
def save_trade_to_sqlite(trade):
    connection = sqlite3.connect('trading.db')  # SQLite file-based database
    cursor = connection.cursor()
    
    # Create the trades table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock TEXT,
            price REAL,
            quantity INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert the trade into the table
    cursor.execute('''
        INSERT INTO trades (stock, price, quantity) VALUES (?, ?, ?)
    ''', (trade["stock"], trade["price"], trade["quantity"]))
    
    connection.commit()
    connection.close()
    print(f"Trade saved to SQLite: {trade}")

# Function to process RabbitMQ messages
def log_trade(ch, method, properties, body):
    trade = json.loads(body.decode())  # Deserialize message
    print(f"Logging trade: {trade}")
    save_trade_to_sqlite(trade)  # Save trade to SQLite

# Set up RabbitMQ consumer
def setup_rabbitmq():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='trades', durable=True)
    channel.basic_consume(queue='trades', on_message_callback=log_trade, auto_ack=True)
    
    print("Waiting for trades...")
    channel.start_consuming()

# Start the consumer script
if __name__ == "__main__":
    setup_rabbitmq()
