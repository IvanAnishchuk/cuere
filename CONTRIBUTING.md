# Contributing to cuere

Thanks for your interest! This describes how to contribute code, docs, or bug
reports to cuere.

## Code of conduct

By participating you agree to the [Code of Conduct](CODE_OF_CONDUCT.md):
be kind, assume good faith, ask if unsure.

## Development setup

cuere uses [uv](https://docs.astral.sh/uv/) and the meson-python build backend.

```sh
git clone https://github.com/IvanAnishchuk/cuere.git
cd cuere
uv sync                 # editable install via meson-python

# Install pre-commit hooks (one-time, required)
uv run pre-commit install --install-hooks
uv run pre-commit install --hook-type commit-msg
uv run pre-commit install --hook-type pre-push
```

### The quality bar (all enforced in CI)

- `uv run pytest` — **100% branch coverage** (`fail_under = 100`).
- `uv run ruff check` and `uv run ruff format --check`.
- **All three type checkers, zero errors and zero warnings:**
  `uv run mypy src/ tests/` (strict), `uv run ty check`, `uv run basedpyright`.
- `uv run zizmor .github/workflows/` for any workflow change.

Because the hooks run via `uv run`, local results match CI.

### meson-python gotchas

- **Meson does not glob.** A new file under `src/cuere/` must be added to
  `src/cuere/meson.build` (`py.install_sources`) or it won't ship in wheels;
  `tests/test_packaging.py` guards this.
- The version lives **only** in the root `meson.build`.
- sdists come from `meson dist` (git archive) — **commit before `uv build`**,
  or uncommitted files won't be in the artifact.

### Mutation testing (local)

`uv run mutmut run` checks test *quality* beyond coverage. It is **local-only**
(not a CI gate); kill meaningful survivors with new tests.

## Signed commits are required

Commits merged to `main` **must be cryptographically signed** (branch
protection rejects unsigned commits). Use GPG, SSH, or sigstore/gitsign — see
GitHub's docs on commit signing.

## Developer Certificate of Origin (DCO)

Sign off every commit (`git commit -s`) to certify you may submit it under the
project's CC0 license.

## Commit messages — Conventional Commits (required, CI-enforced)

```
<type>(<optional-scope>): <subject>
```

- Subject ≤ 72 chars, imperative, no trailing period; body wraps at 72.
- One commit = one logical change; always sign (`-S`) and sign-off (`-s`).
- Types: `feat`, `fix`, `security`, `perf`, `docs`, `test`, `refactor`,
  `style`, `chore`, `ci`, `build`, `revert`.
- Scopes: `matrix`, `render`, `terminal`, `rich`, `wallet`, `cli`, `ci`,
  `deps`, `docs`, `release`.

## Testing

All new behavior needs tests, and coverage must stay at **100%** (branch).
Prefer Hypothesis property tests where a round-trip or invariant fits.
Golden files in `tests/golden/` pin exact render output — if you change a
renderer, regenerate them **and scan the result with a phone** before
committing.

## Pull request checklist

- [ ] Tests added/updated; `uv run pytest` passes at 100% coverage
- [ ] `uv run pre-commit run --all-files` passes (ruff, types, zizmor, gitleaks)
- [ ] `CHANGELOG.md` updated under `## [Unreleased]`
- [ ] Docs updated if the public interface changed
- [ ] Commits signed (`-S`) and DCO-signed off (`-s`), Conventional Commits

## Reporting security issues

**Do not open public issues for vulnerabilities.** See
[SECURITY.md](SECURITY.md) for private reporting.

## License

Contributions are released under the project's
[CC0 1.0 Universal](LICENSE.md) dedication.
