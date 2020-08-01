"""Server for Go online
"""
import pickle
import socket
import threading

HOST = socket.gethostbyname(socket.gethostname())
PORT = 5000

GAMES = {}
GAMES_STARTED = {}


def threaded_client(serve, num, game_id):
    """For each player connected, manage which game the player
    plays, and determine whether game has started. Also facilitate
    the communication of game state between players

    Args:
        serve (client connection): the connection to the client/player
        num (int): the player number (0 and 1)
        game_id (int): the game number
    """
    connected = True
    try:
        with serve:
            # sending player number
            serve.send(str.encode(str(num)))
            # sending game id
            serve.send(str.encode(str(game_id)))

            if num == 0:
                GAMES[game_id] = pickle.loads(serve.recv(4096))
                print(f"Player {num} started game {game_id}")
                GAMES_STARTED[game_id] = False
            else:
                print(f"Player {num} connected to game {game_id}")
                if game_id in GAMES_STARTED:
                    GAMES_STARTED[game_id] = True
                else:
                    connected = False

            while connected:
                data = serve.recv(4096).decode()

                if not data:
                    connected = False
                else:
                    if data == "GET":
                        if GAMES_STARTED[game_id]:
                            serve.sendall(pickle.dumps(GAMES[game_id]))
                        else:
                            serve.sendall(pickle.dumps(False))
                    elif data == "POST":
                        GAMES[game_id] = pickle.loads(serve.recv(4096))
                    else:
                        connected = False

        print(f"Player {num} lost connection")
        del GAMES_STARTED[game_id]
    except KeyError:
        print(f"Player {num} lost connection")


def main():
    """Starts the server and waits for players to connect
    """
    # counts how many players have connected to server
    id_count = 0

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((HOST, PORT))
        server.listen()
        print("Server started, listening for connections")

        #### close server after 5 minutes of inactivity
        while True:
            conn, addr = server.accept()
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
