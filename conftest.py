"""Make the in-tree ``src/`` importable without an installed package.

Normally cuere is installed editable (meson-python), but mutmut mutates a
*copy* under ``mutants/`` that the editable import hook would shadow. Running
mutation tests with the project uninstalled (`uv sync --no-install-project`)
plus this path insert means `import cuere` resolves to the (possibly mutated)
sibling ``src/`` tree. Harmless when the editable install is present.
"""

import sys
from pathlib import Path

_src = Path(__file__).resolve().parent / "src"
if _src.is_dir() and str(_src) not in sys.path:
    sys.path.insert(0, str(_src))
