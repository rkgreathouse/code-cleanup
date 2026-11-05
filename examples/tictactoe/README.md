# Example: tic-tac-toe, before and after

A small game: you play X from the command line against a computer that searches
every move (negamax) and never loses.

```sh
cd examples/tictactoe/after
python -m tictactoe 1,2,7,6,9
```

```
 X | X | O
---+---+---
 O | O | X
---+---+---
 X | O | X
draw
```

- `before/` is the code as first written: ordinary Python, not made messy on purpose.
- `after/` is `before/` after one run of `code-cleanup`, unedited.

`code_cleanup/tests/test_main.py` cleans a copy of `before/` and checks that it
matches `after/` byte for byte, so this example always shows what the tool really
does. Both versions play identical games.

## The run

![code-cleanup report](screenshots/report.png)

The tool fixed what is safe to fix and listed the rest for a person to decide:

| Code | What it wants | Why it was not fixed automatically |
|---|---|---|
| `CC101` | `from .board import ...` inside the package | not yet auto-fixed; planned |
| `B904` | `raise ... from error` inside `except` | changes the traceback, so a person chooses |
| `ANN001` | a type for `argv` | the tool cannot know the intended type |
| `N818` | `InvalidMove` renamed `InvalidMoveError` | a rename touches every caller |

## What changed

### `board.py`

- `Optional[str]` became `str | None`, and the unused `typing` import went.
- Blank lines around every block, slice spacing from `ruff format`.
- `WINNING_LINES` was split one tuple per line, because the list ends with a trailing
  comma. The `# rows` / `# columns` comments now sit on the last tuple of each group,
  which reads worse than before. This is `ruff format`'s behaviour.

![board.py before and after](screenshots/board.png)

### `ai.py`

- `@lru_cache(maxsize=None)` became `@cache`.
- Blank lines around blocks, including one after the docstring before an `if`.

![ai.py before and after](screenshots/ai.png)

### `__main__.py`

- `if` / `elif` / `else` chains that all `return` became flat `if` guards.
- Blank lines around blocks and between `try` and `except`.

![__main__.py before and after](screenshots/main.png)
