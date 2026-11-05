# code-cleanup

One house style for every file in a repo. Point it at a directory: it walks every
file (honouring `.gitignore`), picks the language from each file, and cleans it.
The same input always gives the same output, on a laptop and in CI.

```sh
pip install code-cleanup        # or: uv tool install code-cleanup

code-cleanup                    # fix the current repo in place
code-cleanup path/to/repo       # fix another repo
code-cleanup --check            # CI: report only, exit 1 if anything would change
code-cleanup --check --report junit > report.xml
```

There is no `--language` flag: a router maps each file to its language plugin, and
files no plugin claims are skipped.

| Language | Status |
|---|---|
| Python | done |
| Java, TypeScript, Kotlin | next, built on the Python rules |
| YAML (Spring config), log4j, ignore files | planned |

See [examples/tictactoe](examples/tictactoe/) for a real before/after run with screenshots.

## What the Python plugin does

In order, on each `.py` / `.pyi` file:

1. `ruff check --fix`: safe lint fixes (unused imports, import order, `pathlib`, ...).
2. `ruff format`: line length 88, double quotes.
3. Spacing pass (ours, ruff has no setting for these):
   - a blank line before and after every `if` / `for` / `while` / `with` / `try` /
     `match` block;
   - a blank line above a comment that opens a block (ruff deletes it);
   - a blank line between a `try` body and each `except` / `finally`;
   - no blank line between an `if` body and its `elif` / `else`.
4. Report what cannot be fixed: remaining ruff findings, plus our own checks.

ruff is pinned to an exact version and run with a config generated from the style,
so a project's own ruff settings never change the result.

## Codes

| Code | Meaning |
|---|---|
| `CC000` | syntax error; the file is left as is |
| `CC001` | file over 350 lines (warning) or 400 lines (error) |
| `CC101` | a package imports itself absolutely; use `from .module import name` |
| `CC102` | more than two UPPER_CASE module constants; move the rest to config |
| `CC103` | a docstring; names and small functions carry the meaning (`allow_docstrings: true` to permit) |
| others | ruff rule codes |

Warnings never fail a run. Errors fail both modes; `--check` also fails when any
file would change.

## Customising

The house style ships inside the package (`code_cleanup/style.yaml`). A project
overrides any key in `.code-cleanup.yaml` at its root (or `--config FILE`):
mappings merge key by key, lists and values replace.

```yaml
file_length:
  max: 500

python:
  spacing:
    tight_else: false
  ruff:
    line-length: 100
```

## Development

Written to the `python-style` skill (in
[rkgreathouse/setup](https://github.com/rkgreathouse/setup), `claude/dot-claude/skills/python-style`).
Done when all four pass:

```sh
uv run code-cleanup .
uv run mypy .
uv run pytest
uv run code-cleanup --help
```
