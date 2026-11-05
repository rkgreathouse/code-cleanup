# code-cleanup

- Write all Python here to the `python-style` skill. It lives in the
  `rkgreathouse/setup` repo at `claude/dot-claude/skills/python-style/`; read its
  `SKILL.md` and `example/` before changing code.
- Java code that code-cleanup checks is written to the `java-style` skill, kept in
  this repo for now at `docs/java-style/` (`SKILL.md` and `example/`). Java covers
  Spring REST services only (`profile: service`); there is no Java CLI layout yet.
  `uv run code-cleanup --check docs/java-style/example` must stay clean too.
- The plan and design decisions live in `rkgreathouse/setup` at
  `docs/code-cleanup/MEMORY.md`. Update it when a decision changes.
- The tool checks itself: `uv run code-cleanup .` must leave no diff and no errors,
  alongside `uv run mypy .` and `uv run pytest`.
- A new plugin (a language or a config-file type) is a subpackage
  (`code_cleanup/<plugin>/`) exposing `clean_<plugin>(text, path, settings) ->
  Cleaned`, and optionally a whole-project check, registered in `router.py` by
  suffix or file name, with its settings section in `style.yaml` and `settings.py`.
  Model a language on `code_cleanup/python/`, a config file on `toml/` or `ignore/`.
- The flow is: pinned formatter/linter first (ruff, taplo), then our fixes, then
  checks (lint, type checker, our `CC` rules). Codes are grouped by concept, not
  language, so a new language reuses them: `CC0xx` file, `CC1xx` modules, `CC2xx`
  logging, `CC3xx` layout, `CC4xx` config files.
