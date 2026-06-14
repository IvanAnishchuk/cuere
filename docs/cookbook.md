# cuere cookbook

Task-oriented recipes for common jobs. For the full API see the docstrings;
for the rendering model and CLI see the [README](../README.md).

## Show a Bitcoin payment request (BIP-21)

[`bitcoin_uri`](../src/cuere/wallet.py) builds a well-formed
[BIP-21](https://github.com/bitcoin/bips/blob/master/bip-0021.mediawiki)
`bitcoin:` URI: the address is validated, `amount` is rendered as a plain BTC
decimal, and `label` / `message` are percent-encoded. It returns a plain `str`,
so it composes with the rest of cuere — `optimize_uri` to shrink the code and
`show` / `render` to draw it.

```python
from decimal import Decimal

from cuere import bitcoin_uri, optimize_uri, show

uri = bitcoin_uri(
    "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4",
    amount=Decimal("0.005"),
    label="Coffee",
    message="Order #1234",
)
# bitcoin:bc1q...?amount=0.005&label=Coffee&message=Order%20%231234

show(optimize_uri(uri))   # draw it in the terminal
```

`amount` is in **BTC** and accepts `Decimal`, `int`, or `str` — never `float`,
which can't represent decimal money exactly. It must be a finite, positive value
no finer than one satoshi (8 decimal places); anything else raises
`WalletURIError`:

```python
from cuere import WalletURIError

bitcoin_uri("bc1q...", amount=Decimal("0.005"))   # ok
bitcoin_uri("bc1q...", amount="0.00000001")        # ok: exactly one satoshi
bitcoin_uri("bc1q...", amount="0.000000001")       # WalletURIError: sub-satoshi
bitcoin_uri("bad address!")                          # WalletURIError: bad address
```

### Why `optimize_uri`?

A bare `bitcoin:`/`lightning:` address (no `?amount=...` query) is bech32, which
is case-insensitive, so `optimize_uri` uppercases it to reach QR *alphanumeric*
mode and produce a noticeably smaller code:

```python
from cuere import bitcoin_uri, optimize_uri, show

show(optimize_uri(bitcoin_uri("bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4")))
# -> BITCOIN:BC1Q...  (smaller QR)
```

Once a URI carries a query string (an `amount`, `label`, or `message`), it is no
longer QR-alphanumeric and `optimize_uri` returns it unchanged — passing it
through is always safe.

For the underlying format see the [BIP-21 summary](bip-21.md).

## Show a Lightning invoice (BOLT11 / LNURL)

[`lightning_uri`](../src/cuere/wallet.py) wraps a bech32 Lightning payload — a
BOLT11 invoice (`lnbc…`), an LNURL (`lnurl1…`), or a BOLT12 offer (`lno1…`) — in
a `lightning:` URI. Like `bitcoin_uri` it validates the payload structurally (the
bech32 alphabet, never mixed-case) but does not verify its checksum:

```python
from cuere import lightning_uri, optimize_uri, show

uri = lightning_uri("lnbc1pvjluezpp5qqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqf...")
# lightning:lnbc1pvjluez...

show(optimize_uri(uri))   # BOLT11 is bech32, so optimize_uri shrinks the code
```

A `lightning:` URI is bech32 and case-insensitive (just like a bare `bitcoin:`
address), so `optimize_uri` uppercases a lowercase one to reach QR *alphanumeric*
mode for a smaller, faster-to-scan code. Lightning *addresses* (`user@domain`)
are **not** bech32 and are out of scope.

## Which URIs does `optimize_uri` shrink? (`scheme_case`)

`optimize_uri` only ever uppercases a URI whose scheme is case-insensitive.
[`scheme_case`](../src/cuere/wallet.py) exposes that classification as a typed
`SchemeCase`, so you can tell *why* a URI will or won't be optimized:

```python
from cuere import SchemeCase, scheme_case

scheme_case("bitcoin:bc1q...")     # SchemeCase.INSENSITIVE  -> optimize_uri may uppercase
scheme_case("lightning:lnbc1...")  # SchemeCase.INSENSITIVE
scheme_case("ethereum:0xAbC...")   # SchemeCase.SIGNIFICANT  -> EIP-55 case matters; left as-is
scheme_case("wc:topic@2?...")      # SchemeCase.SIGNIFICANT  -> WalletConnect; left as-is
scheme_case("mailto:hi")           # SchemeCase.UNKNOWN      -> not recognized; left as-is
```

Only `SchemeCase.INSENSITIVE` URIs are candidates; `optimize_uri` still returns
them unchanged unless they are also already lowercase and have no query string.
WalletConnect (`wc:`) is recognized **explicitly** as case-significant — it is a
one-shot pairing handshake that must be encoded exactly as issued. See
[lightning-uri.md](lightning-uri.md) for the full scheme model.

## Show an Ethereum payment request (EIP-681)

[`ethereum_uri`](../src/cuere/wallet.py) builds an
[EIP-681](https://eips.ethereum.org/EIPS/eip-681) native-payment URI. The
`value` is in **wei** (1 ETH = 10¹⁸ wei) — cuere matches the spec rather than
hiding a unit conversion, so convert from ether yourself:

```python
from cuere import ethereum_uri, show

ONE_ETH = 10**18
uri = ethereum_uri(
    "0xfb6916095ca1df60bb79Ce92ce3ea74c37c5d359",
    value=ONE_ETH // 100,   # 0.01 ETH, expressed in wei
    chain_id=1,             # EIP-155 mainnet
)
# ethereum:0xfb69...d359@1?value=10000000000000000

show(uri)   # draw it in the terminal
```

The address case is significant — when mixed-case it carries the
[EIP-55](https://eips.ethereum.org/EIPS/eip-55) checksum — so an `ethereum:` URI
is **never** passed through `optimize_uri` (it would corrupt the checksum).
`value`, `gas_price`, and `gas_limit` are non-negative `uint256` integers;
invalid input raises `WalletURIError`.

## Request an ERC-20 token transfer

[`erc20_transfer_uri`](../src/cuere/wallet.py) builds the EIP-681
`transfer(address,uint256)` form. `amount` is in the token's **base units** (its
own `decimals`, which the library can't know — so apply any scaling yourself):

```python
from cuere import erc20_transfer_uri, show

# 1 USDC (6 decimals) to the recipient, on Ethereum mainnet.
uri = erc20_transfer_uri(
    "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC contract
    to="0x8e23ee67d1332ad560396262c48ffbb01f93d052",
    amount=1_000_000,                               # 1 USDC = 10**6 base units
    chain_id=1,
)
# ethereum:0xA0b8...eB48@1/transfer?address=0x8e23...d052&uint256=1000000

show(uri)
```

See the [EIP-681 summary](eip-681.md) for the full grammar, the wei/base-unit
conventions, and the EIP-55 case-significance rule.

## Save a QR code to a file (SVG, PNG)

[`save`](../src/cuere/output.py) renders any payload to a file. The format is
taken from the path suffix (`.svg`, `.png`, `.txt`), so the common case needs no
extra arguments:

```python
from cuere import save

save("bitcoin:BC1Q...", "invoice.svg")            # vector, infinite resolution
save("bitcoin:BC1Q...", "invoice.png", scale=8)   # 8 pixels per module
```

`scale` is pixels-per-module for the image formats (SVG scales its `width` /
`height`; PNG is a raster grid). For full control over the destination, pass an
explicit `format` (overriding the suffix) or write to an open binary stream:

```python
from io import BytesIO
from cuere import save

save("HELLO", "code.dat", format="svg")   # suffix says nothing; be explicit
buffer = BytesIO()
save("HELLO", buffer, format="png")       # a stream always needs format=
```

Need the bytes without touching the filesystem (to attach, upload, or embed)?
[`render_bytes`](../src/cuere/output.py) returns them directly:

```python
from cuere import render_bytes

svg = render_bytes("HELLO", format="svg")            # -> bytes (UTF-8 SVG)
png = render_bytes("HELLO", format="png", scale=10)  # -> bytes (PNG image)
```

All the encoding knobs (`error`, `border`, `micro`, `boost_error`) and `invert`
work here too, exactly as in `render` / `show`.

### PNG needs the `cuere[image]` extra

PNG output uses [Pillow](https://python-pillow.org/), which is an optional
dependency to keep the base install lightweight — text and SVG export need
nothing extra. Install it with:

```bash
pip install 'cuere[image]'   # or: uv add 'cuere[image]'
```

Without it, PNG raises a clear `MissingDependencyError` (a `CuereError`); an
unrecognized format name raises `UnknownFormatError`:

```python
from cuere import MissingDependencyError, UnknownFormatError, render_bytes

try:
    render_bytes("HELLO", format="png")     # MissingDependencyError if Pillow absent
    render_bytes("HELLO", format="jpeg")    # UnknownFormatError: not a known format
except (MissingDependencyError, UnknownFormatError) as exc:
    print(exc)
```

From the CLI, the same lives behind `--output FORMAT[:PATH]` (and `--scale`);
`PATH` of `-` or omitted writes to stdout, and omitting `--output` keeps the
default terminal rendering. See [output formats](output-formats.md) for the full
model.
