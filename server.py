import socket
import threading
from config import SETTINGS

def handle_client(conn, addr):
    print(f"New connection from {addr}")
    while True:
        try:
            message = conn.recv(8192).decode()
            if message:
                print(f"Position of {addr}: {message}")
        except Exception as e:
            print(f"Error with connection from {addr}: {e}")
            break
    conn.close()

def server_program():
    server_socket = socket.socket()
    server_socket.bind((SETTINGS.data["host"], SETTINGS.data["port"]))
    server_socket.listen()

    while True:
        conn, addr = server_socket.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"Active connections: {threading.active_count() - 1}")

if __name__ == '__main__':
    server_program()