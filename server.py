import pickle
import socket
import threading

HOST = socket.gethostbyname(socket.gethostname())
PORT = 5000

GAMES = {}
GAMES_STARTED = {}


def threaded_client(client, num, game_id):
    with client:
        # sending player number
        client.send(str.encode(str(num)))
        # sending game id
        client.send(str.encode(str(game_id)))

        if num == 0:
            GAMES[game_id] = pickle.loads(client.recv(4096))
            print(f"Player {num} started game {game_id}")
            GAMES_STARTED[game_id] = False
        else:
            print(f"Player {num} connected to game {game_id}")
            GAMES_STARTED[game_id] = True

        while True:
            data = client.recv(4096).decode()

            if not data:
                break
            else:
                if data == "GET":
                    if GAMES_STARTED[game_id]:
                        client.sendall(pickle.dumps(GAMES[game_id]))
                    else:
                        client.sendall(pickle.dumps(False))
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
