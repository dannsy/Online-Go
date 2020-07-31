import socket

import pygame

from go_gui_online import GoGuiOnline

HOST = "10.10.40.27"
PORT = 5000


def main():
    pygame.init()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        addr = (HOST, PORT)
        client.connect(addr)

        player_num = int(client.recv(1024).decode("utf-8"))
        print(f"You are player {player_num}")
        game_id = int(client.recv(1024).decode("utf-8"))
        print(f"Game id {game_id}")

        go_game = GoGuiOnline(19, game_id, player_num)
        go_game.start_game(client)


if __name__ == "__main__":
    main()
