"""Type-level regression tests for the public API.

`assert_type` is a no-op at runtime but is verified by mypy / ty / basedpyright,
so these pin the inferred types of the public surface against accidental drift.
"""

import io
from typing import assert_type

from cuere import (
    QRMatrix,
    SchemeCase,
    fits,
    is_qr_alphanumeric,
    lightning_uri,
    optimize_uri,
    render,
    scheme_case,
    show,
)
from cuere.render import render_height, render_matrix, render_width


def test_public_api_return_types() -> None:
    # assert_type is a no-op at runtime; bind its passthrough result to `_` to
    # satisfy basedpyright's reportUnusedCallResult (house style for unused
    # call results — see e.g. `_ = stream.write(...)` in terminal.py).
    matrix = QRMatrix.encode("HI")
    _ = assert_type(matrix, QRMatrix)
    _ = assert_type(matrix.size, int)
    _ = assert_type(matrix.modules, tuple[tuple[bool, ...], ...])
    _ = assert_type(matrix.inverted(), QRMatrix)

    _ = assert_type(render("HI"), str)
    _ = assert_type(render(matrix), str)
    _ = assert_type(render_matrix(matrix), str)
    _ = assert_type(render_width(matrix), int)
    _ = assert_type(render_height(matrix), int)

    # `show` returns None: call it bare (don't bind/assert the result) so the
    # call's signature is still type-checked without tripping CodeQL's
    # py/use-of-return-value on an intentionally-None value. Its None return and
    # behavior are covered in test_terminal.py.
    show("HI", out=io.StringIO(), width=80)
    _ = assert_type(fits("HI", width=80), bool)

    _ = assert_type(optimize_uri("bitcoin:bc1q"), str)
    _ = assert_type(is_qr_alphanumeric("HI"), bool)
    _ = assert_type(lightning_uri("lnbc1abc"), str)
    _ = assert_type(scheme_case("bitcoin:bc1q"), SchemeCase)
