# Mutation testing

`cuere` keeps 100% branch coverage, but coverage only proves a line *ran* — not
that a test would *fail* if its behavior changed. We use
[mutmut](https://mutmut.readthedocs.io/) to measure that: it makes small
edits ("mutants") to the source and checks whether the test suite catches each
one. A surviving mutant is a hole in the assertions, not the coverage.

Mutation testing is **run locally, never in CI** — it is slow and the surviving
set is reviewed by hand (some mutants are equivalent; see below). Config lives in
`pyproject.toml` under `[tool.mutmut]`.

## Running it

Mutmut must run with cuere **uninstalled**. meson-python's editable install
registers a `sys.meta_path` import hook that shadows the `conftest.py`
`sys.path` insert, so with the package installed `import cuere` resolves to the
real `src/cuere` instead of the mutated copy under `mutants/`, and mutmut reports
"could not find any test case for any mutant". Uninstall the project first, then
run mutmut without letting `uv run` re-sync it:

```bash
uv sync --no-install-project        # install deps but NOT cuere itself
uv run --no-sync mutmut run         # mutate src/cuere/ and run the suite per mutant
uv run --no-sync mutmut results     # list survivors
uv run --no-sync mutmut show <id>   # one mutant's diff, e.g. cuere.terminal.x_fits__mutmut_24
uv sync                             # restore the editable install when done
```

The root `conftest.py` puts the in-tree `src/` on `sys.path` so that — with the
package uninstalled — `import cuere` resolves to the mutated copy mutmut places
under `mutants/` (gitignored). The mutmut config clears cuere's coverage/junit
`addopts` and deselects three install-dependent tests (subprocess re-import +
distribution metadata) that cannot pass with the project run uninstalled, as
mutation runs require.

## Type-check pass (mypy)

Before running tests, mutmut runs mypy once over the whole mutant tree
(`type_check_command` in `[tool.mutmut]`). A mutant that introduces a *type*
error — e.g. passing `None` to a parameter typed `bool`/`RenderMode` — is
"caught by the type checker" (🧙 in the progress line) and skipped from the test
run. This both speeds the run up and catches defects no runtime test needs to.

It uses a **relaxed** config, `mutmut-mypy.ini`, not the project's strict
settings (`[tool.mypy]`). mutmut's own scaffolding — the
`mutmut.mutation.trampoline` import, the untyped trampoline decorator, and
injected `# type: ignore` comments — would otherwise produce errors on
non-mutant lines, and mutmut crashes if any reported error does not fall inside a
mutant function. The relaxed config (`ignore_missing_imports`, no strict-only
warnings) reports only genuine type errors inside the mutant bodies. mypy's
JSON-lines output (`--output=json`) is required by mutmut's parser. A
consequence: the baseline must type-check clean (it does — see the main CLAUDE.md
gate), or mutmut will fail to map an error to a mutant.

## Hypothesis under mutmut

`tests/conftest.py` loads a dedicated `mutmut` hypothesis profile (selected when
mutmut sets `MUTANT_UNDER_TEST`) that **disables the shrink phase**. Under
mutation testing a failing example already means the mutant is caught, so
shrinking it is pure overhead that can overrun mutmut's per-mutant timeout and
turn a clean kill into a flaky `⏰`. Generation is unaffected, so detection is
unchanged; normal `pytest` runs keep full shrinking.

## Current status

As of the suite in this branch: **219 mutants — 99 killed by tests, 116 caught
by the type checker, 4 survivors (~98.2% caught)**. All 4 survivors are
**equivalent mutants** that are also type-safe (so mypy cannot catch them
either) — the mutated code is behaviorally identical to the original, so no test
can distinguish it without asserting something artificial or weakening the code.
They are listed below and **accepted for now**. This is not cemented: a later
iteration may revisit whether any can be removed by a small refactor.

(mutmut's numeric mutant IDs shift whenever the source changes, so the table
describes the *mutation*, not a fixed `__mutmut_N` id.)

## Accepted equivalent mutants

| Mutation | Why it is equivalent |
| --- | --- |
| `render._half_lines`: `zip(top, bottom, strict=True)` → `strict=False` / `strict` removed | `top` and `bottom` are always equal length by construction — `bottom` is either the next matrix row (rectangular) or an explicit `len(top)` light row — so `strict` can never trip. Kept as a defensive invariant. (The `strict=None` variant *is* caught by the type checker.) |
| `terminal.show`: `warnings.warn(..., stacklevel=2)` dropped / changed to `3` | `stacklevel` only affects the file/line the warning is attributed to; it is not observable from the warning object, so no meaningful assertion exists. |

Several other `None`-substitution mutants (e.g. `_half_lines`'s `strict=None`,
`show`'s `render_mode=None`) are caught by the type-check pass rather than by a
test — each passes `None` where a concrete type is required, which mypy rejects.
(An earlier run also had two `fits` `boost_error` equivalents; the encode-options
DRY removed those per-call mutation sites, so the kwarg is now only mutated once,
in `QRMatrix.encode`.)

If a future run reports a *new* survivor not in this table, it is a real gap —
add a test that pins the affected behavior rather than extending this list.
