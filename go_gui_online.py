"""This module contains the GoGuiOnline class.
GoGuiOnline objects contain a representation of the
Chinese strategy board game Go and is played online.
"""
import pickle
import os
from collections import namedtuple

import pygame

from go_gui import GoGui

Color = namedtuple("Color", ["r", "g", "b"])
BLACK = Color(0, 0, 0)
GREY = Color(150, 150, 150)


class GoGuiOnline(GoGui):
    """Class representing GUI for Go online

    Args:
        GoGui: Base class for GUI of Go
    """

    def __init__(self, conn, size, player):
        super().__init__(size)
        self.player = player
        self.conn = conn
        self.color = self.player == 0
        if self.color:
            self.my_color = "BLACK"
            self.op_color = "WHITE"
        else:
            self.my_color = "WHITE"
            self.op_color = "BLACK"
        self.my_turn = False
        self.started = False
        self.current_gui = self.wait_gui

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
                if (len(self.states) >= 2 and self.check_ko()) or self.board[
                    row, col
                ] == 0:
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
                    state = (
                        self.board.copy(),
                        self.pointer.copy(),
                        self.white_group.copy(),
                        self.black_group.copy(),
                        self.white_captured,
                        self.black_captured,
                    )
                    self.states.append(state)

                    state = list(state)
                    state.insert(0, self.op_color)
                    state = tuple(state)
                    self.my_turn = False
                    self.conn.sendall(str.encode("POST"))
                    self.conn.sendall(pickle.dumps(state))

        if (
            pos[0] > self.but0_x
            and pos[0] < self.but0_x + self.but_width
            and pos[1] > self.but0_y
            and pos[1] < self.but0_y + self.but_height
        ):
            self.my_turn = False
            state = (
                self.op_color,
                self.board.copy(),
                self.pointer.copy(),
                self.white_group.copy(),
                self.black_group.copy(),
                self.white_captured,
                self.black_captured,
            )
            self.conn.sendall(str.encode("POST"))
            self.conn.sendall(pickle.dumps(state))

    def draw_turn(self, font):
        """Drawing which player's turn it is

        Args:
            font (pygame font): font to use to draw
        """
        color = f"{self.my_color} TURN" if self.my_turn else f"{self.op_color} TURN"
        text = font.render(color, True, BLACK)
        self.display.blit(text, (self.width // 2 - text.get_width() // 2, 15))

    def wait_gui(self):
        """GUI for waiting for opponent to connect
        """
        self.display.fill(GREY)

        font = pygame.font.SysFont("timesnewroman", 35)
        text = font.render("Waiting for opponent...", True, BLACK)
        self.display.blit(
            text,
            (
                (self.width - text.get_width()) // 2,
                (self.height - text.get_height()) // 2,
            ),
        )

    def start_game(self):
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
        self.wait_gui()
        pygame.display.set_caption("GO online")

        if self.player == 0:
            self.my_turn = True
            state = (
                "BLACK",
                self.board,
                self.pointer,
                self.white_group,
                self.black_group,
                self.white_captured,
                self.black_captured,
            )
            self.conn.sendall(pickle.dumps(state))
        else:
            self.started = True

        # main loop of Go
        while not self.started:
            self.conn.sendall(str.encode("GET"))
            response = pickle.loads(self.conn.recv(4096))

            if response:
                self.started = True

            for event in pygame.event.get():
                # enable closing of display
                if event.type == pygame.QUIT:
                    self.started = True
                    self.running = False
                    break

            self.wait_gui()

            self.clock.tick(60)
            pygame.display.update()

        start_time = pygame.time.get_ticks()
        pygame.mouse.set_visible(False)
        # add loop for main game
        while self.running:
            self.time_elapsed = int((pygame.time.get_ticks() - start_time) / 1000)
            self.conn.sendall(str.encode("GET"))
            response = pickle.loads(self.conn.recv(8192))

            if response[0] == self.my_color:
                self.my_turn = True
                (
                    _,
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
                    break
                # getting position of mouse
                if event.type == pygame.MOUSEBUTTONDOWN and self.my_turn:
                    mouse_pos = pygame.mouse.get_pos()
                    self.fill_stone(mouse_pos)

            self.update_gui()

            self.clock.tick(60)
            pygame.display.update()
