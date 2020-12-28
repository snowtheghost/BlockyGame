"""CSC148 Assignment 2

=== CSC148 Winter 2020 ===
Department of Computer Science,
University of Toronto

This code is provided solely for the personal and private use of
students taking the CSC148 course at the University of Toronto.
Copying for purposes other than this use is expressly prohibited.
All forms of distribution of this code, whether as given or with
any changes, are expressly prohibited.

Authors: Diane Horton, David Liu, Mario Badr, Sophia Huynh, Misha Schwartz,
and Jaisie Sin

All of the files in this directory and all subdirectories are:
Copyright (c) Diane Horton, David Liu, Mario Badr, Sophia Huynh,
Misha Schwartz, and Jaisie Sin

=== Module Description ===

This file contains the hierarchy of Goal classes.
"""
from __future__ import annotations
import math
import random
from typing import List, Tuple
from block import Block
from settings import colour_name, COLOUR_LIST


def generate_goals(num_goals: int) -> List[Goal]:
    """Return a randomly generated list of goals with length num_goals.

    All elements of the list must be the same type of goal, but each goal
    must have a different randomly generated colour from COLOUR_LIST. No two
    goals can have the same colour.

    Precondition:
        - num_goals <= len(COLOUR_LIST)
    """
    # Reviewed 17/03/2020
    out_list = []
    cl_copy = COLOUR_LIST[:]
    goal = random.choice([BlobGoal, PerimeterGoal])
    while num_goals > 0:
        out_list.append(goal(cl_copy.pop(random.randrange(len(cl_copy)))))
        num_goals -= 1
    return out_list


def _flatten(block: Block) -> List[List[Tuple[int, int, int]]]:
    """Return a two-dimensional list representing <block> as rows and columns of
    unit cells.

    Return a list of lists L, where,
    for 0 <= i, j < 2^{max_depth - self.level}
        - L[i] represents column i and
        - L[i][j] represents the unit cell at column i and row j.

    Each unit cell is represented by a tuple of 3 ints, which is the colour
    of the block at the cell location[i][j]

    L[0][0] represents the unit cell in the upper left corner of the Block.
    """
    # Reviewed 17/03/2020, although still kinda spaghetti code
    out_list = []
    if block.colour is not None:
        length = int(math.pow(2, (block.max_depth - block.level)))
        for i in range(length):
            out_list.append([])
            for _ in range(length):
                out_list[i].append(block.colour)
    else:
        length = int(math.pow(2, (block.max_depth - block.level - 1)))
        lh = []
        rh = []
        for i in range(length):
            lh.append(_flatten(block.children[1])[i] +
                      _flatten(block.children[2])[i])
            rh.append(_flatten(block.children[0])[i] +
                      _flatten(block.children[3])[i])
        out_list.extend(lh + rh)
    return out_list


class Goal:
    """A player goal in the game of Blocky.

    This is an abstract class. Only child classes should be instantiated.

    === Attributes ===
    colour:
        The target colour for this goal, that is the colour to which
        this goal applies.
    """
    colour: Tuple[int, int, int]

    def __init__(self, target_colour: Tuple[int, int, int]) -> None:
        """Initialize this goal to have the given target colour.
        """
        self.colour = target_colour

    def score(self, board: Block) -> int:
        """Return the current score for this goal on the given board.

        The score is always greater than or equal to 0.
        """
        raise NotImplementedError

    def description(self) -> str:
        """Return a description of this goal.
        """
        raise NotImplementedError


def _helper_score(flat: List[List]) -> List[List]:
    """Return a 'visited' board in the format of a flattened board."""
    # 01/04/2020
    visited = []
    for i in range(len(flat)):  # Make a visited board like _flatten()
        visited.append([])
        for _ in range(len(flat)):
            visited[i].append(-1)
    return visited


class PerimeterGoal(Goal):
    """A player goal in the game of blocky, that calculates the score by the
    number of goal coloured blocks on the perimeter of the board.
    """
    # Reviewed 17/03/2020
    def score(self, board: Block) -> int:
        flat = _flatten(board)
        score = 0
        for i in range(len(flat)):
            for j in [0, len(flat) - 1]:
                if flat[i][j] == self.colour:
                    score += 1
                if flat[j][i] == self.colour:
                    score += 1
        return score

    def description(self) -> str:
        # Reviewed 17/03/2020
        colour = colour_name(self.colour)
        return 'Place as many {0} units on the perimeter!'.format(colour)


class BlobGoal(Goal):
    """A player goal in the game of blocky, that calculates the score by the
    number of goal coloured blocks connected together vertically/horizontally.
    """
    def score(self, board: Block) -> int:
        # Reviewed 17/03/2020
        largest = 0  # There may be 0 blocks of this colour
        flat = _flatten(board)
        visited = _helper_score(flat)
        for i in range(len(flat)):
            for j in range(len(flat)):
                current = self._undiscovered_blob_size((i, j), flat, visited)
                if current > largest:
                    largest = current
        return largest

    def _undiscovered_blob_size(self, pos: Tuple[int, int],
                                board: List[List[Tuple[int, int, int]]],
                                visited: List[List[int]]) -> int:
        """Return the size of the largest connected blob that (a) is of this
        Goal's target colour, (b) includes the cell at <pos>, and (c) involves
        only cells that have never been visited.

        If <pos> is out of bounds for <board>, return 0.

        <board> is the flattened board on which to search for the blob.
        <visited> is a parallel structure that, in each cell, contains:
            -1 if this cell has never been visited
            0  if this cell has been visited and discovered
               not to be of the target colour
            1  if this cell has been visited and discovered
               to be of the target colour

        Update <visited> so that all cells that are visited are marked with
        either 0 or 1.
        """
        # Reviewed 17/03/2020
        i = pos[0]
        j = pos[1]
        size = 0
        if i < len(board) and j < len(board) and visited[i][j] == -1:
            if board[i][j] == self.colour:
                visited[i][j] = 1
                size += 1
                for k in [-1, 1]:
                    size += self._undiscovered_blob_size(
                        (abs(i + k), j), board, visited) +\
                        self._undiscovered_blob_size(
                            (i, abs(j + k)), board, visited)
            else:
                visited[i][j] = 0
        return size

    def description(self) -> str:
        # Reviewed 17/03/2020
        colour = colour_name(self.colour)
        return 'Connect as many {0} units together!'.format(colour)


if __name__ == '__main__':
    import python_ta
    python_ta.check_all(config={
        'allowed-import-modules': [
            'doctest', 'python_ta', 'random', 'typing', 'block', 'settings',
            'math', '__future__'
        ],
        'max-attributes': 15
    })
