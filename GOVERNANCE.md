# Governance

cuere is a small, single-maintainer open-source project. This document records
who holds which responsibilities, who has access to sensitive resources, and how
decisions are made — both so contributors know what to expect and to satisfy the
governance controls of the [OpenSSF OSPS Baseline](docs/security/osps-baseline.md).

## Roles and responsibilities

| Role | Who | Responsibilities |
|------|-----|------------------|
| **Maintainer** | Ivan Anishchuk ([@IvanAnishchuk](https://github.com/IvanAnishchuk)) | Sets direction; reviews and merges changes; cuts releases; owns security response; administers the repository, CI, and publishing. |
| **Contributor** | Anyone who opens an issue or pull request | Proposes changes and reports bugs under the [Code of Conduct](CODE_OF_CONDUCT.md) and [Contributing guide](CONTRIBUTING.md). |

cuere currently has **one maintainer**. There is no separate "core team" beyond
the maintainer; the table above is the complete member list.

## Members with access to sensitive resources

The following sensitive resources exist, and **only the maintainer** has access
to each. This list is the authoritative record for OSPS-GV-01.01.

| Resource | Access |
|----------|--------|
| GitHub repository administration (settings, branch protection, secrets) | Maintainer |
| Release publishing to PyPI | PyPI **trusted publishing (OIDC)** from the tagged release workflow — no long-lived API token; the maintainer controls the trusted-publisher configuration |
| GitHub Pages / documentation deploys | Maintainer (via CI) |
| Security advisory triage and private vulnerability reports | Maintainer |
| Commit/release signing keys | Held by the maintainer; never stored in the repository |

Access is granted at the **lowest privilege** necessary, and automated releases
use short-lived OIDC credentials rather than stored secrets.

## Decision-making

- Day-to-day changes are decided by the maintainer through ordinary pull-request
  review.
- Larger or breaking changes are discussed in the open first — as a GitHub
  **issue** (or the project board) — before implementation.
- The project is tracked on a public [GitHub Projects board](https://github.com/users/IvanAnishchuk/projects/4).

## Becoming a maintainer

cuere is open to growing its maintainer team. A sustained track record of
high-quality contributions — code or review — that follow the
[Contributing guide](CONTRIBUTING.md) and the project's quality bar (100% branch
coverage, three passing type checkers, signed and DCO-signed commits) is the
basis for an invitation. Reach out via an issue or the security contact in
[SECURITY.md](SECURITY.md) if you are interested.

## Code of conduct

Participation is governed by the [Code of Conduct](CODE_OF_CONDUCT.md). The
maintainer is responsible for enforcement.

## Changing this document

Governance changes are made by pull request to this file and take effect on
merge.
