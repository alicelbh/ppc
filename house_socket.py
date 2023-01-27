import sys
import socket

HOST = "localhost"
PORT = 1790

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
    client_socket.connect((HOST, PORT))
    data = str(2000)

    client_socket.send(data.encode())
    resp = client_socket.recv(1024)
    if not len(resp):
        print("The socket connection has been closed!")
        sys.exit(1)
    print("Server response:", resp.decode())
