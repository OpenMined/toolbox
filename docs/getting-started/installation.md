# Installation

## Requirements

Before installing Toolbox, ensure you have:

- **Python 3.12 or later**
- **[uv](https://docs.astral.sh/uv/getting-started/installation/)** - Fast Python package installer

## Install from PyPI

The recommended way to install Toolbox:

```bash
uv tool install --prerelease allow --python 3.12 -U syft-toolbox
```

Verify the installation:

```bash
tb info
```

## Install from Source

For development or latest features:

```bash
git clone https://github.com/OpenMined/toolbox.git
cd toolbox
uv pip install -e .
```

## Troubleshooting

### CLang Issues

If you encounter CLang errors during installation:

```bash
uv python install --reinstall
```

This [fixes Python in uv](https://github.com/astral-sh/python-build-standalone/pull/414).

### C++ Include Errors

If you see `#include <string>` errors:

```bash
CXXFLAGS="-isystem $(xcrun --show-sdk-path)/usr/include/c++/v1" uv pip install -e .
```

### Permission Issues

If you get permission errors, ensure you have write access to the uv tool directory. You may need to use `sudo` or adjust your PATH.

## Next Steps

After installation, proceed to the [Quick Start](quick-start.md) guide to install your first MCP server.
