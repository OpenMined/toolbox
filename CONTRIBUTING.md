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

## Adding a new package

To add a new package to the workspace, run from the root of the repo:

```
uv init --lib packages/<package_name>
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

## Release to PyPI

To bump the version, tag the commit, and publish to PyPI:

Since main is protected, create a release branch after bumping the version:

```bash
# Start from main
git checkout main
git pull origin main

# bump version, see https://docs.astral.sh/uv/guides/package/#updating-your-version
uv version --package syft_toolbox --bump minor
NEW_VERSION=$(uv version --package syft_toolbox --short)

# Create release branch with the new version
git checkout -b release/v${NEW_VERSION}
git commit -am "Release v${NEW_VERSION}"
git push -u origin release/v${NEW_VERSION}

# Create PR and merge to main
# After PR is merged, checkout main and create tag

git checkout main
git pull origin main
git tag "v${NEW_VERSION}"
git push origin "v${NEW_VERSION}"

# clean build dir, build and publish to PyPI
rm -rf dist/
uv build --package syft_toolbox
uv publish dist/syft-toolbox-* --token <your_token>
```

### Documentation Versioning

Documentation is automatically deployed via GitHub Actions when creating version tags.
If automatic deployment fails, you can manually deploy docs:

```bash
# Deploy a new version and update the latest alias
mike deploy --push --update-aliases ${NEW_VERSION} latest

# Set default version (only needed for first release)
mike set-default --push latest
```

## Documentation

To serve the docs locally, run this in the repo root:

```
mkdocs serve
```
