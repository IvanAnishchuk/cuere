# BIP-21 — `bitcoin:` payment-request URIs (summary)

A condensed reference for the part of [BIP-21] cuere implements in
[`bitcoin_uri`](../src/cuere/wallet.py). It is a summary, not the spec — read
the original for anything load-bearing.

[BIP-21]: https://github.com/bitcoin/bips/blob/master/bip-0021.mediawiki

## Grammar

```
bitcoinurn     = "bitcoin:" bitcoinaddress [ "?" bitcoinparams ]
bitcoinaddress = *base58 | bech32          ; the on-chain address
bitcoinparams  = bitcoinparam [ "&" bitcoinparams ]
bitcoinparam   = amountparam | labelparam | messageparam | otherparam
amountparam    = "amount=" *digit [ "." *digit ]
labelparam     = "label=" *pchar          ; percent-encoded
messageparam   = "message=" *pchar        ; percent-encoded
```

- **`amount`** is denominated in **BTC** (decimal), *not* satoshis — e.g.
  `amount=20.3` is 20.3 BTC. It is a plain decimal: no scientific notation, no
  thousands separators. One satoshi = `0.00000001` BTC, so the value is
  meaningful to at most 8 fractional digits.
- **`label`** / **`message`** are free-form human text and MUST be
  percent-encoded (RFC 3986). `label` names the payee/address; `message` is a
  note shown to the user.
- Keys are case-sensitive. Unknown `req-*` parameters a wallet does not
  understand must cause it to reject the URI; other unknown parameters are
  ignored.

## What cuere does

`bitcoin_uri(address, *, amount=None, label=None, message=None)`:

- Validates `address` **structurally** against the base58 + bech32 alphabet
  (`[0-9A-Za-z]+`). This is *not* a base58check / bech32 checksum verification —
  that would need the checksum algorithms cuere intentionally does not bundle.
- Renders `amount` (accepts `Decimal` / `int` / `str`, never `float` — binary
  floats cannot represent decimal money exactly) as a plain BTC decimal, and
  rejects non-finite, non-positive, or finer-than-one-satoshi (>8 fractional
  digit) values.
- Percent-encodes `label` / `message` with `quote(safe="")` (so spaces become
  `%20`, not `+`). A `None` parameter is omitted; an explicit empty string is
  kept as a present-but-empty value.
- Emits parameters in a fixed `amount` → `label` → `message` order for
  reproducible output.

Out of scope: `req-*` parameters, BIP-72 `r=` payment-protocol URLs, and any
checksum validation.

## Why `optimize_uri` only touches bech32, lowercase, no-query URIs

A QR code is smallest when its payload fits **alphanumeric** mode (digits,
upper-case A–Z and a few symbols). A bech32 address ([BIP-173]) is
case-insensitive, so a *fully lowercase* `bitcoin:bc1…` URI with **no query
string** can be uppercased wholesale to reach alphanumeric mode and shrink the
code — losslessly. [`optimize_uri`](../src/cuere/wallet.py) does exactly this
and only this:

- only the `bitcoin:` / `lightning:` schemes (known case-insensitive);
- only when the URI is already entirely lowercase (so uppercasing cannot
  destroy significant case);
- only when the uppercased form is fully QR-alphanumeric (a `?amount=…` query
  contains `?`/`&`/`=`, which are not alphanumeric, so any URI with parameters
  is returned unchanged).

It is deliberately **not** applied to case-significant schemes such as
`ethereum:` (EIP-55 checksums) — see [eip-681.md](eip-681.md).

[BIP-173]: https://github.com/bitcoin/bips/blob/master/bip-0173.mediawiki
