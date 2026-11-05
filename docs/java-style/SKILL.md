---
name: java-style
description: The user's Java house style for Spring Boot REST services (Maven layout, entry class, spacing, errors, JSON logging, tests). Use when writing, editing, scaffolding, or reviewing Java code.
---

# Java style

The Java translation of the `python-style` skill. Spacing, decomposition, errors,
logging and layout follow the same rules; only the shape changes. Every rule here
is checked by `code-cleanup` (rule codes in brackets). `example/` is a complete
service written to these rules; when a rule and the example seem to disagree, the
example wins.

Scope for now: **Spring Boot REST services only** (`profile: service`). A Java
CLI layout mirroring `profile: cli` is not written yet.

Pinned toolchain: Java 21 (or the release the `pom.xml` declares), Maven,
Spring Boot 4.1, google-java-format 2.0.0, Checkstyle 14.4.0, Error Prone 2.52.0.

## Layout

One Maven project per service, in the standard Maven layout [CC301]. The root
package holds the entry class and the settings record; each feature gets its own
package; errors get one package.

```
bookmarks/
├── pom.xml
├── .code-cleanup.yaml                 profile: service
└── src/
    ├── main/
    │   ├── java/com/example/bookmarks/
    │   │   ├── Application.java       entry class
    │   │   ├── Settings.java          application.yml → @ConfigurationProperties record
    │   │   ├── ClockConfig.java       @Configuration beans
    │   │   ├── bookmark/              one package per feature
    │   │   │   ├── Bookmark.java              record
    │   │   │   ├── BookmarkRequest.java       validated request record
    │   │   │   ├── BookmarkController.java    HTTP only
    │   │   │   ├── BookmarkService.java       the rules
    │   │   │   └── BookmarkRepository.java    storage
    │   │   └── errors/
    │   │       ├── ApiException.java          base
    │   │       ├── NotFoundException.java     one per failure
    │   │       └── ErrorHandler.java          the only place that maps errors
    │   └── resources/
    │       ├── application.yml
    │       └── log4j2-spring.xml
    └── test/java/com/example/bookmarks/       mirrors main, one <Class>Test each
```

- A request flows controller → service → repository. A controller never touches
  a repository [CC306].
- Features stay apart: a feature reaches another feature through its service,
  never by importing its controller or repository [CC305]. Shared code goes in
  its own package.
- Every class in `src/main/java` sits under the entry class's package [CC303].

## Entry class

`Application` is the only `@SpringBootApplication` class, in the root package,
and does one thing [CC303]:

```java
@SpringBootApplication
@ConfigurationPropertiesScan
public class Application {

  public static void main(String[] args) {
    SpringApplication.run(Application.class, args);
  }
}
```

Beans go in `@Configuration` classes beside it (`ClockConfig`), not in
`Application`.

## Classes and methods

- Spring components take their collaborators through one constructor into
  `private final` fields. Field injection is left out, except `@Autowired` in tests.
- Data is a `record`: requests, responses, domain values, settings. Validate
  requests with Bean Validation annotations and `@Valid` in the controller.
- One job per method, named verb-first (`addBookmark`, `findTagged`).
- Guard clauses: handle the failing case and return or throw early; the main
  path stays unindented.
- Length is free; branching is capped. Cyclomatic complexity ≤ 10 (Checkstyle)
  and nesting ≤ 4 blocks [CC107]; an `else if` counts as its `if`, and a lambda
  starts its own count.
- Locals use `var` when the type is plain from the right-hand side. That is the
  Java form of the Python rule to leave locals unannotated.

## Streams

The Java form of the comprehension rule [CC105]:

- Build a list with a stream rather than a loop that only adds:
  `repository.findAll().stream().filter(bookmark -> bookmark.hasTag(tag)).toList()`.
- At most one `map` and one `filter`, no `flatMap`, and no stream inside a
  lambda. Anything bigger is a loop, or a helper method the stream calls.
- Test and bind in one step with pattern matching: `if (value instanceof Bookmark
  bookmark)` (Error Prone `PatternMatchingInstanceof`, a warning).

## Spacing

google-java-format sets indent (2), width (100), imports and braces. On top of
it, the same blank lines as Python:

- before and after every `if` / `for` / `while` / `do` / `try` / `switch` /
  `synchronized` block, including after the run of setup statements;
- before `} catch` and `} finally`, so each clause's body is set apart;
- before a comment that introduces a block, even when it opens its parent block.

No blank line opens a method or block otherwise, and an `if` body sits directly
against its `} else`. See `BookmarkService.addBookmark`.

## Constants and config

- A file holds at most two `static final` UPPER_CASE constants that are true facts
  [CC102]. The `log` field does not count.
- Anything tunable goes in `application.yml` [CC402: not `.properties`], under
  the service's prefix, bound once to a validated `@ConfigurationProperties`
  record (`Settings`) that is passed to whoever needs it.
- Code reads no environment variables or system properties, and does not use
  `@Value` [CC104]. Spring's own relaxed binding still lets operations override a
  key from the environment; code only ever sees the record.

## Errors

- `errors/` holds one abstract base, `ApiException extends RuntimeException`,
  and a subclass per failure (`NotFoundException`, `ConflictException`) [CC304].
- Throw with the context needed to act: `new NotFoundException("no bookmark " + id)`.
- One `@RestControllerAdvice`, `ErrorHandler`, is the only place that turns
  failures into responses: one `@ExceptionHandler` per subclass, each picking
  the HTTP status and returning a `ProblemDetail` (RFC 9457) [CC304]. Code never
  catches `Exception`, `RuntimeException` or `Throwable` (Checkstyle
  `IllegalCatch`), and never leaves a catch empty.

## Logging

- Code logs through SLF4J; log4j2 is the backend, set up once in
  `src/main/resources/log4j2-spring.xml` with a `JsonTemplateLayout` (ECS) to
  stdout [CC203]. Code never configures logging [CC201].
- Each class that logs declares exactly
  `private static final Logger log = LoggerFactory.getLogger(ThisClass.class);` [CC202].
- Messages are constants with `{}` placeholders; values go as arguments, never
  joined with `+` or `String.format` [CC204].
- Nothing prints to `System.out` or `System.err` (Checkstyle `Regexp`).

## Comments

Names and small methods carry the meaning; Javadoc is left out [CC103]. A comment
appears only above a condition whose reason is not visible in the code, and
states that reason in one line:

```java
// the same page saved twice is one bookmark; the second save is a client mistake
if (repository.findByUrl(request.url()).isPresent()) {
```

## Tests

- JUnit 5 and AssertJ, in `src/test/java`, mirroring the main packages: one
  `<Class>Test` per class with methods [CC302]. `@Configuration` and
  `@ConfigurationProperties` classes are covered by `ApplicationTest`.
- Services and repositories are tested as plain objects built in the test, with a
  fixed `Clock`; controllers through `@SpringBootTest` with `MockMvcTester`.
- Test names state the behaviour: `rejectsTheSameUrlTwice`.

## Files

A file stays under 400 lines, aiming for 350 [CC001].

## Finishing

Done when both pass from the service root:

```sh
mvn verify                       # compiles, runs the tests
code-cleanup --check .           # format, Checkstyle, Error Prone, CC rules
```
