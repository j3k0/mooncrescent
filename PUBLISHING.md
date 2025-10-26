# Publishing to PyPI

This guide explains how to publish Mooncrescent to PyPI.

## Prerequisites

1. Install build and publishing tools:
```bash
pip install build twine
```

2. Create accounts on:
   - [PyPI](https://pypi.org/account/register/) (production)
   - [TestPyPI](https://test.pypi.org/account/register/) (testing)

## Build the Package

Clean old builds and create new distribution files:

```bash
# Clean old builds
rm -rf build/ dist/ *.egg-info

# Build the package
python -m build
```

This creates two files in `dist/`:
- `mooncrescent-X.Y.Z.tar.gz` (source distribution)
- `mooncrescent-X.Y.Z-py3-none-any.whl` (wheel)

## Test on TestPyPI (Optional but Recommended)

Upload to TestPyPI first to verify everything works:

```bash
# Upload to TestPyPI
python -m twine upload --repository testpypi dist/*

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ mooncrescent
```

## Publish to PyPI

Once you've verified everything works:

```bash
# Upload to production PyPI
python -m twine upload dist/*
```

You'll be prompted for your PyPI username and password.

## Using API Tokens (Recommended)

Instead of using your password, use API tokens:

1. Go to PyPI → Account Settings → API tokens
2. Create a new token (scope: entire account or just this project)
3. Use the token as your password with username `__token__`

Or configure it in `~/.pypirc`:

```ini
[pypi]
username = __token__
password = pypi-YOUR_TOKEN_HERE

[testpypi]
username = __token__
password = pypi-YOUR_TOKEN_HERE
```

## Version Bumping

Before publishing a new version:

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md` with changes
3. Commit the changes:
```bash
git add pyproject.toml CHANGELOG.md
git commit -m "Bump version to X.Y.Z"
git tag vX.Y.Z
git push && git push --tags
```

## Verify Publication

After uploading:

1. Check the package page: https://pypi.org/project/mooncrescent/
2. Test installation:
```bash
pip install mooncrescent
mooncrescent --help
```

## Common Issues

### Wrong version already exists
- You cannot replace an existing version on PyPI
- Increment the version number and try again

### Missing README on PyPI page
- Ensure `README.md` is included in `MANIFEST.in`
- Check that `readme = "README.md"` is in `pyproject.toml`

### Import errors after installation
- Verify package structure with: `python -m zipfile -l dist/*.whl`
- Check that all Python files are in the `mooncrescent/` directory
- Ensure `__init__.py` exists

## Automation (Future)

Consider setting up GitHub Actions to automate:
- Build on every commit
- Publish to TestPyPI on tags matching `v*-rc*`
- Publish to PyPI on tags matching `v*`

