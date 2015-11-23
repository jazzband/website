title: Releases
published: 2010-12-22

### Setting up automatic releases to PyPI

For Jazzband members who are so inclined to automatically release Python packages to PyPI via Travis-CI here’s the step by step guide to do that.

Use [setuptools_scm](https://pypi.python.org/pypi/setuptools_scm) in your `setup.py` to automatically build a version number from the Git repository.

To do that update it to contain the following:

```python
from setuptools import setup
setup(
	...,
	use_scm_version=True,
	setup_requires=['setuptools_scm'],
	...,
)
```

### Travis

Then follow Travis-CI’s documentation for how to do [PyPI deployment](pypi-deploy).

[pypi-deploy]: https://docs.travis-ci.com/user/deployment/pypi/

In short:

- install [Travis CI’s command line tool]
- run `travis setup pypi` and:
	- use the username “jazzband” when it asks
	- leave the password *empty*
	- answer all other answers with “yes”
- [open an issue](https://github.com/jazzband/roadies/issues/new) for the roadies to add the encrypted password of the jazzband PyPI account

When you’re ready to do a release to PyPI simply make sure to prepare all the code you’d like just as before (e.g. update AUTHORS, CHANGELOG, documentation), commit the changes and tag them with `git tag`. Please follow [semantic release versioning][semver] when deciding on a version number.

[semver]: http://blog.versioneye.com/2014/01/16/semantic-versioning/

Here’s a quick summary how it works:

> Given a version number MAJOR.MINOR.PATCH, increment the:
> 1. MAJOR version when you make incompatible API changes,
  2. MINOR version when you add functionality in a backwards-compatible manner, and
  3. PATCH version when you make backwards-compatible bug fixes.

Alternatively you can remember the pattern like this:

> [BREAKING.FEATURE.FIX][bff]

[bff]: https://medium.com/javascript-scene/software-versions-are-broken-3d2dc0da0783
