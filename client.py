import socket

from go_gui import GoGui

HOST = "10.10.40.27"
PORT = 5000

if __name__ == "__main__":
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        addr = (HOST, PORT)
        s.connect(addr)
        s.sendall(b"Hello, world")
        data = s.recv(2048)

    print("Received", repr(data))
