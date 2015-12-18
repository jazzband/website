title: Releases
published: 2010-12-22

This explains how you can configure a Jazzband repository to be
auto-released on PyPI whenever you create a Git tag and push it to GitHub.

### Packaging

Since we're currently aiming at Python projects primarily please
make sure your project is able to be packaged as a Python package
on PyPI. There is a great and extensive documentation in the
[Python Packaging Guide][PyPUG] that should allow you to prepare
your project accordingly.

We recommend using [setuptools_scm] for automatically deducing
the version of the project package from Git -- but setting the
version manually in the `setup.py` works just the same.

[PyPUG]: https://packaging.python.org/en/latest/
[setuptools_scm]: https://pypi.python.org/pypi/setuptools_scm

### Travis

Next you will want to follow Travis-CI’s documentation for how to do
[PyPI deployments][pypi-deploy].

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
documentation), commit the changes, tag them with `git tag` and push
the code to GitHub with `git push --tags`. If all goes according to plan
you'll see the release show up on PyPI automatically.

### Versions and code names

When tagging releases using Git you need to make sensible decisions about
which version number you use.

Jazzband follows the [semantic release versioning scheme][semver] in which
"semantic" means "correct for when a computer sees it" -- not "nice to read
for a human". Don't hesitate to release `1.0`, or `2.0` or `41.5.12` for
that matter. Do a `1.0` release as soon as your project is used in a real
world application.

If you'd like to make statements about the importance of your releases
attach a human readable release code name to your public announcments.
Choose a theme that will allow you to pick one for every release, e.g.
cat names. Or city names. Tree names. Color names. Anything that has lots
of names.

No:

> Happy to announce that we just released Useful Software 1.4!

Yes:

> Happy to announce the "Cello" release (1.4) of our Useful Software!

[semver]: http://blog.versioneye.com/2014/01/16/semantic-versioning/
[travis-cli]: https://github.com/travis-ci/travis.rb#installation

!!! note "How to decide for the version number?"

	Given a version number `BREAKING.FEATURE.FIX` increment...

	1. `BREAKING` when you make a backward-incompatible change to existing APIs
	2. `FEATURE` when you add a new feature without breaking backward-compatibility
	3. `FIX` when you fix a bug in an existing feature
