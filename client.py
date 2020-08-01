"""Client to connect to server for Go online
"""
import socket

import pygame

from go_gui_online import GoGuiOnline

HOST = socket.gethostbyname(socket.gethostname())
PORT = 5000


def main():
    """Creates a client and connects to server, then launches the Go game
    """
    pygame.init()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        addr = (HOST, PORT)
        client.connect(addr)

        player_num = int(client.recv(1024).decode("utf-8"))
        print(f"You are player {player_num}")
        game_id = int(client.recv(1024).decode("utf-8"))
        print(f"Game id {game_id}")

        go_game = GoGuiOnline(client, 19, player_num)
        go_game.start_game()

    pygame.quit()


if __name__ == "__main__":
    main()
