import tkinter as tk
from tkinter import scrolledtext
from chat import ChatApplication  # Your existing chat implementation

class ChatGUI:
    def __init__(self, username, room_name, host='localhost', port=5672):
        self.chat = ChatApplication(username, room_name, host, port)
        self.root = tk.Tk()
        self.setup_ui()
        self.chat.receive_callback = self.display_message
        self.chat.join_room()
        
    def setup_ui(self):
        self.root.title(f"Chat - {self.chat.username}")
        
        # Message display
        self.message_area = scrolledtext.ScrolledText(self.root, state='disabled')
        self.message_area.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        
        # Message entry
        self.entry = tk.Entry(self.root, width=50)
        self.entry.pack(padx=10, pady=5)
        self.entry.bind("<Return>", self.send_message)
        self.entry.focus_set()
        
    def send_message(self, event):
        message = self.entry.get()
        if message:
            self.chat.send_message(message)
            self.display_message(f"You: {message}")
            self.entry.delete(0, tk.END)
            
    def display_message(self, message):
        self.message_area.config(state='normal')
        self.message_area.insert(tk.END, message + "\n")
        self.message_area.config(state='disabled')
        self.message_area.see(tk.END)
        
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python chat_gui.py <username> <room_name> [host] [port]")
        sys.exit(1)
        
    username = sys.argv[1]
    room_name = sys.argv[2]
    host = sys.argv[3] if len(sys.argv) > 3 else 'localhost'
    port = int(sys.argv[4]) if len(sys.argv) > 4 else 5672
    
    gui = ChatGUI(username, room_name, host, port)
    gui.run()

