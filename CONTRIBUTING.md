# Contributing to Toolbox

## Environment setup

`toolbox` is a monorepo, with all dependencies managed as a uv workspace.

To install, create a virtual environment and sync dependencies:

```bash
cd toolbox # The root of the repo
uv venv
uv sync
```

### Pre-commit hooks

We use pre-commit hooks to ensure code quality and consistency. Install them with:

```bash
pre-commit install
```

To run them manually:

```bash
uv run pre-commit run --all-files
```

## Analytics

We use PostHog for anonymous CLI analytics (commands, errors, usage patterns).
Exclude yourself from analytics during development:

```bash
export TOOLBOX_TEST_USER="true"
```

Add this to your .zshrc or .bashrc to exclude yourself permanently.

### Dashboard Access

Contact developers to get invited to the PostHog workspace for viewing metrics and error tracking.
