# Security Policy

## Supported Versions

Only the latest release receives security fixes.

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
- Verify a wheel with:
  `gh attestation verify dist/cuere-*.whl --repo IvanAnishchuk/cuere`
