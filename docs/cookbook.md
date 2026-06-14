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
