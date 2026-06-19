# Threat model & self-assessment

This is the maintainer self-assessment backing OSPS-SA-03.01: the most likely
and impactful security problems for cuere, and how the project mitigates them.
It builds on the [architecture & design](design.md) page. Last reviewed
2026-06-19.

## Scope and assets

cuere is a pure-Python library plus a thin CLI that renders QR codes for
terminals and exports them to SVG/PNG. The assets worth protecting are:

- **The published package** (`cuere` on PyPI) — the artifact users install.
- **The release supply chain** — the path from source to a signed PyPI release.
- **The user's terminal session** — the surface cuere writes to.

cuere holds no user data, makes no runtime network calls, and has no persistent
state, which keeps the threat surface small.

## Trust boundaries

The two boundaries that matter are **untrusted input entering the library** and
**rendered output leaving for the terminal/sink** (see
[design](design.md#trust-boundaries)).

## Threats and mitigations

| # | Threat | Assessment | Mitigation |
|---|--------|-----------|------------|
| T1 | **Terminal escape-sequence injection** via a crafted payload | Most relevant runtime risk for a terminal renderer | The payload is encoded into the QR matrix and **never echoed raw** to the terminal. The only escape sequences emitted are SGR colour codes in `ansi` mode, derived from the **validated** `dark`/`light` colour options, not from the payload. Colour inputs are resolved/validated and reject malformed values. |
| T2 | **Malicious or oversized payload** causing a crash or resource blow-up | Low — encoding is bounded | Encoding is delegated to segno, which enforces QR capacity limits and raises on data that does not fit; cuere surfaces these as typed `CuereError`s. No unbounded buffers are built from input. |
| T3 | **Dependency compromise** (segno, or the optional rich/typer/Pillow) | Medium — the usual OSS supply-chain risk | Runtime dependencies are deliberately minimal (segno only; the rest are optional extras). All are pinned in `uv.lock`, scanned by **OSV-Scanner** and **pip-audit**, reviewed on PRs by **dependency-review**, and updated via **dependabot**. See the [dependency policy](dependencies.md). |
| T4 | **Release/supply-chain tampering** (a malicious build or impersonated release) | High impact, low likelihood | Releases are built only in CI from tags, published to PyPI via **trusted publishing (OIDC)** with **PEP 740 attestations**, **sigstore** signatures, **SLSA** provenance, and a **CycloneDX SBOM**. Verification steps are in [SECURITY.md](https://github.com/IvanAnishchuk/cuere/blob/main/SECURITY.md#verifying-a-release). |
| T5 | **Source tampering / unauthorized commits** | Low | `main` is protected: pull requests with review, required status checks, **required signatures**, and no force-push/deletion. Commits are GPG/SSH-signed and DCO-signed. |
| T6 | **Secret leakage into version control** | Low | gitleaks runs in CI and as a pre-commit hook; GitHub secret scanning with **push protection** is enabled. cuere has no runtime secrets. |
| T7 | **CI/CD pipeline injection** (script injection, over-broad token scope) | Low | Workflows set a top-level `permissions: {}` with least-privilege job scopes, avoid `pull_request_target`, harden the runner, pin actions, and are audited by **zizmor** in CI and pre-commit. |

## Residual risk and assumptions

- cuere trusts segno and the optional extras to be correct; this is mitigated but
  not eliminated by pinning and auditing (T3).
- cuere trusts GitHub Actions and PyPI as platforms.
- A terminal emulator that misrenders standard Unicode block glyphs is out of
  scope; cuere emits spec-correct output and documents
  [scanning caveats](../colors.md).

No high-severity issues are open against this model. Suspected vulnerabilities
should be reported privately per [SECURITY.md](https://github.com/IvanAnishchuk/cuere/blob/main/SECURITY.md).
