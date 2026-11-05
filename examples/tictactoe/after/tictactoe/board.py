"""Board representation and rules for tic-tac-toe."""

EMPTY = " "
WINNING_LINES = [
    # rows
    (0, 1, 2),
    (3, 4, 5),
    (6, 7, 8),
    # columns
    (0, 3, 6),
    (1, 4, 7),
    (2, 5, 8),
    # diagonals
    (0, 4, 8),
    (2, 4, 6),
]


class InvalidMove(Exception):
    """Raised when a player tries to play an illegal move."""


def new_board() -> list[str]:
    """Return an empty 3x3 board as a flat list of 9 cells."""
    return [EMPTY] * 9


def place(board: list[str], cell: int, player: str) -> list[str]:
    """Return a new board with `player` placed in `cell` (0-8)."""
    if not 0 <= cell < 9:
        raise InvalidMove(f"cell {cell + 1} is off the board")

    if board[cell] != EMPTY:
        raise InvalidMove(f"cell {cell + 1} is already taken")

    new = board.copy()
    new[cell] = player
    return new


def winner(board: list[str]) -> str | None:
    """Return the winning player's mark, or None if nobody has won."""
    for a, b, c in WINNING_LINES:
        if board[a] != EMPTY and board[a] == board[b] == board[c]:
            return board[a]

    return None


def is_full(board: list[str]) -> bool:
    return EMPTY not in board


def open_cells(board: list[str]) -> list[int]:
    return [i for i, mark in enumerate(board) if mark == EMPTY]


def render(board: list[str]) -> str:
    rows = []

    for start in range(0, 9, 3):
        rows.append(" " + " | ".join(board[start : start + 3]))

    return "\n---+---+---\n".join(rows)
