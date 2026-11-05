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
| Java (Spring REST services) | `*.java` | done |
| TOML | `*.toml` | done |
| Ignore files | `.gitignore`, `.dockerignore` | done |
| TypeScript, Kotlin | | next, built on the Python rules |
| YAML (`application.yml`), log4j2 XML | | planned; the service profile checks they exist |

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

### Java

Needs a JDK 21+ and Maven on `PATH`. The Java tools are pinned by Maven coordinate
in the style and resolved through Maven once, into `~/.cache/code-cleanup/java`.

1. **google-java-format** 2.0.0 (2-space indent, 100 columns, no options) formats.
2. **Our fixes**: the Python spacing rules: a blank line around every block,
   before `} catch` / `} finally`, and above a comment that opens a block; none
   opening a block otherwise.
3. **Checks**: our `CC` rules per file; then over all cleaned files at once
   **Checkstyle** 14.4.0 (rules rendered from `java.checkstyle` in the style) and
   **Error Prone** 2.52.0, which compiles each Maven module's cleaned sources
   against the classpath from `mvn dependency:build-classpath`. The release comes
   from the project's `pom.xml` (`maven.compiler.release`, `java.version`), else 21.

The style for Java code is [docs/java-style](docs/java-style/SKILL.md), with a
complete example service in [docs/java-style/example](docs/java-style/example/).

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

- `service`: also the java-style Spring REST layout (`CC3xx`, `CC203`, `CC402`):
  Maven layout, one `Application` entry class, an `errors` package with a
  `@RestControllerAdvice`, controller → service → repository, tests that mirror
  classes, JSON logs through `log4j2-spring.xml`, settings in `application.yml`.

## Codes

| Code | Meaning | Fixed? |
|---|---|---|
| `CC000` | syntax error; the file is left as is | |
| `CC001` | file over 350 lines (warning) or 400 lines (error) | |
| `CC101` | absolute import of the own package | yes, for `from` imports |
| `CC102` | more than two UPPER_CASE module constants (Java: `static final` per file); move the rest to config | |
| `CC103` | a docstring or Javadoc; names and small functions carry the meaning | |
| `CC104` | reads the environment (Java: also `System.getProperty`, `@Value`); take a flag or config file instead | |
| `CC105` | comprehension with more than one `for` or `if`, or nested (Java: stream with more than one `map` or `filter`, a `flatMap`, or a nested stream); use a loop | |
| `CC106` | warning: a value only tested once; use `if x := ...` | |
| `CC107` | Java: nested more than 4 blocks deep | |
| `CC201` | `logging.basicConfig` outside `__main__.py`; Java: configures logging in code | |
| `CC202` | logger not named `getLogger("<tool>")` (entry) / `getLogger(__name__)`; Java: not `private static final Logger log = LoggerFactory.getLogger(This.class)` | |
| `CC203` | `basicConfig` without the house `format` and `datefmt`; Java: no JSON `log4j2-spring.xml` (`profile: service`) | |
| `CC204` | Java: log message built with `+` or `String.format`; use `{}` | |
| `CC301` | module at the repo root (`profile: cli`); Java source outside `src/{main,test}/java` (`profile: service`) | |
| `CC302` | module with functions but no `tests/test_<module>.py` (`profile: cli`); class with methods but no `<Class>Test` (`profile: service`) | |
| `CC303` | entry module shape: `main() -> int`, frozen `Options`, `raise SystemExit(main())`; Java: one `Application` that only runs Spring, at the root package | |
| `CC304` | no `errors.py` with a `ToolError(Exception)` base (`profile: cli`); Java: no `errors` package with a `RuntimeException` base and a `@RestControllerAdvice` (`profile: service`) | |
| `CC305` | a tool imports another tool; share through `utils` (`profile: cli`); Java: a feature imports another feature's controller or repository (`profile: service`) | |
| `CC306` | a controller uses a repository; call a service (`profile: service`) | |
| `CC401` | ignore-file block without a `# comment` header | |
| `CC402` | `application.properties`, or no `application.yml` (`profile: service`) | |
| `mypy:*` | mypy error codes | |
| `checkstyle:*`, `errorprone:*`, `javac` | Checkstyle modules, Error Prone bug patterns, compile errors | |
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

The Java example service is checked on its own, under `profile: service`:

```sh
uv run code-cleanup --check docs/java-style/example
(cd docs/java-style/example && mvn verify)
```
