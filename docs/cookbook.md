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
