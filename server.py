import socket
import threading
import json
from config import SETTINGS

clients = {}
next_id = 1

def broadcast(message, sender_id):
    for client_id, conn in list(clients.items()):
        if client_id != sender_id:
            try:
                conn.send((message + "\n").encode('utf8'))
            except:
                pass

def handle_client(conn, addr, player_id):
    print(f"New player {addr} got ID: {player_id}")
    
    init_msg = json.dumps({"type": "INIT", "id": player_id})
    conn.send((init_msg + "\n").encode('utf8'))

    while True:
        try:
            data = conn.recv(1024).decode('utf8')
            if not data:
                break
                
            for msg in data.split('\n'):
                if msg.strip():
                    broadcast(msg, player_id)
                    
        except Exception as e:
            print(f"Error with player {player_id}: {e}")
            break
            
    print(f"Player {player_id} left.")
    del clients[player_id]
    conn.close()

def server_program():
    global next_id
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SETTINGS.data["host"], SETTINGS.data["port"]))
    server_socket.listen()
    print(f"Server running on port {SETTINGS.data['port']}...")

    while True:
        conn, addr = server_socket.accept()
        clients[next_id] = conn
        thread = threading.Thread(target=handle_client, args=(conn, addr, next_id))
        thread.start()
        next_id += 1

if __name__ == '__main__':
    server_program()