# code-cleanup

One house style for every file in a repo. Point it at a directory: it walks every
file (honouring `.gitignore`), picks the plugin from each file's name, and cleans it.
The same input always gives the same output, on a laptop and in CI: every tool it
runs is pinned, and a project's own tool configs never change the result.

```sh
pip install code-cleanup        # or: uv tool install code-cleanup

code-cleanup                    # fix the current repo in place
code-cleanup path/to/repo       # fix another repo
code-cleanup --check            # CI: report only, exit 1 if anything would change
code-cleanup --check --report junit > report.xml
```

There is no `--language` flag: a router maps each file to its plugin, and files no
plugin claims are skipped.

| Plugin | Files | Status |
|---|---|---|
| Python | `*.py`, `*.pyi` | done |
| TOML | `*.toml` | done |
| Ignore files | `.gitignore`, `.dockerignore` | done |
| Java, TypeScript, Kotlin | | next, built on the Python rules |
| YAML (Spring config), log4j | | planned |

See [examples/tictactoe](examples/tictactoe/) for a real before/after run with screenshots.

## The flow

Each file is fixed, then the whole project is checked:

1. **ruff** (pinned): `ruff check --fix` for safe lint fixes, then `ruff format`.
2. **Our fixes** on top: the spacing rules ruff has no setting for, and relative
   imports inside a package.
3. **Checks**: ruff findings that cannot be fixed, then **mypy --strict** (pinned)
   over the cleaned files, then **our own rules** (the `CC` codes below).

mypy type-checks a temporary copy of the cleaned files, so its line numbers match the
cleaned code and nothing is written into the project. It uses `ROOT/.venv` for
third-party packages when present.

### Python fixes

- A blank line before and after every `if` / `for` / `while` / `with` / `try` /
  `match` block, above a comment that opens a block, and between `try` and each
  `except` / `finally`; none between an `if` body and its `elif` / `else`. A
  docstring counts as part of its function's header.
- `from tool.errors import X` inside the `tool` package becomes `from .errors import X`.
- ruff's safe fixes, for example `Optional[str]` to `str | None`, and f-strings in
  log calls to lazy `"%s", value` arguments.

### TOML

taplo (pinned) formats with a 4-space indent and width 88; then a blank line goes
above every `[table]` together with the comments that introduce it, and `#note`
becomes `# note`.

### Ignore files

Blocks of patterns, each under a `# comment` header, separated by one blank line.
Patterns are sorted within a block and repeats dropped, only where no `!` negation
makes order matter, so the set of ignored files never changes.

## Profiles

`profile` in `.code-cleanup.yaml` says what kind of project this is:

- `none` (default): file rules only.
- `cli`: also the python-style project layout (`CC3xx`): one package per tool run as
  `python -m <tool>`, an entry module of a fixed shape, `errors.py`, and tests that
  mirror modules.

A `service` profile (JSON logs, REST layout) comes with the Java work.

## Codes

| Code | Meaning | Fixed? |
|---|---|---|
| `CC000` | syntax error; the file is left as is | |
| `CC001` | file over 350 lines (warning) or 400 lines (error) | |
| `CC101` | absolute import of the own package | yes, for `from` imports |
| `CC102` | more than two UPPER_CASE module constants; move the rest to config | |
| `CC103` | a docstring; names and small functions carry the meaning | |
| `CC104` | reads the environment; take a flag or config.yaml instead | |
| `CC201` | `logging.basicConfig` outside `__main__.py` | |
| `CC202` | logger not named `getLogger("<tool>")` (entry) / `getLogger(__name__)` | |
| `CC203` | `basicConfig` without the house `format` and `datefmt` | |
| `CC301` | module at the repo root (`profile: cli`) | |
| `CC302` | module with functions but no `tests/test_<module>.py` (`profile: cli`) | |
| `CC303` | entry module shape: `main() -> int`, frozen `Options`, `raise SystemExit(main())` | |
| `CC304` | no `errors.py` with a `ToolError(Exception)` base (`profile: cli`) | |
| `CC305` | a tool imports another tool; share through `utils` (`profile: cli`) | |
| `CC401` | ignore-file block without a `# comment` header | |
| `mypy:*` | mypy error codes | |
| others | ruff rule codes | some |

Warnings never fail a run. Errors fail both modes; `--check` also fails when any
file would change.

## Customising

The house style ships inside the package (`code_cleanup/style.yaml`). A project
overrides any key in `.code-cleanup.yaml` at its root (or `--config FILE`):
mappings merge key by key, lists and values replace.

```yaml
profile: cli

file_length:
  max: 500

python:
  checks:
    allow_docstrings: true
  mypy:
    enabled: false
  ruff:
    line-length: 100
```

## Development

Written to the `python-style` skill (in
[rkgreathouse/setup](https://github.com/rkgreathouse/setup), `claude/dot-claude/skills/python-style`),
and checked by itself under `profile: cli`. Done when all four pass:

```sh
uv run code-cleanup .
uv run mypy .
uv run pytest
uv run code-cleanup --help
```
