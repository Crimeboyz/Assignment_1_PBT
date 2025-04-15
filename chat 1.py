import pika
import sys
import threading
import time

class ChatApplication:
    def __init__(self, username, room="general", host="localhost"):
        self.username = username
        self.room = room
        self.host = host
        self.should_stop = threading.Event()  # Flag for graceful shutdown
        self.setup_rabbitmq()

    def setup_rabbitmq(self):
        """Establish RabbitMQ connection and setup exchange/queue"""
        try:
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=self.host))
            self.channel = self.connection.channel()
            
            # Topic exchange for multiple rooms
            self.channel.exchange_declare(
                exchange="chat_rooms",
                exchange_type="topic",
                durable=False)  # Changed to non-durable for simplicity
            
            # Temporary queue for this user
            result = self.channel.queue_declare(queue="", exclusive=True)
            self.queue_name = result.method.queue
            
            # Bind to specified room
            self.channel.queue_bind(
                exchange="chat_rooms",
                queue=self.queue_name,
                routing_key=self.room)
            
            # Start message consumer thread
            self.consumer_thread = threading.Thread(
                target=self.receive_messages,
                daemon=True)
            self.consumer_thread.start()
            
            print(f"\n[{self.username}] Joined room: '{self.room}'")
            print("Type messages below (Ctrl+C or /exit to quit):")
            
        except pika.exceptions.AMQPConnectionError as e:
            print(f"Failed to connect to RabbitMQ: {e}")
            sys.exit(1)

    def receive_messages(self):
        """Handle incoming messages"""
        def callback(ch, method, properties, body):
            if self.should_stop.is_set():
                return
            message = body.decode()
            # Skip echoing your own messages
            if not message.startswith(f"[{self.username}]"):
                print(f"\r{message}\n> ", end="", flush=True)
        
        try:
            self.channel.basic_consume(
                queue=self.queue_name,
                on_message_callback=callback,
                auto_ack=True)
            self.channel.start_consuming()
        except Exception as e:
            if not self.should_stop.is_set():
                print(f"\nError receiving messages: {e}")

    def send_message(self, message):
        """Publish message to chat room"""
        try:
            timestamp = time.strftime("%H:%M:%S")
            formatted_msg = f"[{timestamp}] [{self.username}] {message}"
            self.channel.basic_publish(
                exchange="chat_rooms",
                routing_key=self.room,
                body=formatted_msg)
        except Exception as e:
            print(f"Failed to send message: {e}")

    def cleanup(self):
        """Graceful shutdown"""
        self.should_stop.set()
        if hasattr(self, 'channel') and self.channel.is_open:
            self.channel.stop_consuming()
        if hasattr(self, 'connection') and self.connection.is_open:
            self.connection.close()

def main():
    if len(sys.argv) < 2:
        print("Usage: python chat_app.py <username> [room] [host]")
        print("Example: python chat_app.py Alice general localhost")
        sys.exit(1)
    
    username = sys.argv[1]
    room = sys.argv[2] if len(sys.argv) > 2 else "general"
    host = sys.argv[3] if len(sys.argv) > 3 else "localhost"
    
    chat = ChatApplication(username, room, host)
    
    try:
        while True:
            message = input("> ")
            if message.lower().strip() == '/exit':
                break
            chat.send_message(message)
    except (KeyboardInterrupt, EOFError):
        print("\nExiting chat...")
    finally:
        chat.cleanup()

if __name__ == "__main__":
    main()