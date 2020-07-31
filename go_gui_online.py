"""This module contains the GoGuiOnline class.
GoGuiOnline objects contain a representation of the
Chinese strategy board game Go and is played online.
"""
import pickle
import os
import time

import pygame

from go_gui import GoGui

BLACK = (0, 0, 0)


class GoGuiOnline(GoGui):
    def __init__(self, size, identifier, player):
        super().__init__(size)
        self.id = identifier
        self.ready = False
        self.player = player
        self.color = self.player == 0
        if self.color:
            self.my_color = "BLACK"
            self.op_color = "WHITE"
        else:
            self.my_color = "WHITE"
            self.op_color = "BLACK"
        self.my_turn = False

    def fill_stone(self, pos):
        """Fill stone in position according to mouse click

        Args:
            pos (tuple): pos[0] is x position, pos[1] is y position
        """
        if (
            pos[0] > self.hor_pad - self.buffer
            and pos[0] < self.width - self.hor_pad + self.buffer
            and pos[1] > self.top_pad + self.bot_pad - self.buffer
            and pos[1] < self.height - self.bot_pad + self.buffer
        ):
            # getting row and col from x and y positino
            row = round((pos[1] - self.top_pad - self.bot_pad) / self.spacing)
            col = round((pos[0] - self.hor_pad) / self.spacing)
            if self.board[row, col] == 0:
                # if board position is unfilled

                # save state of game
                self.states.append(
                    (
                        self.board.copy(),
                        self.pointer.copy(),
                        self.white_group.copy(),
                        self.black_group.copy(),
                        self.white_captured,
                        self.black_captured,
                    )
                )

                # updating board
                color_num = 1 if self.color else -1
                if self.color:
                    self.board[row, col] = color_num
                else:
                    self.board[row, col] = color_num

                self.newest_stone = row * self.size + col

                # adding to group
                self.add_group(row, col, color_num)
                # remove captured stones
                self.check_board()

                # checking for Ko, prevent illegal move
                if len(self.states) >= 2 and self.check_ko():
                    # violated Ko, move prevented
                    (
                        self.board,
                        self.pointer,
                        self.white_group,
                        self.black_group,
                        self.white_captured,
                        self.black_captured,
                    ) = self.states.pop()
                else:
                    self.my_turn = False

    def draw_turn(self):
        font = pygame.font.SysFont("timesnewroman", 30)
        color = f"{self.my_color} TURN" if self.my_turn else f"{self.op_color} TURN"
        text = font.render(color, True, BLACK)
        self.display.blit(text, (self.width // 2 - text.get_width() // 2, 15))

    def start_game(self, conn):
        """Start game of Go
        """
        self.running = True
        self.display = pygame.display.set_mode((self.width, self.height))
        self.black_stone_img = pygame.image.load(
            os.path.join(os.getcwd(), "img", "black_stone.png")
        ).convert_alpha()
        self.white_stone_img = pygame.image.load(
            os.path.join(os.getcwd(), "img", "white_stone.png")
        ).convert_alpha()
        self.clock = pygame.time.Clock()
        self.gui_init()
        pygame.mouse.set_visible(False)
        pygame.display.set_caption("GO online")
        start_time = pygame.time.get_ticks()

        if self.player == 0:
            # while True:
            #     time.sleep(2)
            self.my_turn = True
            state = (
                self.board,
                self.pointer,
                self.white_group,
                self.black_group,
                self.white_captured,
                self.black_captured,
            )
            conn.sendall(pickle.dumps(state))

        # main loop of Go
        while self.running:
            self.time_elapsed = int((pygame.time.get_ticks() - start_time) / 1000)

            conn.sendall(str.encode("GET"))
            response = pickle.loads(conn.recv(4096))
            if (self.board != response[0]).any():
                self.my_turn = True
                (
                    self.board,
                    self.pointer,
                    self.white_group,
                    self.black_group,
                    self.white_captured,
                    self.black_captured,
                ) = response

            for event in pygame.event.get():
                # enable closing of display
                if event.type == pygame.QUIT:
                    self.running = False
                    self.score()
                    return
                # getting position of mouse
                if event.type == pygame.MOUSEBUTTONDOWN and self.my_turn:
                    mouse_pos = pygame.mouse.get_pos()
                    self.fill_stone(mouse_pos)
                    state = (
                        self.board,
                        self.pointer,
                        self.white_group,
                        self.black_group,
                        self.white_captured,
                        self.black_captured,
                    )
                    conn.sendall(str.encode("POST"))
                    conn.sendall(pickle.dumps(state))

            self.clock.tick(60)
            self.update_gui()
            pygame.display.update()
