"""A perfect tic-tac-toe player using negamax search."""

from functools import lru_cache

from tictactoe.board import is_full, open_cells, place, winner


def best_move(board: list[str], player: str, opponent: str) -> int:
    """Return the cell that gives `player` the best guaranteed outcome."""
    best_score, best_cell = -2, -1
    for cell in open_cells(board):
        score = -_negamax(tuple(place(board, cell, player)), opponent, player)
        if score > best_score:
            best_score, best_cell = score, cell
    return best_cell


@lru_cache(maxsize=None)
def _negamax(board: tuple[str, ...], player: str, opponent: str) -> int:
    """Score the position for `player`, who is about to move: 1 win, 0 draw, -1 loss."""
    if winner(list(board)) == opponent:
        return -1
    if is_full(list(board)):
        return 0
    return max(
        -_negamax(tuple(place(list(board), cell, player)), opponent, player)
        for cell in open_cells(list(board))
    )
