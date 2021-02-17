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
Misha Schwartz, and Jaisie Sin.

=== Module Description ===

This file contains the hierarchy of player classes.
"""
from __future__ import annotations
from typing import List, Optional, Tuple
import random
import pygame

from block import Block
from goal import Goal, generate_goals

from actions import KEY_ACTION, ROTATE_CLOCKWISE, ROTATE_COUNTER_CLOCKWISE, \
    SWAP_HORIZONTAL, SWAP_VERTICAL, SMASH, PASS, PAINT, COMBINE


def create_players(num_human: int, num_random: int, smart_players: List[int]) \
        -> List[Player]:
    """Return a new list of Player objects.

    <num_human> is the number of human player, <num_random> is the number of
    random players, and <smart_players> is a list of difficulty levels for each
    SmartPlayer that is to be created.

    The list should contain <num_human> HumanPlayer objects first, then
    <num_random> RandomPlayer objects, then the same number of SmartPlayer
    objects as the length of <smart_players>. The difficulty levels in
    <smart_players> should be applied to each SmartPlayer object, in order.
    """
    # Reviewed 17/03/2020, though there may be a way to optimize this more...
    players = []
    goals = generate_goals(num_human + num_random + len(smart_players))
    id_ = 0
    player_to_count = {HumanPlayer: num_human, RandomPlayer: num_random}
    for player in list(player_to_count):
        while player_to_count[player] > 0:
            goal = goals.pop(random.randrange(len(goals)))
            players.append(player(id_, goal))
            id_ += 1
            player_to_count[player] -= 1
    for difficulty in smart_players:
        goal = goals.pop(random.randrange(len(goals)))
        players.append(SmartPlayer(id_, goal, difficulty))
        id_ += 1
    return players


def _get_block(block: Block, location: Tuple[int, int], level: int) -> \
        Optional[Block]:
    """Return the Block within <block> that is at <level> and includes
    <location>. <location> is a coordinate-pair (x, y).

    A block includes all locations that are strictly inside of it, as well as
    locations on the top and left edges. A block does not include locations that
    are on the bottom or right edge.

    If a Block includes <location>, then so do its ancestors. <level> specifies
    which of these blocks to return. If <level> is greater than the level of
    the deepest block that includes <location>, then return that deepest block.

    If no Block can be found at <location>, return None.

    Preconditions:
        - 0 <= level <= max_depth
    """
    # Reviewed 17/03/2020
    for i in [0, 1]:  # For each axis x, y
        if not 0 <= location[i] - block.position[i] < block.size:
            return None
    if block.level != level and block.colour is None:
        for child in block.children:
            test_child = _get_block(child, location, level)
            if test_child is not None:
                block = test_child
    return block


class Player:
    """A player in the Blocky game.

    This is an abstract class. Only child classes should be instantiated.

    === Public Attributes ===
    id:
        This player's number.
    goal:
        This player's assigned goal for the game.
    """
    id: int
    goal: Goal

    def __init__(self, player_id: int, goal: Goal) -> None:
        """Initialize this Player.
        """
        self.goal = goal
        self.id = player_id

    def get_selected_block(self, board: Block) -> Optional[Block]:
        """Return the block that is currently selected by the player.

        If no block is selected by the player, return None.
        """
        raise NotImplementedError

    def process_event(self, event: pygame.event.Event) -> None:
        """Update this player based on the pygame event.
        """
        raise NotImplementedError

    def generate_move(self, board: Block) -> \
            Optional[Tuple[str, Optional[int], Block]]:
        """Return a potential move to make on the game board.

        The move is a tuple consisting of a string, an optional integer, and
        a block. The string indicates the move being made (i.e., rotate, swap,
        or smash). The integer indicates the direction (i.e., for rotate and
        swap). And the block indicates which block is being acted on.

        Return None if no move can be made, yet.
        """
        raise NotImplementedError

    def _helper_generate_move_check(self, action: Tuple[str, Optional[int]],
                                    block: Block) -> bool:
        # Reviewed 17/03/2020
        """Return whether or not an action can be successfully performed on
        the given block.

        This mutates the block, and should be used on a shallow copy of block.
        """
        # Reviewed 17/03/2020
        success = False
        if action == ROTATE_CLOCKWISE:
            success = block.rotate(1)
        elif action == ROTATE_COUNTER_CLOCKWISE:
            success = block.rotate(3)
        elif action == SWAP_HORIZONTAL:
            success = block.swap(0)
        elif action == SWAP_VERTICAL:
            success = block.swap(1)
        elif action == PAINT:
            success = block.paint(self.goal.colour)
        elif action == COMBINE:
            success = block.combine()
        elif action == SMASH:
            success = block.smash()
        elif action == PASS:
            success = True
        return success


def _create_move(action: Tuple[str, Optional[int]], block: Block) -> \
        Tuple[str, Optional[int], Block]:
    return action[0], action[1], block


def _helper_generate_move_level(board: Block,
                                copy: Block) -> Tuple[Block, Block]:
    """Iterates to a random valid level of both block and copy to the
    same level.

    This does not mutate any values of block or copy.
    """
    # Reviewed 17/03/2020. Strange bug where return at comment causes crash
    level = random.randint(0, board.max_depth)
    while level > board.level:
        if board.colour is None:
            i = random.randint(0, 3)
            board = board.children[i]
            copy = copy.children[i]
        else:
            break  # return board, copy here causes game to crash
    return board, copy


def _helper_generate_move_choose() -> tuple:
    """Return a random possible action."""
    # Reviewed 17/03/2020
    actions_and_penalties = [(ROTATE_CLOCKWISE, 0),
                             (ROTATE_COUNTER_CLOCKWISE, 0),
                             (SWAP_HORIZONTAL, 0), (SWAP_VERTICAL, 0),
                             (SMASH, 3), (PAINT, 1),
                             (COMBINE, 1), (PASS, 0)]
    return random.choice(actions_and_penalties)


class HumanPlayer(Player):
    """A human player.
    """
    # === Private Attributes ===
    # _level:
    #     The level of the Block that the user selected most recently.
    # _desired_action:
    #     The most recent action that the user is attempting to do.
    #
    # == Representation Invariants concerning the private attributes ==
    #     _level >= 0
    _level: int
    _desired_action: Optional[Tuple[str, Optional[int]]]

    def __init__(self, player_id: int, goal: Goal) -> None:
        """Initialize this HumanPlayer with the given <renderer>, <player_id>
        and <goal>.
        """
        Player.__init__(self, player_id, goal)

        # This HumanPlayer has not yet selected a block, so set _level to 0
        # and _selected_block to None.
        self._level = 0
        self._desired_action = None

    def get_selected_block(self, board: Block) -> Optional[Block]:
        """Return the block that is currently selected by the player based on
        the position of the mouse on the screen and the player's desired level.

        If no block is selected by the player, return None.
        """
        mouse_pos = pygame.mouse.get_pos()
        block = _get_block(board, mouse_pos, self._level)

        return block

    def process_event(self, event: pygame.event.Event) -> None:
        """Respond to the relevant keyboard events made by the player based on
        the mapping in KEY_ACTION, as well as the W and S keys for changing
        the level.
        """
        if event.type == pygame.KEYDOWN:
            if event.key in KEY_ACTION:
                self._desired_action = KEY_ACTION[event.key]
            elif event.key == pygame.K_w:
                self._level = max(0, self._level - 1)
                self._desired_action = None
            elif event.key == pygame.K_s:
                self._level += 1
                self._desired_action = None

    def generate_move(self, board: Block) -> \
            Optional[Tuple[str, Optional[int], Block]]:
        """Return the move that the player would like to perform. The move may
        not be valid.

        Return None if the player is not currently selecting a block.
        """
        block = self.get_selected_block(board)

        if block is None or self._desired_action is None:
            return None
        else:
            move = _create_move(self._desired_action, block)

            self._desired_action = None
            return move


class RandomPlayer(Player):
    """A player in the game of blocky that makes random moves each turn"""
    # === Private Attributes ===
    # _proceed:
    #   True when the player should make a move, False when the player should
    #   wait.
    _proceed: bool

    def __init__(self, player_id: int, goal: Goal) -> None:
        # Reviewed 17/03/2020
        Player.__init__(self, player_id, goal)
        self._proceed = False

    def get_selected_block(self, board: Block) -> Optional[Block]:
        return None

    def process_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._proceed = True

    def generate_move(self, board: Block) ->\
            Optional[Tuple[str, Optional[int], Block]]:
        """Return a valid, randomly generated move.

        A valid move is a move other than PASS that can be successfully
        performed on the <board>.

        This function does not mutate <board>.
        """
        # Reviewed 17/03/2020
        action = PASS  # Default, but are always overridden
        board_child = board
        if not self._proceed:
            return None  # Do not remove
        success = False  # Initialize success value as False
        while not success:  # While a valid move has not been generated
            copy = board.create_copy()
            board_and_copy = _helper_generate_move_level(board, copy)
            board_child = board_and_copy[0]
            copy_child = board_and_copy[1]
            action = _helper_generate_move_choose()[0]
            success = self._helper_generate_move_check(action, copy_child)
        self._proceed = False  # Must set to False before returning!
        return _create_move(action, board_child)  # Create the move


class SmartPlayer(Player):
    """A player in the game of blocky that considers a given amount of possible
    moves and choosing the best move.
    """
    # === Private Attributes ===
    # _proceed:
    #   True when the player should make a move, False when the player should
    #   wait.
    # _difficulty:
    #   The number of possible moves considered
    _difficulty: int
    _proceed: bool

    def __init__(self, player_id: int, goal: Goal, difficulty: int) -> None:
        # 16/03/2020
        Player.__init__(self, player_id, goal)
        self._difficulty = difficulty
        self._proceed = False

    def get_selected_block(self, board: Block) -> Optional[Block]:
        return None

    def process_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._proceed = True

    def generate_move(self, board: Block) ->\
            Optional[Tuple[str, Optional[int], Block]]:
        """Return a valid move by assessing multiple valid moves and choosing
        the move that results in the highest score for this player's goal (i.e.,
        disregarding penalties).

        A valid move is a move other than PASS that can be successfully
        performed on the <board>. If no move can be found that is better than
        the current score, this player will pass.

        This function does not mutate <board>.
        """
        # Reviewed 17/03/2020, though the code is still quite long. Nested (4/3)
        n = self._difficulty
        max_action = PASS
        max_board_child = board
        max_ = self.goal.score(board)  # These variables store the best move
        if not self._proceed:
            return None  # Do not remove
        while n > 0:  # Come up with n possible moves
            success = False
            while not success:
                copy = board.create_copy()
                # Iterate both board and copy to the desired child level
                board_and_copy = _helper_generate_move_level(board, copy)
                board_child = board_and_copy[0]
                copy_child = board_and_copy[1]
                # Choose an action at random and store its penalty
                action_and_penalty = _helper_generate_move_choose()
                action = action_and_penalty[0]
                penalty = action_and_penalty[1]
                # Check if the move is valid
                success = self._helper_generate_move_check(action, copy_child)
                if success:  # Compare and store if this is the best move so far
                    current = self.goal.score(copy) - penalty
                    # Round-about fix due to nested warning (4/3)
                    max_action = action if current > max_ else max_action
                    max_board_child = board_child if current > max_ \
                        else max_board_child
                    max_ = current if current > max_ else max_
                    n -= 1
        self._proceed = False
        return _create_move(max_action, max_board_child)


if __name__ == '__main__':
    import python_ta

    python_ta.check_all(config={
        'allowed-io': ['process_event'],
        'allowed-import-modules': [
            'doctest', 'python_ta', 'random', 'typing', 'actions', 'block',
            'goal', 'pygame', '__future__'
        ],
        'max-attributes': 10,
        'generated-members': 'pygame.*'
    })
