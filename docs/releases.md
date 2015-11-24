title: Releases
published: 2010-12-22

This explains how you can configure a Jazzband repository to be auto-released
on PyPI whenever create a Git tag and push it to GitHub.

### Packaging

First we need to make sure your Python package is able to automatically
deduct its version from Git tags, a feature that allows us to stop worrying
about having to update version identifiers in the `setup.py` file. It's
recommended to use the setuptools plugin [setuptools_scm] to do that.

All you need to do is to modify your `setup.py`:

```python
from setuptools import setup
# ...
setup(
	# ...
	use_scm_version=True,
	setup_requires=['setuptools_scm'],
	# ...
)
```

Please refer to the [setuptools_scm documentation][setuptools_scm] for more
information how it works.

In case you use [Sphinx] to document your project, use the following snippet
in your documentation's `conf.py`:

```python
from setuptools_scm import get_version
version = get_version()
```

[setuptools_scm]: https://pypi.python.org/pypi/setuptools_scm
[Sphinx]: http://sphinx-doc.org/

### Travis

Next you will want to follow Travis-CI’s documentation for how to do
[PyPI deployments](pypi-deploy).

[pypi-deploy]: https://docs.travis-ci.com/user/deployment/pypi/

In short:

- Install [Travis CI’s command line tool][travis-cli]
- Run `travis setup pypi` and:
	- use the username `jazzband` when it asks for one
	- leave the password *empty*
	- answer all other answers with “yes”
- [open an issue](https://github.com/jazzband/roadies/issues/new) for the
  roadies to add the encrypted password of the jazzband PyPI account to
  your project's `.travis.yml` with a pull request

When you’re ready to do a release to PyPI simply make sure to prepare all
the code you’d like just as before (e.g. update AUTHORS, CHANGELOG,
documentation), commit the changes and tag them with `git tag`.

### Versions

When tagging releases using Git you need to make sensible decisions about
which version number you use.

Jazzband follows the [semantic release versioning scheme][semver] in which
"semantic" means "correct for when a computer see it" -- not "nice to read
for a human". Don't hesitate to release 1.0. Or 2.0 or 41.0 for tat matter.
If you'd like to make statements about the importance of your releases,
chose a theme and attach a human readable release code name to your public
announcments.

No:

> Happy to announce that we just released Useful Software 1.4!

Yes:

> Happy to announce the "Cello" release (1.4) of our Useful Software!

[semver]: http://blog.versioneye.com/2014/01/16/semantic-versioning/
[travis-cli]: https://github.com/travis-ci/travis.rb#installation

Here's a quick primer for how to decide which version number
to use:

Given a version number `BREAKING.FEATURE.FIX` increment...

1. BREAKING when you make a backward-incompatible change to existing APIs
2. FEATURE when you add a new feature without breaking backward-compatibility
3. FIX when you fix a bug in a

[bff]: https://medium.com/javascript-scene/software-versions-are-broken-3d2dc0da0783
