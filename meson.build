# Build definition for cuere (pure-Python, built with meson-python).
#
# The project version below is the single source of truth: pyproject.toml
# declares `dynamic = ["version"]` and mesonpy reads it from here.
project(
    'cuere',
    version: '0.2.0',
    meson_version: '>= 1.5.0',
    license: 'CC0-1.0',
    license_files: 'LICENSE.md',
)

py = import('python').find_installation(pure: true)

subdir('src/cuere')
