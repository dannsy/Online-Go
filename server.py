import pickle
import socket
import threading

HOST = "10.10.40.27"
PORT = 5000

GAMES = {}


def threaded_client(client, num, game_id):
    with client:
        # sending player number
        client.send(str.encode(str(num)))
        # sending game id
        client.send(str.encode(str(game_id)))

        if num == 0:
            GAMES[game_id] = pickle.loads(client.recv(4096))
            print(f"Player {num} started game {game_id}")
        else:
            print(f"Player {num} connected to game {game_id}")

        while True:
            data = client.recv(4096).decode()

            if not data:
                break
            else:
                if data == "GET":
                    client.sendall(pickle.dumps(GAMES[game_id]))
                elif data == "POST":
                    GAMES[game_id] = pickle.loads(client.recv(4096))
                else:
                    break

    print(f"Player {num} lost connection")
    # try:
    #     del GAMES[game_id]
    #     print("Closing game", game_id)
    # except:
    #     pass


def main():
    """Starts the server and waits for players to connect
    """
    # counts how many players have connected to server
    id_count = 0

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print("Server started, listening for connections")

        while True:
            conn, addr = s.accept()
            print(f"Connected to: {addr}")

            # every two player means one game
            game_id = id_count // 2
            player_num = id_count % 2

            player = threading.Thread(
                target=threaded_client, args=[conn, player_num, game_id]
            )
            player.start()

            id_count += 1


if __name__ == "__main__":
    main()
