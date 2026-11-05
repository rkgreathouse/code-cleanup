"""Command-line entry point: play X against the computer."""

import argparse
import sys

from tictactoe.ai import best_move
from tictactoe.board import InvalidMove, is_full, new_board, place, render, winner


def parse_moves(text: str) -> list[int]:
    try:
        return [int(part) - 1 for part in text.split(",")]

    except ValueError:
        raise argparse.ArgumentTypeError("moves must be numbers from 1 to 9")


def play(moves: list[int]) -> list[str]:
    board = new_board()

    for move in moves:
        board = place(board, move, "X")

        if winner(board) or is_full(board):
            break

        board = place(board, best_move(board, "O", "X"), "O")

        if winner(board):
            break

    return board


def describe(board: list[str]) -> str:
    result = winner(board)

    if result == "X":
        return "you win"

    if result == "O":
        return "the computer wins"

    if is_full(board):
        return "draw"

    return "unfinished: give more moves"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="tictactoe",
        description="Play X against a computer that never loses.",
    )
    parser.add_argument(
        "moves",
        type=parse_moves,
        help="your moves as cells 1-9 (left to right, top to bottom), e.g. 5,9,7",
    )
    args = parser.parse_args(argv)

    try:
        board = play(args.moves)

    except InvalidMove as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    print(render(board))
    print(describe(board))
    return 0


if __name__ == "__main__":
    sys.exit(main())
