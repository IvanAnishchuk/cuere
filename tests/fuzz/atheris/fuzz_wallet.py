"""Atheris fuzz target for the cuere wallet-URI helpers.

Feeds arbitrary text to the URI classifier/optimizer and the payment-request
builders, asserting the optimizer's documented invariants and that the
case-significant ``ethereum:`` scheme is never rewritten. Mirrors the
properties in tests/test_wallet.py under libFuzzer coverage feedback; a builder
rejecting malformed input with WalletURIError is expected, but any *other*
exception is a finding.

    uv run --group fuzz python tests/fuzz/atheris/fuzz_wallet.py
"""

from harness import atheris, instrument, run

with instrument():
    from cuere import (
        SchemeCase,
        bitcoin_uri,
        erc20_transfer_uri,
        ethereum_uri,
        is_qr_alphanumeric,
        lightning_uri,
        optimize_uri,
        scheme_case,
    )
    from cuere.errors import WalletURIError


def _check_optimize(uri: str) -> None:
    """Assert optimize_uri's documented invariants for an arbitrary URI."""
    out = optimize_uri(uri)
    # The result is only ever the input or its uppercase, and is idempotent.
    assert out in (uri, uri.upper())
    assert optimize_uri(out) == out
    # A change implies an all-lowercase, case-insensitive scheme whose
    # uppercase is fully QR-alphanumeric (the only condition that shrinks a code).
    if out != uri:
        assert scheme_case(uri) is SchemeCase.INSENSITIVE
        assert uri == uri.lower()
        assert is_qr_alphanumeric(out)


def fuzz_target(data: bytes) -> None:
    """Fuzz the wallet-URI helpers and builders, asserting their documented invariants."""
    fdp = atheris.FuzzedDataProvider(data)
    choice = fdp.ConsumeIntInRange(0, 5)

    if choice == 0:
        _check_optimize(fdp.ConsumeUnicodeNoSurrogates(200))
    elif choice == 1:
        scheme_case(fdp.ConsumeUnicodeNoSurrogates(120))
        is_qr_alphanumeric(fdp.ConsumeUnicodeNoSurrogates(120))
    elif choice == 2:
        try:
            uri = bitcoin_uri(
                fdp.ConsumeUnicodeNoSurrogates(80),
                amount=fdp.ConsumeUnicodeNoSurrogates(40),
                label=fdp.ConsumeUnicodeNoSurrogates(40),
            )
        except WalletURIError:
            return
        _check_optimize(uri)
    elif choice == 3:
        try:
            uri = lightning_uri(fdp.ConsumeUnicodeNoSurrogates(120))
        except WalletURIError:
            return
        _check_optimize(uri)
    elif choice == 4:
        try:
            uri = ethereum_uri(
                fdp.ConsumeUnicodeNoSurrogates(80),
                value=fdp.ConsumeUnicodeNoSurrogates(40),
            )
        except WalletURIError:
            return
        # ethereum: is case-significant — optimize_uri must never touch it.
        assert optimize_uri(uri) == uri
    else:
        try:
            uri = erc20_transfer_uri(
                fdp.ConsumeUnicodeNoSurrogates(80),
                to=fdp.ConsumeUnicodeNoSurrogates(80),
                amount=fdp.ConsumeUnicodeNoSurrogates(40),
            )
        except WalletURIError:
            return
        assert optimize_uri(uri) == uri


run(fuzz_target)
