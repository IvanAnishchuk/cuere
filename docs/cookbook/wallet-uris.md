# Wallet URI cookbook

Recipes for the crypto-wallet use case: turn a payment request or a pairing URI
into a QR code you can show in a terminal and scan with a phone wallet. For the
underlying URI formats see the [BIP-21](../bip-21.md),
[Lightning](../lightning-uri.md), and [EIP-681](../eip-681.md) summaries; for the
rendering model and CLI see the [README](../../README.md).

Each builder returns a plain `str`, so it composes with the rest of cuere —
[`optimize_uri`](../../src/cuere/wallet.py) to shrink the code and
[`show`](../../src/cuere/terminal.py) / [`render`](../../src/cuere/terminal.py) to
draw it. The codes below are the real `render` output: plain Unicode half-blocks,
the same shapes `show` prints to a terminal (a dark module is foreground ink, so
in a light-on-dark terminal you may want `--invert` for a scanner). The addresses
are valid, but some invoices and keys are shortened for a compact illustration.

## Why error-correction level L?

cuere encodes at QR **error-correction level L** (~7% recovery), the lowest of
the four levels, with `boost_error=False` — and that is deliberate, not a default
to "fix". A terminal is a clean, backlit, high-contrast surface that does not
smudge, fade, or pick up a coffee ring like a printed sticker, so the redundancy
that protects a *printed* code buys almost nothing on screen. Level L spends the
fewest modules on recovery, which means a **smaller code**: fewer modules per
side, larger on-screen modules, and an easier scan. If you export a code to print
it (see the [exporting recipe](exporting.md)), pass a stronger level explicitly —
`error="M"`, `"Q"`, or `"H"` — where physical wear actually matters.

## Bitcoin payment request (BIP-21)

