# Releasing

Releases are automated by [.github/workflows/release.yml](../.github/workflows/release.yml).
Pushing a version tag runs the full pipeline:

```
check-version -> test matrix (3.11-3.13) -> build -> TestPyPI -> PyPI -> GitHub Release
```

Publishing uses [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/)
(OIDC), so no API tokens or GitHub secrets are involved.

## Cutting a release

1. Bump `__version__` in `asyncio_channel/__init__.py` and commit to `main`.
2. Tag and push:

   ```sh
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```

3. Watch the *Release* workflow under the repo's *Actions* tab. It will:
   - fail fast if the tag does not match `__version__`,
   - run the full test matrix,
   - build and validate the sdist and wheel,
   - upload to TestPyPI, then PyPI,
   - create a GitHub Release with auto-generated notes and the dist
     files attached.

If a late stage fails, fix the cause and re-run the failed jobs from the
Actions UI — the TestPyPI upload uses `skip-existing`, so re-runs do not
fail on already-uploaded files. PyPI versions are immutable: if the
published files themselves are broken, bump the version and release
again.

