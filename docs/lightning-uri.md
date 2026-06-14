# `lightning:` URIs and the `optimize_uri` scheme model (summary)

A condensed reference for the part of the Lightning ecosystem cuere implements
in [`lightning_uri`](../src/cuere/wallet.py), plus the typed scheme model
(`SchemeCase` / `scheme_case`) that decides what [`optimize_uri`] may touch. It
is a summary, not the specs — read the originals for anything load-bearing.

## What rides on a `lightning:` URI

A `lightning:` URI carries a single **bech32** ([BIP-173]) payload whose
human-readable part begins `ln`:

- a **BOLT11** payment invoice — `lnbc…` (mainnet), `lntb…` (testnet),
  `lntbs…` (signet), `lnbcrt…` (regtest) ([BOLT #11]);
- an **LNURL** — `lnurl1…`, a bech32-wrapped HTTPS URL ([LNURL specs]);
- a **BOLT12** offer — `lno1…` ([BOLT #12]).

All three are bech32, so they share its key property for QR: the alphabet is a
subset of ASCII alphanumerics and **case is not significant** — but a bech32
string must be *all* lower- or *all* upper-case, **never mixed** (mixed case is
a decoding error per BIP-173).

## What cuere does

`lightning_uri(payload)`:

- Validates `payload` **structurally**: it must be `ln…`/`LN…` followed by
  bech32 characters, all one case, with no `:` / `@` / query character or
  whitespace. This is *not* a bech32 checksum verification — that needs the
  bech32 polynomial cuere intentionally does not bundle (mirroring how
  `bitcoin_uri` does not run base58check).
- Returns the bare `lightning:<payload>` URI verbatim (case preserved). An
  all-uppercase payload is already QR-alphanumeric; a lowercase one becomes so
  via [`optimize_uri`].
- Raises [`WalletURIError`](../src/cuere/errors.py) on an empty, mixed-case, or
  otherwise non-conforming payload.

Out of scope: lightning *addresses* (`user@domain`, which are not bech32 and not
case-insensitive), the `lightning=` BIP-21 unified-QR parameter, and any
checksum or network validation.

## The scheme model: `SchemeCase` / `scheme_case`

`optimize_uri` may uppercase a URI to reach QR **alphanumeric** mode only when
doing so is provably lossless. Whether a scheme qualifies is classified by
[`scheme_case`](../src/cuere/wallet.py), which returns a `SchemeCase`:

| `SchemeCase`  | Meaning                                            | Schemes                       | `optimize_uri` |
| ------------- | -------------------------------------------------- | ----------------------------- | -------------- |
| `INSENSITIVE` | bech32 payload — case carries no meaning           | `bitcoin:`, `lightning:`      | may uppercase  |
| `SIGNIFICANT` | cuere knows the case matters — folding corrupts it | `ethereum:`, `wc:`            | never touched  |
| `UNKNOWN`     | unrecognized scheme / no scheme at all             | everything else               | never touched  |

`optimize_uri` folds a URI only when **all** of these hold: its scheme is
`INSENSITIVE`, the URI is already entirely lowercase, and the uppercased form is
fully QR-alphanumeric (a `?…` query contains `?`/`&`/`=`, which are not
alphanumeric, so any URI with parameters is returned unchanged).

### Why `wc:` (WalletConnect) is `SIGNIFICANT`, not `UNKNOWN`

A [WalletConnect] URI — `wc:<topic>@<version>?relay-protocol=irn&symKey=…`
(v2), or `wc:<topic>@<version>?bridge=<url>&key=…` (v1) — must be encoded
**exactly as issued**: it is a one-shot pairing handshake. Its `relay-protocol`
identifier is case-significant, its v1 `bridge` is a percent-encoded URL (also
case-significant), and the `@`/`?`/`&`/`=` punctuation is not QR-alphanumeric
anyway. cuere therefore recognizes `wc:` **explicitly** as case-significant and
leaves it untouched — distinct from an unknown scheme, so the intent is pinned
rather than incidental. `ethereum:` is `SIGNIFICANT` for the same family of
reasons (EIP-55 checksum case — see [eip-681.md](eip-681.md)).

[`optimize_uri`]: ../src/cuere/wallet.py
[BIP-173]: https://github.com/bitcoin/bips/blob/master/bip-0173.mediawiki
[BOLT #11]: https://github.com/lightning/bolts/blob/master/11-payment-encoding.md
[BOLT #12]: https://github.com/lightning/bolts/blob/master/12-offer-encoding.md
[LNURL specs]: https://github.com/lnurl/luds
[WalletConnect]: https://specs.walletconnect.com/
