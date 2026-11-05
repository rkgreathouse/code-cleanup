# code-cleanup

- Write all Python here to the `python-style` skill. It lives in the
  `rkgreathouse/setup` repo at `claude/dot-claude/skills/python-style/`; read its
  `SKILL.md` and `example/` before changing code.
- The plan and design decisions live in `rkgreathouse/setup` at
  `docs/code-cleanup/MEMORY.md`. Update it when a decision changes.
- The tool checks itself: `uv run code-cleanup .` must leave no diff and no errors,
  alongside `uv run mypy .` and `uv run pytest`.
- A new language is a subpackage (`code_cleanup/<language>/`) exposing a
  `clean_<language>(text, path, settings) -> Cleaned` function, registered in
  `router.py`, with its settings section in `style.yaml` and `settings.py`. Model it
  on `code_cleanup/python/`.
