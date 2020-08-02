"""This module contains the GoGui class.
GoGui objects contain a representation of the
Chinese strategy board game Go.
"""
import os
import string
from collections import deque, namedtuple

import numpy as np
import pygame
from pygame import gfxdraw

BOARD_WIDTH = 612
WIDTH = 740
HEIGHT = int(WIDTH * 1.2)

Color = namedtuple("Color", ["r", "g", "b"])
WHITE = Color(255, 255, 255)
YELLOW = Color(220, 179, 92)
BLACK = Color(0, 0, 0)
GREY = Color(150, 150, 150)
BLUE = Color(160, 180, 220)

#### TODO implement algorithm to check for which player an intersection belongs to


class GoGui:
    """Class representing the GUI of a Go board
    """

    def __init__(self, size):
        self.size = size
        self.board_width = BOARD_WIDTH
        self.width = WIDTH
        self.height = HEIGHT
        self.spacing = self.board_width // (size - 1)
        self.bot_pad = (self.width - self.board_width) // 2
        self.top_pad = self.height - self.board_width - self.bot_pad * 2
        self.hor_pad = self.bot_pad
        self.buffer = self.spacing // 2
        self.stone_width = self.spacing // 2 - 1
        self.black_stone_img = None
        self.white_stone_img = None

        self.but0_x = 15
        self.but0_y = 15
        self.but_width = 70
        self.but_height = 35

        self.board = np.zeros((self.size, self.size), dtype=int)
        # keeps track of the parent of each group
        self.pointer = np.zeros((self.size, self.size), dtype=tuple)
        self.white_group = {}
        self.black_group = {}
        self.newest_stone = None
        self.states = deque()

        self.running = False
        self.display = None
        self.clock = None
        self.time_elapsed = 0

        self.player = 0
        # True for black, False for white
        self.color = True
        self.white_captured = 0
        self.black_captured = 0

    def check_liberty(self, row, col):
        """Checks the liberty of a stone

        Args:
            row (int): row of the stone
            col (int): column of the stone

        Returns:
            bool: True if stone has liberty, False otherwise
        """
        # checking row above
        if row != 0 and self.board[row - 1, col] == 0:
            return True
        # checking row below
        if row != self.size - 1 and self.board[row + 1, col] == 0:
            return True
        # checking col to the left
        if col != 0 and self.board[row, col - 1] == 0:
            return True
        # checking col to the right
        if col != self.size - 1 and self.board[row, col + 1] == 0:
            return True

        return False

    def check_board(self):
        """Checks the entire board for any stones that should be removed
        because they lack liberty
        """
        # checking white stones
        white_to_del = []
        check_again = None
        for key, group in self.white_group.items():
            for pos in group:
                if pos == self.newest_stone:
                    # do not check newest placed stone yet
                    check_again = key
                    break
                if self.check_liberty(pos // self.size, pos % self.size):
                    break
            else:
                # if no stones in a group has liberty, remove entire group
                white_to_del.append(key)
                for pos in group:
                    self.white_captured += 1
                    row = pos // self.size
                    col = pos % self.size
                    self.board[row, col] = 0
                    self.pointer[row, col] = 0

        # remove group representation
        for to_del in white_to_del:
            del self.white_group[to_del]

        # checking black stones
        black_to_del = []
        for key, group in self.black_group.items():
            for pos in group:
                if pos == self.newest_stone:
                    # do not check newest placed stone yet
                    check_again = key
                    break
                if self.check_liberty(pos // self.size, pos % self.size):
                    break
            else:
                # if no stones in a group has liberty, remove entire group
                black_to_del.append(key)
                for pos in group:
                    self.black_captured += 1
                    row = pos // self.size
                    col = pos % self.size
                    self.board[row, col] = 0
                    self.pointer[row, col] = 0

        # remove group representation
        for to_del in black_to_del:
            del self.black_group[to_del]

        if check_again is not None:
            # checking newest placed stone and removing it if necessary
            if self.color:
                for pos in self.black_group[check_again]:
                    if self.check_liberty(pos // self.size, pos % self.size):
                        break
                else:
                    for pos in self.black_group[check_again]:
                        self.black_captured += 1
                        row = pos // self.size
                        col = pos % self.size
                        self.board[row, col] = 0
                        self.pointer[row, col] = 0
                    del self.black_group[check_again]
            else:
                for pos in self.white_group[check_again]:
                    if self.check_liberty(pos // self.size, pos % self.size):
                        break
                else:
                    for pos in self.white_group[check_again]:
                        self.white_captured += 1
                        row = pos // self.size
                        col = pos % self.size
                        self.board[row, col] = 0
                        self.pointer[row, col] = 0
                    del self.white_group[check_again]

    def add_group(self, row, col, color_num):
        """Updating stones to form correct groups

        Args:
            row (int): row of the stone
            col (int): column of the stone
            color_num (int): 1 for black, -1 for white
        """
        group = self.black_group if color_num == 1 else self.white_group
        setted = False

        # checking whether stone above is of same color
        if row != 0 and self.board[row - 1, col] == color_num:
            parent = self.pointer[row - 1, col]
            self.pointer[row, col] = parent
            # adding stone to group of above stone
            group[parent] = group[parent].union({row * self.size + col})
            setted = True

        # checking whether stone below is of same color
        if row != self.size - 1 and self.board[row + 1, col] == color_num:
            if setted:
                # adding group of below stone to group newest stone belongs to
                prev_parent = self.pointer[row + 1, col]
                if prev_parent != parent:
                    for pos in group[prev_parent]:
                        self.pointer[pos // self.size, pos % self.size] = parent
                    group[parent] = group[parent].union(group[prev_parent])
                    del group[prev_parent]
            else:
                parent = self.pointer[row + 1, col]
                self.pointer[row, col] = parent
                # adding stone to group of below stone
                group[parent] = group[parent].union({row * self.size + col})
                setted = True

        # checking whether left stone is of same color
        if col != 0 and self.board[row, col - 1] == color_num:
            if setted:
                # adding left group to group newest stone belongs to
                prev_parent = self.pointer[row, col - 1]
                if prev_parent != parent:
                    for pos in group[prev_parent]:
                        self.pointer[pos // self.size, pos % self.size] = parent
                    group[parent] = group[parent].union(group[prev_parent])
                    del group[prev_parent]
            else:
                parent = self.pointer[row, col - 1]
                self.pointer[row, col] = parent
                # adding stone to left group
                group[parent] = group[parent].union({row * self.size + col})
                setted = True

        # checking whether right stone is of same color
        if col != self.size - 1 and self.board[row, col + 1] == color_num:
            if setted:
                # adding right group to group newest stone belongs to
                prev_parent = self.pointer[row, col + 1]
                if prev_parent != parent:
                    for pos in group[prev_parent]:
                        self.pointer[pos // self.size, pos % self.size] = parent
                    group[parent] = group[parent].union(group[prev_parent])
                    del group[prev_parent]
            else:
                parent = self.pointer[row, col + 1]
                self.pointer[row, col] = parent
                # adding stone to right group
                group[parent] = group[parent].union({row * self.size + col})
                setted = True

        # create new group of stone if there are no adjacent same color stones
        if not setted:
            parent = row * self.size + col
            self.pointer[row, col] = parent
            group[parent] = {parent}

    def check_ko(self):
        """Checking whether newest move violates Ko rule

        Returns:
            bool: True if violated, False otherwise
        """
        _ = self.states.pop()
        board_2, pointer_2, white_2, black_2, w_cap_2, b_cap_2 = self.states.pop()

        self.states.append((board_2, pointer_2, white_2, black_2, w_cap_2, b_cap_2))
        self.states.append(_)

        return (board_2 == self.board).all()

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
                    # did not violate Ko, move on
                    self.color = not self.color
        if (
            pos[0] > self.but0_x
            and pos[0] < self.but0_x + self.but_width
            and pos[1] > self.but0_y
            and pos[1] < self.but0_y + self.but_height
        ):
            self.color = not self.color

    def update_stones(self):
        """Update the stones on GUI
        """
        top_bot_padding = self.top_pad + self.bot_pad

        for row in range(self.size):
            for col in range(self.size):
                if self.board[row, col] == 1:
                    gfxdraw.aacircle(
                        self.display,
                        self.hor_pad + col * self.spacing,
                        top_bot_padding + row * self.spacing,
                        self.stone_width,
                        BLACK,
                    )
                    gfxdraw.filled_circle(
                        self.display,
                        self.hor_pad + col * self.spacing,
                        top_bot_padding + row * self.spacing,
                        self.stone_width,
                        BLACK,
                    )
                elif self.board[row, col] == -1:
                    gfxdraw.aacircle(
                        self.display,
                        self.hor_pad + col * self.spacing,
                        top_bot_padding + row * self.spacing,
                        self.stone_width,
                        WHITE,
                    )
                    gfxdraw.filled_circle(
                        self.display,
                        self.hor_pad + col * self.spacing,
                        top_bot_padding + row * self.spacing,
                        self.stone_width,
                        WHITE,
                    )

    def draw_lines(self):
        """Drawing the grid lines on GUI
        """
        thin_line = 1
        top_bot_padding = self.top_pad + self.bot_pad
        end_x = self.width - self.hor_pad
        end_y = self.height - self.bot_pad

        for i in range(self.size):
            # horizontal lines
            pygame.draw.line(
                self.display,
                BLACK,
                (self.hor_pad, i * self.spacing + top_bot_padding),
                (end_x, i * self.spacing + top_bot_padding),
                thin_line,
            )
            # vertical lines
            pygame.draw.line(
                self.display,
                BLACK,
                (self.hor_pad + i * self.spacing, top_bot_padding),
                (self.hor_pad + i * self.spacing, end_y),
                thin_line,
            )

    def draw_dots(self):
        """Drawing the small dots on GUI
        """
        top_bot_padding = self.top_pad + self.bot_pad

        for i in range(3, self.size, 6):
            for j in range(3, self.size, 6):
                gfxdraw.aacircle(
                    self.display,
                    self.hor_pad + j * self.spacing,
                    top_bot_padding + i * self.spacing,
                    3,
                    BLACK,
                )
                gfxdraw.filled_circle(
                    self.display,
                    self.hor_pad + j * self.spacing,
                    top_bot_padding + i * self.spacing,
                    3,
                    BLACK,
                )
        if self.size == 13:
            gfxdraw.aacircle(
                self.display,
                self.hor_pad + 6 * self.spacing,
                top_bot_padding + 6 * self.spacing,
                3,
                BLACK,
            )
            gfxdraw.filled_circle(
                self.display,
                self.hor_pad + 6 * self.spacing,
                top_bot_padding + 6 * self.spacing,
                3,
                BLACK,
            )

    def draw_nums(self):
        """Drawing the numbers on the side of the board
        """
        font = pygame.font.SysFont("calibri", 20)
        upper_case = string.ascii_uppercase

        for i in range(self.size):
            num = font.render(str(i + 1), True, BLACK)
            letter = font.render(upper_case[i], True, BLACK)
            increment = i * self.spacing
            letter_x = self.hor_pad + increment - letter.get_width() // 2
            height = self.height - self.bot_pad - num.get_height() // 2 - increment

            # drawing nums on left side
            self.display.blit(
                num, (self.hor_pad - self.buffer - num.get_width(), height),
            )
            # drawing nums on right side
            self.display.blit(
                num, (self.width - self.hor_pad + self.buffer, height),
            )
            # drawing letters on top
            self.display.blit(
                letter,
                (
                    letter_x,
                    self.top_pad + self.bot_pad - self.buffer - letter.get_height(),
                ),
            )
            # drawing letters on bottom
            self.display.blit(
                letter, (letter_x, self.height - self.bot_pad + self.buffer,),
            )

    def draw_captured(self, font):
        """Drawing the captured stone counts

        Args:
            font (pygame font): font to use to draw
        """
        hori_padding = self.board_width + self.spacing
        stone_width = 16

        # how many black stones have been captured
        text = font.render(str(self.black_captured), True, BLACK)
        gfxdraw.aacircle(
            self.display,
            hori_padding,
            self.top_pad - stone_width * 3 - 10,
            stone_width,
            BLACK,
        )
        gfxdraw.filled_circle(
            self.display,
            hori_padding,
            self.top_pad - stone_width * 3 - 10,
            stone_width,
            BLACK,
        )
        self.display.blit(
            text,
            (
                hori_padding + stone_width * 2,
                self.top_pad - stone_width * 3 - text.get_height() // 2 - 10,
            ),
        )
        # how many white stones have been captured
        text = font.render(str(self.white_captured), True, BLACK)
        gfxdraw.aacircle(
            self.display,
            hori_padding,
            self.top_pad - stone_width - 5,
            stone_width,
            WHITE,
        )
        gfxdraw.filled_circle(
            self.display,
            hori_padding,
            self.top_pad - stone_width - 5,
            stone_width,
            WHITE,
        )
        self.display.blit(
            text,
            (
                hori_padding + stone_width * 2,
                self.top_pad - stone_width - text.get_height() // 2 - 5,
            ),
        )

    def draw_turn(self, font):
        """Drawing which player's turn it is

        Args:
            font (pygame font): font to use to draw
        """
        color = "BLACK TURN" if self.color else "WHITE TURN"
        text = font.render(color, True, BLACK)
        self.display.blit(text, (self.width // 2 - text.get_width() // 2, 15))

    def draw_pass(self):
        self.display.fill(
            BLUE, pygame.Rect(self.but0_x, self.but0_y, self.but_width, self.but_height)
        )

        font = pygame.font.SysFont("timesnewroman", 22)
        text = font.render("PASS", True, BLACK)
        self.display.blit(
            text,
            (
                15 + (self.but_width - text.get_width()) // 2,
                15 + (self.but_height - text.get_height()) // 2,
            ),
        )

    def update_gui(self):
        """Update Go board GUI
        """
        self.display.fill(GREY, pygame.Rect(0, 0, self.width, self.top_pad))
        self.display.fill(YELLOW, pygame.Rect(0, self.top_pad, self.width, self.width))

        # drawing grid
        self.draw_lines()

        # drawing dots
        self.draw_dots()

        font = pygame.font.SysFont("timesnewroman", 30)
        # drawing stones
        self.update_stones()

        # drawing nums on the sides of board
        self.draw_nums()

        # indicate the time elapsed since the game has started
        text = font.render(
            f"{(self.time_elapsed // 60):02}:{(self.time_elapsed % 60):02}",
            True,
            BLACK,
        )
        self.display.blit(text, (self.width - text.get_width() - 40, 15))

        # # fps counter
        # fps = str(int(self.clock.get_fps()))
        # fps_text = font.render(fps, True, BLACK)
        # self.display.blit(fps_text, (470, 15))

        # whose turn it is
        self.draw_turn(font)

        # drawing stones captured
        self.draw_captured(font)

        # drawing pass button
        self.draw_pass()

        mouse_x = pygame.mouse.get_pos()[0] - self.stone_width
        mouse_y = pygame.mouse.get_pos()[1] - self.stone_width
        if self.color:
            self.display.blit(self.black_stone_img, (mouse_x, mouse_y))
        else:
            self.display.blit(self.white_stone_img, (mouse_x, mouse_y))

    def scan_peripheral(self, row, col):
        """Scan peripheral of specified stone

        Args:
            row (int): row of the stone
            col (col): column of the stone

        Returns:
            int: 1 for Black, -1 for White, 0 for tie
        """
        black_score = 0
        white_score = 0
        for i in range(-2, 3):
            temp_row = row + i
            if temp_row >= 0 and temp_row < self.size:
                for j in range(-2, 3):
                    temp_col = col + j
                    if temp_col >= 0 and temp_col < self.size:
                        if self.board[temp_row, temp_col] == 1:
                            black_score += 1
                        elif self.board[temp_row, temp_col] == -1:
                            white_score += 1

        if black_score > white_score:
            return 1
        elif white_score > black_score:
            return -1
        else:
            return 0

    def score(self):
        """Score the game
        """
        black_score = self.white_captured
        white_score = self.black_captured
        for row in range(self.size):
            for col in range(self.size):
                if self.scan_peripheral(row, col) == 1:
                    black_score += 1
                elif self.scan_peripheral(row, col) == -1:
                    white_score += 1

        if black_score > white_score:
            print("BLACK WON")
        elif white_score > black_score:
            print("WHITE WON")
        else:
            print("TIE")

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
        pygame.mouse.set_visible(False)
        pygame.display.set_caption("GO")
        start_time = pygame.time.get_ticks()

        # main loop of Go
        while self.running:
            self.time_elapsed = int((pygame.time.get_ticks() - start_time) / 1000)

            for event in pygame.event.get():
                # enable closing of display
                if event.type == pygame.QUIT:
                    self.running = False
                    self.score()
                    return
                # getting position of mouse
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    self.fill_stone(mouse_pos)
                if event.type == pygame.KEYDOWN:
                    keys = pygame.key.get_pressed()
                    if keys[pygame.K_LCTRL] and keys[pygame.K_z]:
                        try:
                            (
                                self.board,
                                self.pointer,
                                self.white_group,
                                self.black_group,
                                self.white_captured,
                                self.black_captured,
                            ) = self.states.pop()
                            self.color = not self.color
                        except IndexError:
                            pass

            self.clock.tick(60)
            self.update_gui()
            pygame.display.update()


if __name__ == "__main__":
    pygame.init()
    go_gui = GoGui(19)
    go_gui.start_game()
    pygame.quit()
