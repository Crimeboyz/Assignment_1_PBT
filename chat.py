import pika
import sys
import threading

class ChatClient:
    def __init__(self, username, room="general"):
        self.username = username
        self.room = room
        self.setup_rabbitmq()
        
    def setup_rabbitmq(self):
        # Connect to RabbitMQ (use 'rabbitmq' when in Docker Compose)
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='localhost'))
        self.channel = self.connection.channel()
        
        # Create topic exchange
        self.channel.exchange_declare(
            exchange='chat_rooms', 
            exchange_type='topic')
        
        # Create temporary queue
        result = self.channel.queue_declare(queue='', exclusive=True)
        self.queue_name = result.method.queue
        
        # Bind to room
        self.channel.queue_bind(
            exchange='chat_rooms',
            queue=self.queue_name,
            routing_key=self.room)
        
        # Start message consumer thread
        threading.Thread(target=self.receive_messages, daemon=True).start()
    
    def receive_messages(self):
        def callback(ch, method, properties, body):
            message = body.decode()
            if not message.startswith(f"{self.username}:"):
                print(f"\r{message}\nYou: ", end="", flush=True)
        
        self.channel.basic_consume(
            queue=self.queue_name,
            on_message_callback=callback,
            auto_ack=True)
        
        print(f"\nJoined room '{self.room}'. Start chatting (Ctrl+C to exit)...")
        self.channel.start_consuming()
    
    def send_message(self, message):
        full_message = f"{self.username}: {message}"
        self.channel.basic_publish(
            exchange='chat_rooms',
            routing_key=self.room,
            body=full_message)
    
    def close(self):
        self.connection.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python chat_client.py <username> [room]")
        sys.exit(1)
    
    username = sys.argv[1]
    room = sys.argv[2] if len(sys.argv) > 2 else "general"
    
    client = ChatClient(username, room)
    
    try:
        while True:
            message = input("You: ")
            client.send_message(message)
    except KeyboardInterrupt:
        print("\nDisconnecting...")
    finally:
        client.close()
        