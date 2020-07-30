import socket

from _thread import start_new_thread

HOST = "10.10.40.27"
PORT = 5000


def threaded_client(client):
    with client:
        while True:
            data = client.recv(2048)
            if not data:
                print("Disconnected")
                break
            reply = data.decode("utf-8")
            print(f"Received: {reply}")
            print(f"Sending: {reply}")
            client.sendall(str.encode(reply))


if __name__ == "__main__":
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen(2)
        print("Server started, listening for connections")

        while True:
            conn, addr = s.accept()
            print(f"Connected to: {addr}")

            start_new_thread(threaded_client, (conn,))
