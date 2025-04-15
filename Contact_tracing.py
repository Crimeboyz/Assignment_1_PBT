import pika
import json
import random
import threading
import time
import tkinter as tk
from collections import defaultdict

# RabbitMQ connection parameters
RABBITMQ_HOST = 'localhost'
POSITION_TOPIC = 'position'
QUERY_TOPIC = 'query'
QUERY_RESPONSE_TOPIC = 'query-response'

# Environment settings
environment_size = (10, 10)  # Default size, can be changed
positions = {}  # Tracks people's positions
contacts = defaultdict(list)  # Tracks contacts

def setup_rabbitmq_channel():
    """Sets up a connection and channel for RabbitMQ."""
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
    channel = connection.channel()
    channel.queue_declare(queue=POSITION_TOPIC)
    channel.queue_declare(queue=QUERY_TOPIC)
    channel.queue_declare(queue=QUERY_RESPONSE_TOPIC)
    return connection, channel

def tracker():
    """Tracker listens for position updates and logs contacts between individuals."""
    connection, channel = setup_rabbitmq_channel()
    
    def position_callback(ch, method, properties, body):
        """Handles incoming position updates and tracks contacts."""
        data = json.loads(body)
        person_id = data['id']
        new_position = tuple(data['position'])
        
        if person_id in positions:
            old_position = positions[person_id]
            if old_position != new_position:
                print(f"{person_id} moved from {old_position} to {new_position}")
        else:
            print(f"{person_id} started at {new_position}")

        # Check for contact with other individuals
        for other_id, pos in positions.items():
            if other_id != person_id and pos == new_position:
                contacts[person_id].append((other_id, time.time()))
                contacts[other_id].append((person_id, time.time()))
                print(f"Contact recorded: {person_id} <-> {other_id}")

        positions[person_id] = new_position

    def query_callback(ch, method, properties, body):
        """Handles contact query requests and responds with contact history."""
        queried_id = body.decode()
        response = {queried_id: sorted(contacts[queried_id], key=lambda x: x[1], reverse=True)}
        channel.basic_publish(exchange='', routing_key=QUERY_RESPONSE_TOPIC, body=json.dumps(response))

    channel.basic_consume(queue=POSITION_TOPIC, on_message_callback=position_callback, auto_ack=True)
    channel.basic_consume(queue=QUERY_TOPIC, on_message_callback=query_callback, auto_ack=True)
    print("Tracker running...")
    channel.start_consuming()

def person(person_id, speed):
    """Simulates a person's movement within the environment."""
    connection, channel = setup_rabbitmq_channel()
    x, y = random.randint(0, environment_size[0]-1), random.randint(0, environment_size[1]-1)
    channel.basic_publish(exchange='', routing_key=POSITION_TOPIC, body=json.dumps({'id': person_id, 'position': [x, y]}))
    
    while True:
        time.sleep(speed)
        dx, dy = random.choice([(-1,0), (1,0), (0,-1), (0,1)])
        x, y = max(0, min(environment_size[0]-1, x+dx)), max(0, min(environment_size[1]-1, y+dy))
        channel.basic_publish(exchange='', routing_key=POSITION_TOPIC, body=json.dumps({'id': person_id, 'position': [x, y]}))

def query(person_id):
    """Sends a contact query request for a given person and prints the response."""
    connection, channel = setup_rabbitmq_channel()
    channel.basic_publish(exchange='', routing_key=QUERY_TOPIC, body=person_id)
    
    def response_callback(ch, method, properties, body):
        """Handles the response from the tracker and prints the contact history."""
        print(json.loads(body))
        connection.close()
        exit()
    
    channel.basic_consume(queue=QUERY_RESPONSE_TOPIC, on_message_callback=response_callback, auto_ack=True)
    print(f"Querying contacts for {person_id}...")
    channel.start_consuming()

def gui():
    """Graphical User Interface to display the environment and query contact history."""
    root = tk.Tk()
    root.title("Contact Tracing GUI")
    canvas = tk.Canvas(root, width=environment_size[0]*50, height=environment_size[1]*50, bg="white")
    canvas.pack()
    
    def update_display():
        """Updates the canvas with current positions of people in the environment."""
        canvas.delete("all")
        for person_id, (x, y) in positions.items():
            canvas.create_oval(x*50+10, y*50+10, x*50+40, y*50+40, fill="blue")
            canvas.create_text(x*50+25, y*50+25, text=person_id, fill="white")
        root.after(500, update_display)
    
    update_display()
    root.mainloop()

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python script.py [tracker|person|query|gui] [args]")
    elif sys.argv[1] == "tracker":
        tracker()
    elif sys.argv[1] == "person" and len(sys.argv) == 4:
        threading.Thread(target=person, args=(sys.argv[2], float(sys.argv[3]))).start()
    elif sys.argv[1] == "query" and len(sys.argv) == 3:
        query(sys.argv[2])
    elif sys.argv[1] == "gui":
        gui()
    else:
        print("Invalid arguments!")
