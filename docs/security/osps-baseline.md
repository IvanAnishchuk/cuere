# OpenSSF OSPS Baseline conformance

cuere conforms to **Level 2** of the
[OpenSSF Open Source Project Security (OSPS) Baseline](https://baseline.openssf.org/),
catalog version **2026-02**. The Baseline is a tiered set of security controls
(Levels 1–3) that complements the [OpenSSF Scorecard](https://scorecard.dev/)
and the Best Practices Badge by grading project *practices* a static scan can't.

This page is the human-readable conformance record. The machine-readable source
of truth is [`security-insights.yml`](https://github.com/IvanAnishchuk/cuere/blob/main/security-insights.yml)
(OpenSSF [Security Insights](https://security-insights.openssf.org/) v2.2.0) in
the repository root, which the
[Privateer GitHub-repo scanner](https://github.com/ossf/pvtr-github-repo-scanner)
and LFX Insights read to assess conformance automatically.

!!! info "Why Level 2"
    Level 2 adds release integrity, governance, security-assessment, and
    vulnerability-management requirements on top of Level 1's access-control,
    licensing, and quality basics. cuere meets all of them today. The Level 3
    controls (which add formal CVD timeframes, dependency-provenance/SBOM-at-
    build, and historical-vulnerability publication processes) are tracked in
    [#84](https://github.com/IvanAnishchuk/cuere/issues/84) and
    [#85](https://github.com/IvanAnishchuk/cuere/issues/85).

## Supporting documentation

The Baseline's documentation controls are satisfied by these pages and files:

| Document | Backs |
|----------|-------|
| [Architecture & design](design.md) | OSPS-SA-01.01 (design documentation) |
| [Threat model & self-assessment](threat-model.md) | OSPS-SA-03.01 (security assessment) |
| [Dependency management](dependencies.md) | OSPS-DO-06.01 (dependency policy) |
| [Building from source](../building.md) | Build transparency / reproducibility |
| [GOVERNANCE.md](https://github.com/IvanAnishchuk/cuere/blob/main/GOVERNANCE.md) | OSPS-GV-01.01/01.02 (members, roles) |
| [SECURITY.md](https://github.com/IvanAnishchuk/cuere/blob/main/SECURITY.md) | OSPS-VM-01.01/02.01/03.01 (CVD, contacts, private reporting) |
| [CONTRIBUTING.md](https://github.com/IvanAnishchuk/cuere/blob/main/CONTRIBUTING.md) | OSPS-GV-03.01/03.02, OSPS-LE-01.01 (contribution & review guide, DCO) |

## Control-by-control conformance

Every Level 1 and Level 2 requirement in the 2026-02 catalog, and how cuere
meets it. (Level 3 requirements are out of scope for this claim — see
[#84](https://github.com/IvanAnishchuk/cuere/issues/84) /
[#85](https://github.com/IvanAnishchuk/cuere/issues/85).)

### Access control (AC)

| ID | Lvl | Requirement | How cuere conforms |
|----|-----|-------------|--------------------|
| AC-01.01 | 1 | MFA to read/modify sensitive resources | Account-wide two-factor authentication is enforced on the maintainer's GitHub account. |
| AC-02.01 | 1 | New collaborators get least privilege by default | GitHub assigns no access by default; permissions are granted manually at the lowest level (see [GOVERNANCE.md](https://github.com/IvanAnishchuk/cuere/blob/main/GOVERNANCE.md)). |
| AC-03.01 | 1 | Block direct commits to the primary branch | `main` is protected — PRs with review are required; direct pushes are rejected (`.github/settings.yml`). |
| AC-03.02 | 1 | Branch deletion requires confirmed intent | Branch protection forbids deletion and force-push of `main` (`allow_deletions: false`). |
| AC-04.01 | 2 | CI jobs default to least permission | Every workflow sets a top-level `permissions: {}` and grants only the minimum per job; audited by **zizmor** in CI and pre-commit. See the [scanner note](#scanner-results) below. |

### Build & release (BR)

| ID | Lvl | Requirement | How cuere conforms |
|----|-----|-------------|--------------------|
| BR-01.01 | 1 | Sanitize/validate pipeline inputs | Workflows pass untrusted values through `env:` (never interpolated into `run:`); zizmor enforces this. |
| BR-01.02 | 1 | Sanitize/validate branch names in CI | Same env-var discipline; no unsanitized `github.head_ref` in shell steps. |
| BR-02.01 | 2 | Unique version identifier per release | Releases are tagged `vX.Y.Z` (SemVer); the release workflow asserts the built version matches the tag. |
| BR-03.01 | 1 | Official channels delivered over HTTPS | All project URIs in `security-insights.yml` and the docs are HTTPS. |
| BR-03.02 | 1 | Distribution channels over HTTPS | Distribution points are the HTTPS PyPI project page (`https://pypi.org/project/cuere/`) and the GitHub releases page — both HTTPS. |
| BR-04.01 | 2 | Releases carry a change log | [`CHANGELOG.md`](https://github.com/IvanAnishchuk/cuere/blob/main/CHANGELOG.md) (Keep a Changelog) plus per-release notes. |
| BR-05.01 | 2 | Standardized build/dependency tooling | Builds use **uv** + **meson-python** (PEP 517/660); dependencies resolve from the committed `uv.lock`. |
| BR-06.01 | 2 | Releases signed / signed manifest with hashes | Each release ships **sigstore** signatures, **SLSA** provenance, **PEP 740** attestations, and a **CycloneDX SBOM** — see [verifying a release](https://github.com/IvanAnishchuk/cuere/blob/main/SECURITY.md#verifying-a-release). |
| BR-07.01 | 1 | Prevent unencrypted secrets in VCS | **gitleaks** (CI + pre-commit) and GitHub secret scanning with **push protection**; cuere has no runtime secrets. |

### Documentation (DO)

| ID | Lvl | Requirement | How cuere conforms |
|----|-----|-------------|--------------------|
| DO-01.01 | 1 | User guides for basic functionality | The [README](https://github.com/IvanAnishchuk/cuere) and the [documentation site](https://ivananishchuk.github.io/cuere/) (Quickstart, guides, cookbook, CLI/API reference). |
| DO-02.01 | 1 | A guide for reporting defects | Bug/feature/question [issue templates](https://github.com/IvanAnishchuk/cuere/tree/main/.github/ISSUE_TEMPLATE) and [CONTRIBUTING.md](https://github.com/IvanAnishchuk/cuere/blob/main/CONTRIBUTING.md). |
| DO-06.01 | 2 | Describe how dependencies are selected/obtained/tracked | The [dependency management](dependencies.md) policy. |

### Governance (GV)

| ID | Lvl | Requirement | How cuere conforms |
|----|-----|-------------|--------------------|
| GV-01.01 | 2 | List members with access to sensitive resources | [GOVERNANCE.md → Members with access](https://github.com/IvanAnishchuk/cuere/blob/main/GOVERNANCE.md#members-with-access-to-sensitive-resources); mirrored in `security-insights.yml` `core-team`. |
| GV-01.02 | 2 | Document roles and responsibilities | [GOVERNANCE.md → Roles and responsibilities](https://github.com/IvanAnishchuk/cuere/blob/main/GOVERNANCE.md#roles-and-responsibilities). |
| GV-02.01 | 1 | Public discussion mechanism | GitHub **Issues** and the public [project board](https://github.com/users/IvanAnishchuk/projects/4). |
| GV-03.01 | 1 | Explain the contribution process | [CONTRIBUTING.md](https://github.com/IvanAnishchuk/cuere/blob/main/CONTRIBUTING.md) and the [Code of Conduct](https://github.com/IvanAnishchuk/cuere/blob/main/CODE_OF_CONDUCT.md). |
| GV-03.02 | 2 | Code-contributor guide with acceptance requirements | CONTRIBUTING.md states the quality bar (100% coverage, three type checkers, signed + DCO-signed commits) and the [PR checklist](https://github.com/IvanAnishchuk/cuere/blob/main/CONTRIBUTING.md#pull-request-checklist). |

### Legal (LE)

| ID | Lvl | Requirement | How cuere conforms |
|----|-----|-------------|--------------------|
| LE-01.01 | 2 | Contributors assert legal authorization on every commit | **DCO sign-off** (`Signed-off-by:`) is required on every commit — enforced by a `commit-msg` pre-commit hook and the **DCO** CI check (`scripts/check_dco.py`), documented in [CONTRIBUTING.md → DCO](https://github.com/IvanAnishchuk/cuere/blob/main/CONTRIBUTING.md#developer-certificate-of-origin-dco). |
| LE-02.01 | 1 | Source license is OSI/FSF-approved | **CC0-1.0** — see note below. |
| LE-02.02 | 1 | Released-assets license is OSI/FSF-approved | CC0-1.0 applies to the published wheels/sdists too. |
| LE-03.01 | 1 | License in `LICENSE`/`COPYING`/`LICENSE/` | [`LICENSE.md`](https://github.com/IvanAnishchuk/cuere/blob/main/LICENSE.md) at the repository root. |
| LE-03.02 | 1 | License included with release assets | `LICENSE.md` is committed and therefore included in the `meson dist` sdist. |

!!! note "CC0-1.0 and the OSI/FSF test"
    The control requires a license meeting the OSI Open Source Definition **or**
    the FSF Free Software Definition. cuere is released under
    [CC0-1.0](https://github.com/IvanAnishchuk/cuere/blob/main/LICENSE.md), a
    public-domain dedication. OSI has not added CC0 to its approved-licenses
    list, but the **FSF** classifies CC0 as a free, GPL-compatible license — so
    cuere satisfies the requirement via the FSF arm of the test. The Privateer
    scanner confirms this (it reports the license as "OSI or FSF approved").

### Quality (QA)

| ID | Lvl | Requirement | How cuere conforms |
|----|-----|-------------|--------------------|
| QA-01.01 | 1 | Public repo at a static URL | [github.com/IvanAnishchuk/cuere](https://github.com/IvanAnishchuk/cuere) is public. |
| QA-01.02 | 1 | Public record of all changes (who/when) | Full git history; `main` requires signed commits. |
| QA-02.01 | 1 | Dependency list for direct dependencies | `pyproject.toml` declares the runtime/optional/dev dependencies; `uv.lock` pins the full set. |
| QA-03.01 | 2 | Automated status checks must pass (or be bypassed) before merge | `main`'s required checks (tests, lint, three type checkers, CodeQL, dependency audit, OSV scan, secret scan, dependency-review, Actions audit) must all pass before merge; the DCO check runs on every PR. See the [scanner note](#scanner-results) on the informational Benchmark job. |
| QA-04.01 | 1 | List any subprojects | cuere has no subprojects; `security-insights.yml` lists the single repository. |
| QA-05.01 | 1 | No generated executable artifacts in VCS | The tree contains source only; `tests/test_packaging.py` guards the shipped file list. |
| QA-05.02 | 1 | No unreviewable binary artifacts in VCS | None present (the one binary, the README demo GIF, is a reviewable, regenerable asset). |
| QA-06.01 | 2 | CI runs ≥1 automated test suite before accepting a commit | The **test** workflow runs the full pytest suite (100% branch coverage) as a required check on every PR. |

### Security assessment (SA)

| ID | Lvl | Requirement | How cuere conforms |
|----|-----|-------------|--------------------|
| SA-01.01 | 2 | Design documentation of actions and actors | [Architecture & design](design.md). |
| SA-02.01 | 2 | Describe external software interfaces | The auto-generated [API reference](https://ivananishchuk.github.io/cuere/reference/api/) (mkdocstrings) and [CLI reference](https://ivananishchuk.github.io/cuere/cli-reference/) (mkdocs-typer2). |
| SA-03.01 | 2 | Perform a security assessment | The [threat model & self-assessment](threat-model.md), recorded as `security.assessments.self` in `security-insights.yml`. |

### Vulnerability management (VM)

| ID | Lvl | Requirement | How cuere conforms |
|----|-----|-------------|--------------------|
| VM-01.01 | 2 | Coordinated vulnerability disclosure policy with a response timeframe | [SECURITY.md](https://github.com/IvanAnishchuk/cuere/blob/main/SECURITY.md) states private reporting via GitHub Security Advisories and an **initial response within one week**. |
| VM-02.01 | 1 | Security contacts in documentation | SECURITY.md, [`.well-known/security.txt`](https://github.com/IvanAnishchuk/cuere/blob/main/.well-known/security.txt) (RFC 9116), and `security-insights.yml` contacts. |
| VM-03.01 | 2 | Private vulnerability reporting to the security contacts | [GitHub Security Advisories](https://github.com/IvanAnishchuk/cuere/security/advisories/new) (private) plus the email contact in SECURITY.md. |
| VM-04.01 | 2 | Publicly publish data about discovered vulnerabilities | No vulnerabilities have been discovered to date; when one is, it will be published as a GitHub Security Advisory (the GHSA mechanism is enabled) and noted in the changelog. |

## Scanner results

The Privateer GitHub-repo scanner (`pvtr-github-repo-scanner`, catalog
`osps-baseline-2026-02`, applicability Levels 1–2) was run against the
repository. The scanner reads conformance largely from `security-insights.yml`,
so the **baseline run below predates committing that file** — most failures are
"not declared in Security Insights" artifacts that the committed
`security-insights.yml` resolves.

**Baseline run (before `security-insights.yml`)** — of the 42 in-scope Level 1/2
requirements: **22 passed, 4 needs-review, 11 failed, 5 not-evaluated** (checks
the scanner does not implement). All 11 failures and 4 needs-review were
information the Security Insights file now supplies (dependency policy, core
team/roles, vulnerability-reporting/CVD, security contacts, SLSA attestations,
user-guide and design-doc pointers, repository list).

**After-run (current `main`)** — **34 passed, 2 needs-review, 2 failed,
4 not-evaluated**. The scanner only assesses a repository's **default branch**,
so this reflects the merged work. The remaining non-passes are scanner
limitations or checks the scanner does not implement, not conformance gaps:

- **QA-03.01** *(failed — over-report)* — the scanner flags that not *every*
  executed status check is marked *required* (it names the **Benchmark**,
  **Build documentation**, and **Deploy to GitHub Pages** jobs, among others).
  Those are informational or deployment jobs that are non-blocking by design.
  cuere's genuine quality gates — tests, lint, the three type checkers, CodeQL,
  dependency audit, OSV scan, secret scan, dependency-review, and the Actions
  audit — *are* required status checks on `main`. The **DCO** check runs on every
  pull request but is not yet a *required* branch-protection context; closing
  that gap is tracked in
  [#89](https://github.com/IvanAnishchuk/cuere/issues/89).
- **AC-04.01** *(needs review — over-report)* — the scanner reported it could not
  read the repository's Actions configuration ("GitHub Actions is disabled …
  manual review required"). Actions is enabled and least-privilege permissions
  are enforced: every workflow declares a top-level `permissions: {}` and grants
  only the minimum each job needs, verifiable in
  [`.github/workflows/`](https://github.com/IvanAnishchuk/cuere/tree/main/.github/workflows)
  and audited by zizmor.
- **SA-01.01** *(needs review)* — the scanner looks for a design document in the
  repository root and asks for manual review when it only finds a `docs/`
  directory. The design documentation is [`docs/security/design.md`](design.md),
  referenced from `security-insights.yml`.
- **BR-05.01, SA-02.01, SA-03.01, VM-04.01** *(not evaluated)* — checks the
  scanner does not implement; met by the artifacts mapped in the table above
  (standardized `uv`/meson tooling, the API/CLI reference, the threat-model
  self-assessment, and the GitHub Security Advisories publication path).

The earlier after-run also failed **BR-03.02** because the
`vulnerability-reporting` distribution points listed the `pkg:pypi/cuere`
Package-URL, which the scanner's check rejects for lacking an `https` scheme;
the distribution points now use HTTPS URLs (the PyPI project page and the GitHub
releases page), which the scanner accepts.

## Maintaining conformance

- `security-insights.yml` carries `last-updated` / `last-reviewed` dates; review
  it whenever the security posture, contacts, or release process change.
- The supporting docs above are versioned with the code and updated by pull
  request like any other change.
- Level 3 conformance is tracked in
  [#84](https://github.com/IvanAnishchuk/cuere/issues/84) and
  [#85](https://github.com/IvanAnishchuk/cuere/issues/85).