[`bitcoin_uri`](../../src/cuere/wallet.py) builds a well-formed
[BIP-21](https://github.com/bitcoin/bips/blob/master/bip-0021.mediawiki)
`bitcoin:` URI: the address is validated, `amount` is rendered as a plain BTC
decimal, and `label` / `message` are percent-encoded.

```python
from decimal import Decimal

from cuere import bitcoin_uri, show

uri = bitcoin_uri(
    "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4",
    amount=Decimal("0.005"),
    label="Coffee",
    message="Order #1234",
)
# bitcoin:bc1q...?amount=0.005&label=Coffee&message=Order%20%231234

show(uri)   # draw it in the terminal
```

<!-- qr: BTC_FULL -->
```text
                                             
                                             
    █▀▀▀▀▀█ ▄█ ▄▄▄▀▄█▀▀▀█ █▀█▄▀▄█ █▀▀▀▀▀█    
    █ ███ █ ▄█▀█ ▄▄ ▀▄█ ▀▀█  ▄▄█  █ ███ █    
    █ ▀▀▀ █ ▄ █ ▀ ▄██▀ ▀▀█ ▀█▄█▄▀ █ ▀▀▀ █    
    ▀▀▀▀▀▀▀ ▀ ▀ █ ▀▄█ ▀▄▀▄█ ▀ ▀ ▀ ▀▀▀▀▀▀▀    
    ▀▀▀▀▀ ▀██▀▀ ▀▀▀ ▀ ▄▄▄ ▀▄ ▀▀ ██ █ █▄▀     
    █  ▀▀ ▀▄▀▀▄█▀ ███▀▀ ▀██▄▄ ▄▀▀▄█▄▀  █▀    
       ▀█▀▀█ ▄█▀█▀█▀▄█▄▄▄ ▀▄▄▀█▀▀▀▀▀▀▀█▀     
    █▄  ██▀  ▀▄ █▀ ▀█▀  ▄▄█▄▀▀ ▀ ██▄ █▀█▀    
     ▄▀ ▀█▀▄▄ ▀ █▀ ▀▄▀▄█▄▄█▄▀██▀█▀▀▄▀▄█ ▀    
     ▀██▀▀▀▄ ██ ▀ ██▀▀▄▄▄██ █ ▄██   ▄▀▀▀█    
    █▀█ ▀▄▀▀▀▀ ▄▄▀▄▀▄▀▄▄  ▀█▄▀▄▀▀█▀▀▀█▀█▀    
    ▀   ▀▄▀█▀ █▄▄▀ ▀▀▀▄ █▄▀▄▀  █▀ ▄  ▀▀██    
    █▄█▄▀█▀  █▀▄▄▀▄▀█▀▄▄▀▄█▄ ▀▀ ██▀▀▀█▀      
    █ ▄▀▀█▀▄ ▀ ▄█  ▀▀    █▀▄▄▀▄█▄▀██ ▄▀▀▀    
    ▀  ▀ ▀▀▀▄  ▄▄▀ ▀█▀▄▄▀ ▄█▀▀▄▀█▀▀▀█▄▀ ▀    
    █▀▀▀▀▀█ ▀ ▀ ▄ ███    ██▄  █▄█ ▀ █  ▀█    
    █ ███ █ █▄ ▄▄▀▄▀▄▀█▄▀▄▄▄▄██▀█████▄▀▀▀    
    █ ▀▀▀ █ █ ▄▄▄▀ ██▀▄▄▄█ ▄   ▄▄▄▄▄▄  ▀█    
    ▀▀▀▀▀▀▀ ▀▀   ▀   ▀ ▀     ▀▀   ▀▀  ▀▀▀    
                                             
                                             
```

`amount` is in **BTC** and accepts `Decimal`, `int`, or `str` — never `float`,
which can't represent decimal money exactly. It must be a finite, positive value
no finer than one satoshi (8 decimal places); anything else raises
[`WalletURIError`](../../src/cuere/errors.py):

```python
from cuere import WalletURIError

addr = "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4"

bitcoin_uri(addr, amount="0.00000001")   # ok: exactly one satoshi
bitcoin_uri(addr, amount="0.000000001")  # WalletURIError: sub-satoshi (9 dp)
bitcoin_uri("bad address!")              # WalletURIError: bad address
```

For the underlying format see the [BIP-21 summary](../bip-21.md).

## Lightning invoice (BOLT11 / LNURL / BOLT12)

[`lightning_uri`](../../src/cuere/wallet.py) wraps a bech32 Lightning payload — a
BOLT11 invoice (`lnbc…`), an LNURL (`lnurl1…`), or a BOLT12 offer (`lno1…`) — in a
`lightning:` URI. Like `bitcoin_uri` it validates the payload structurally
(ASCII-alphanumeric, a single case) but does not verify its checksum:

```python
from cuere import lightning_uri, show

uri = lightning_uri("lnbc1pvjluezpp5qqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqf")
# lightning:lnbc1pvjluez...

show(uri)   # draw it in the terminal
```

<!-- qr: LN -->
```text
                                         
                                         
    █▀▀▀▀▀█ ▀▀▀█▄███ ▀▄▄ ▀    █▀▀▀▀▀█    
    █ ███ █  ▀▄█ ▀█▄▄▄ ▀ █  ▀ █ ███ █    
    █ ▀▀▀ █  ▄▀█▀█▄▀▄▀▄▀▄██▄  █ ▀▀▀ █    
    ▀▀▀▀▀▀▀ █▄▀ █ █ ▀ ▀▄█ █ █ ▀▀▀▀▀▀▀    
    ██ █▀ ▀▄▄▀▄ ▀▀█▀██ █▀▄ ▄ ▄▀▄▄▄▄▄▀    
    ▄█▀  █▀█▀▀  ▀ ██ █▀▄█▀ █  ▀ ▄▀█▀▀    
     ▀▀  █▀█▄██ ▄▀▀██  ▀▀ ▄█▄ ▀  █ █     
     ▀█ ▀▄▀█▀█▄ ▄▄█▀▄ ▀▀█▀▀ █   ▄▄▄▄     
    ▀▀█▀▀ ▀▄▀█ █▀  █▀▄▄▄▄ █▀ ▀████ ▀█    
    ▀█ ▀  ▀ ▄██▄▀█▀█▀ ▀▀█ █▀██ ▀ ▄█ █    
    █    ▄▀█▀█▄▀▄█ ▄ █ ▄▀▄ ▄   █▄▄ ▀▀    
    █ ▀ ▀▀▀▀▀▄▄█▄█ █▀█▀▄▄▀ ▀█▀ █▀▀▄▀▀    
    ▀▀ ▀  ▀▀▄▄▄▀▀█▄█▄  ▀  ▄▄█▀▀▀██▄▄     
    █▀▀▀▀▀█  ▀ █▀▀ ▀▄ ▀▀█▀▀██ ▀ █▀▄▄▄    
    █ ███ █ ██ ▄▄▄██▀▄▀▄▄  ▀██▀▀▀▄ ▄▄    
    █ ▀▀▀ █ ▄█ ▀▄ ▄█▀▀ ▀█▀▄ ▀ ▄ ▀█▄██    
    ▀▀▀▀▀▀▀ ▀ ▀ ▀▀▀▀ ▀ ▀▀  ▀▀            
                                         
                                         
```

A `lightning:` URI is bech32 and so case-insensitive, just like a bare `bitcoin:`
address — pass a lowercase one through `optimize_uri` to uppercase it into QR
*alphanumeric* mode for a smaller, faster-to-scan code (see
[Shrinking codes](#shrinking-codes-optimize_uri--scheme_case) below). Lightning
*addresses* (`user@domain`) are **not** bech32 and are out of scope. For the
formats see the [Lightning summary](../lightning-uri.md).

## Ethereum payment request (EIP-681)

[`ethereum_uri`](../../src/cuere/wallet.py) builds an
[EIP-681](https://eips.ethereum.org/EIPS/eip-681) native-payment URI. The `value`
is in **wei** (1 ETH = 10¹⁸ wei) — cuere matches the spec rather than hiding a
unit conversion, so convert from ether yourself:

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

<!-- qr: ETH -->
```text
                                         
                                         
    █▀▀▀▀▀█ ▄█▀▀█▀█▄▄▄▄▀▄▀ ▀▄ █▀▀▀▀▀█    
    █ ███ █ ▄▀  ▀▄▀█▀▄▄▀ ▀▄ ▀ █ ███ █    
    █ ▀▀▀ █ ▄█▀▀█ ▀▄█▄ ▀▀▀ ▀█ █ ▀▀▀ █    
    ▀▀▀▀▀▀▀ ▀▄▀ █ █▄█ ▀ █▄▀▄▀ ▀▀▀▀▀▀▀    
    █▀█▀▀ ▀███ ▄▄▀▄▀█▀▄▄▀▄▄▄▄█▄█ ▀▄█▄    
    █▀ ▀█▀▀  █  █  █▄▀▀▄█▄█▄▀▄ ▄▄▄▄█     
    ▀▄▄█  ▀ ▀▀ ▄▄▀▄ ▄▀▀▄▀ ▄▄▀▄▄▄▀▄▄▀▄    
    █▀█▀ █▀▄▀▄▄ █  █▀   ▀█▄ ▀▀▄▀▀██▀     
    ▀▄ █▄ ▀▄█ ▄▄▄▀▄▀▄▀▄▄▄█▀▄▀▄▄▄▀█▄ █    
    ▄██ ▀▀▀▀ ██ █  ▀▄ ▄ █▄▄ ▄  █▀██▀     
    ██  ▀█▀ ▄ ▀▄▄▀▄▀█▀▀▄▄▄▀▄▄▄▄▀▀▄ █▄    
    █   ▄▀▀▄▀▀▄ █  ▀█▀▀▄▀██ ▄▄▀▀▀▀██     
    ▀  ▀▀▀▀ ▄▄▄▄▄▀▄ ▀▀▀▄▀ ▄ █▀▀▀█▀ ▀▄    
    █▀▀▀▀▀█ ▀   █  █▀   ██▄██ ▀ █ ▄█     
    █ ███ █ █▀▀▄▄▀▄▀▀█▀▄▄▄▄▄▀▀▀██▀▄▀▀    
    █ ▀▀▀ █ █ ▀ █  █  ▀▄▀▄  ▀█▀▄ ▄█▀     
    ▀▀▀▀▀▀▀ ▀▀▀  ▀ ▀      ▀▀▀▀ ▀▀▀ ▀     
                                         
                                         
```

The address case is significant — when mixed-case it carries the
[EIP-55](https://eips.ethereum.org/EIPS/eip-55) checksum — so an `ethereum:` URI
is **never** passed through `optimize_uri` (it would corrupt the checksum).
`value`, `gas_price`, and `gas_limit` are non-negative `uint256` integers;
invalid input raises `WalletURIError`.

## ERC-20 token transfer

[`erc20_transfer_uri`](../../src/cuere/wallet.py) builds the EIP-681
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

<!-- qr: ERC20 -->
```text
                                                 
                                                 
    █▀▀▀▀▀█ ▄▄▀██ ▀▄▀▀█ ██   ▄█▄▄▄▄▀▄ █▀▀▀▀▀█    
    █ ███ █ ▄▀█▀▄▄  █▄  ▀▀█▄▀▄ ▄▄▄▀▄▄ █ ███ █    
    █ ▀▀▀ █ ▄█ █ ▄▀▄ ▄█▀██▄▀█ ▀▄  █▀▄ █ ▀▀▀ █    
    ▀▀▀▀▀▀▀ ▀▄▀ ▀ █▄▀ █ █▄█ █ █ ▀ ▀▄▀ ▀▀▀▀▀▀▀    
    ██▀▀▀ ▀▀█▀▀▀▄▀▀▀▄█▀▄▄▄▀▄▄▀▀▀▄▀▄▄▀▀▄█▄▀▄▀▄    
    ▀ ▀▀▄▄▀▄▀▀▄██  █▀▀▄▄▄▄▀  ▀ ▀▄ ▀ ▀   █▄ ▀▄    
     █▄   ▀██▀ ▀▄▀▄▀▀▀ ▄█▄▄▄▄▀▀▀▀▀▄█▀▄▄▄▄▄██▄    
    ▀▄▀▀█▄▀  ▄  ▄▀▀█  ▄▄▄▄ ▄█ ▀▀▄▀▀▄▀█▀▀▄▀ ▄     
    █ █▀█▄▀ ▀ █▄ ▀▀▀▄▀▀▄▀ ▄▄▀▀▄▀▀▀▀▄▀▄ ▀▄█▀ ▄    
     ▀ ▄ ▄▀█▄ ▄ ▀  ▀  ▄  █▄▄█▀▄▀▀ ▄▄▄    █  ▄    
    ▀ ▀▄▀█▀█▄▄▀ ▀▀▄▀▀█▀▄ ▄▄▄▀▀▄▀▀▀▀▄▀▀▄▀▄▀▀▀▄    
     ██ ▄█▀▀ ▄▀█▀ ██▀ █▄ █ ▄█ ▄█▀▀▄ ▀▀  ▄▄       
    ▀█▀▀▄ ▀▄█▀▀█▀▀█▀█ ▄▄▀▄▀▄▄▀▄ ▀▀▀▄▀▀▄▀▄▀▀ ▄    
     ▀▄█▄ ▀▀ ▀▄ ▀  █▄▀█▄▄▄▄ ▄ ▀▀     ▄▄█▀▄▀      
    ▄ ▀▀ ▄▀ █▀█ ▄  ▀▀▀▀▄▀▄▀▄▀█▄▀▀▀▀█▀▀▄▀▄ █▄▄    
    █ █▄ █▀▀▄   ▄▀ ██ █ █▄▄▄▀ ▄▀▀▀█ ▄█ ██        
    ▀  ▀▀▀▀ ▄▀ ▄▀▀▄ █▀▀▄▀█▀▄▀▄▀▀▄▀▀▄█▀▀▀██▀█▄    
    █▀▀▀▀▀█ ▀▄▄ ▄  ▀█  ▄▀█▀ ▀  █ ▀▄▀█ ▀ ██ ▄▄    
    █ ███ █ █ ▄ ▀▄  ▀▀▀▄▀▄▄▄▀▀▀ ▀▀▀ █▀▀▀▀▀██     
    █ ▀▀▀ █ █ ██▀▀█▀▄ ▀  ██▄▀ ▀█  ▀ ▄▀▀██▄ █▀    
    ▀▀▀▀▀▀▀ ▀ ▀▀▀▀▀▀ ▀▀ ▀    ▀ ▀▀▀▀▀  ▀▀▀ ▀      
                                                 
                                                 
```

See the [EIP-681 summary](../eip-681.md) for the full grammar, the wei/base-unit
conventions, and the EIP-55 case-significance rule.

## WalletConnect pairing (`wc:`)

A WalletConnect `wc:` URI is the pairing handshake a dapp shows so a wallet can
connect to it. cuere has **no `walletconnect_uri()` builder, by design** — a `wc:`
URI is minted by the WalletConnect SDK during the handshake (it carries a
session-specific symmetric key), not something an application composes. cuere's
job is simply to *render the URI your client hands you* as a scannable QR:

```python
from cuere import scheme_case, show

# Straight from your WalletConnect client (topic and symKey shortened here):
pairing = "wc:c9e6f7a1@2?relay-protocol=irn&symKey=0123abcd"

show(pairing)             # render it exactly as issued
scheme_case(pairing)      # SchemeCase.SIGNIFICANT
```

<!-- qr: WC -->
```text
                                     
                                     
    █▀▀▀▀▀█ ▄█ ▄▄█ ███▀▀▀ █▀▀▀▀▀█    
    █ ███ █ ▄█▀█▄▄█▀▀▄ ▀▄ █ ███ █    
    █ ▀▀▀ █ ▄ █ █ ▄▄█  ▀▀ █ ▀▀▀ █    
    ▀▀▀▀▀▀▀ ▀ ▀ █ █▄▀ █ ▀ ▀▀▀▀▀▀▀    
    █▀▀▀█▄▀▀██▀ ███ ██▄▄█▀▄▀▄▀ █▄    
    ▀▄▄   ▀▄██▄ ▀ ▄▀▀▀  ██▄ █▀▀▄▄    
    ▄██ █▀▀██▀▄▄▀█▄▀█▀▄█ ▀▄▄█▀█▀█    
    ▄▀▄▀▀▀▀▀▄█▄▄▄ █▀▄▀▀ ▀ █▀██ ▀▄    
    ▄▄  ▀ ▀▀  ▀▄▀▀▄▀ █▄██ ▄▀▄▄▀█▄    
    █ ▀ █ ▀ ▀█▄▄█  ▀▄▀  ▀█▄▀█▀  ▄    
    ▀    ▀▀ ▄ ▀▄▀▀▄ ▄█▄ █▀▀▀██▀ ▄    
    █▀▀▀▀▀█ ▀▀  ▄ ▄▀  ▄██ ▀ █▄▀▄     
    █ ███ █ █▄▄▄▀▀▄▀██▀ ▀▀▀▀▀▄▀▀▄    
    █ ▀▀▀ █ █▀█▄▄▀ █▀  ▀█▀▀█▀ ▀█     
    ▀▀▀▀▀▀▀ ▀▀▀  ▀   ▀ ▀   ▀▀▀▀      
                                     
                                     
```

The `symKey` is case-sensitive and the pairing is one-shot, so the URI must be
encoded **byte-for-byte** as issued. That is exactly why
[`scheme_case`](../../src/cuere/wallet.py) classifies `wc:` as
`SchemeCase.SIGNIFICANT` and `optimize_uri` leaves it untouched (see below) —
case-folding it would break the connection. Real `wc:` topics and keys are
32-byte (64 hex-character) values from the SDK; they are shortened above only to
keep the illustration compact.

## Shrinking codes: `optimize_uri` & `scheme_case`

[`optimize_uri`](../../src/cuere/wallet.py) makes a code smaller when — and only
when — that is safe. QR codes have a compact *alphanumeric* mode that covers
digits, uppercase A–Z, and a few symbols. A bech32 address (`bitcoin:` /
`lightning:`) is case-insensitive, so uppercasing it loses nothing yet lets the
whole payload encode in alphanumeric mode, shaving modules off the result:

```python
from cuere import bitcoin_uri, optimize_uri, show

# A 62-character bech32 (taproot) address — long enough that switching to
# alphanumeric mode drops a whole QR version.
addr = "bc1p5cyxnuxmeuwuvkwfem96lqzszd02n6xdcjrs20cac6yqjjwudpxqkedrcr"
show(optimize_uri(bitcoin_uri(addr)))
# -> BITCOIN:BC1P...  (a smaller code than the lowercase original)
```

<!-- qr: BTC_OPT -->
```text
                                     
                                     
    █▀▀▀▀▀█ █  ▄▄▄█▄ ▀  ▀ █▀▀▀▀▀█    
    █ ███ █ ██▄ ▀█ ▀▄  ▄▀ █ ███ █    
    █ ▀▀▀ █ ▄██ ██▄ ▀▀ ▀▄ █ ▀▀▀ █    
    ▀▀▀▀▀▀▀ ▀ █▄▀▄▀▄▀ ▀ ▀ ▀▀▀▀▀▀▀    
    ▀█▄ ██▀▄▄ ▀ ▀▄█▄  █▀▄▄ ▀ ███▀    
    ▀▄▀█▄ ▀ ▀█▀▄█▀▄▄  █▄ ▀ █▀ █▀▀    
    ▄ █▄ ▀▀ █▄▄▀█ ▄  ▄█ ▀▀▀▄▀█▄ ▀    
    ▄▄█ █▄▀█▀▄▄▄ █ ▄ ██▀█▄▀ ▄▀▄▄▀    
    █▀█▄ ▄▀██▀█▀▀▄▀█▄ █▀▄ █ █▄ ▄▀    
      █▄▄▀▀ █▄█▄▄██▀▀█ ██ █ ▀█▄██    
    ▀▀  ▀▀▀▀█▀█▄█▀▄█▀ ▀██▀▀▀█▄  ▄    
    █▀▀▀▀▀█ ▄███▀▄▄▄██▀ █ ▀ █▀▀▀▀    
    █ ███ █ ▀▀██▄▀█▀▄ ▀ █▀▀█▀█▀ ▄    
    █ ▀▀▀ █ ▄▄▄ ▀█ ▀▄▀▄█▄▀ ▀█▄▄█▀    
    ▀▀▀▀▀▀▀ ▀▀     ▀▀▀▀  ▀  ▀▀▀      
                                     
                                     
```

In byte mode that lowercase address needs QR version 4 (a 41×21 half-block code);
uppercased into alphanumeric mode it drops to version 3 — the 37×19 code above,
the same payload in fewer modules. Once a URI carries a query string (an `amount`,
`label`, or `message`) it is no longer alphanumeric and `optimize_uri` returns it
unchanged, so passing *any* URI through it is always safe.

`optimize_uri` only ever uppercases a URI whose scheme is case-insensitive.
[`scheme_case`](../../src/cuere/wallet.py) exposes that decision as a typed
`SchemeCase`, so you can tell *why* a URI will or won't be optimized:

```python
from cuere import SchemeCase, scheme_case

scheme_case("bitcoin:bc1q...")     # SchemeCase.INSENSITIVE  -> optimize_uri may uppercase
scheme_case("lightning:lnbc1...")  # SchemeCase.INSENSITIVE
scheme_case("ethereum:0xAbC...")   # SchemeCase.SIGNIFICANT  -> EIP-55 case matters; left as-is
scheme_case("wc:topic@2?...")      # SchemeCase.SIGNIFICANT  -> WalletConnect key; left as-is
scheme_case("mailto:hi")           # SchemeCase.UNKNOWN      -> not recognized; left as-is
```

Only `SchemeCase.INSENSITIVE` URIs are candidates, and even those are returned
unchanged unless they are already lowercase with no query string. `ethereum:` and
`wc:` are recognized **explicitly** as case-significant rather than incidentally
passed through. See [lightning-uri.md](../lightning-uri.md) for the full scheme
model.
