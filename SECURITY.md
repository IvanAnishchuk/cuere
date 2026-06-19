# Security Policy

## Supported Versions

Only the latest release receives security fixes.

## OSPS Baseline conformance

cuere conforms to **Level 2** of the
[OpenSSF OSPS Baseline](https://baseline.openssf.org/). The machine-readable
declaration is [`security-insights.yml`](https://github.com/IvanAnishchuk/cuere/blob/main/security-insights.yml)
(OpenSSF Security Insights v2.2.0) at the repository root; the control-by-control
record is in [docs/security/osps-baseline.md](https://ivananishchuk.github.io/cuere/security/osps-baseline/).

## Reporting a Vulnerability

Please report vulnerabilities privately via
[GitHub Security Advisories](https://github.com/IvanAnishchuk/cuere/security/advisories/new).
Do not open public issues for security problems.

You should receive an initial response within a week.

## Supply chain

- Releases are built in CI from tags via PyPI trusted publishing (OIDC) with
  PEP 740 attestations, sigstore signatures, SLSA provenance, and a CycloneDX
  SBOM attached to the GitHub release.
- Dependencies are locked (`uv.lock`), audited with pip-audit and
  OSV-Scanner, and updated via dependabot.

### Verifying a release

Download the wheel and its companion artifacts from the
[GitHub release](https://github.com/IvanAnishchuk/cuere/releases), then verify
any (or all) of the three independent attestations (replace `vX.Y.Z` with the
release tag):

```sh
# 1. GitHub build-provenance attestation (PEP 740)
gh attestation verify cuere-*.whl --repo IvanAnishchuk/cuere

# 2. sigstore keyless signature (uses the bundled *.sigstore.json)
uv tool run sigstore verify identity \
    --cert-identity 'https://github.com/IvanAnishchuk/cuere/.github/workflows/release.yml@refs/tags/vX.Y.Z' \
    --cert-oidc-issuer 'https://token.actions.githubusercontent.com' \
    --bundle cuere-*.whl.sigstore.json \
    cuere-*.whl

# 3. SLSA L3 provenance (slsa-verifier)
slsa-verifier verify-artifact cuere-*.whl \
    --provenance-path cuere-vX.Y.Z-provenance.intoto.jsonl \
    --source-uri github.com/IvanAnishchuk/cuere \
    --source-tag vX.Y.Z
```
