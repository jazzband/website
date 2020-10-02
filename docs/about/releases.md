title: Releases

Releasing packages to the [Python Package Index][PyPI] can be partially
automated for Jazzband projects. To achieve this, we require new or
transfered projects to add the `jazzband` PyPI user as a maintainer role
on [PyPI].

Once that's done, the [roadies] are able to set up the recommended
continuous testing solution [Travis CI] to automatically do releases
to a private and secure package index where Jazzband members can
review the uploaded files and release them to [PyPI] on their own.

### Security

For security reasons we can't grant the ability to release to [PyPI]
to all Jazzband members but only to those who have shown significant
contributions to the projects in question. All other Jazzband features
(as of writing this) continue to be open to all Jazzband members.

To become a project lead, please also
[open a project lead issue](/roadies/issue).

In case no project lead(s) can be found for a project the [roadies]
will act as surrogate leads and can be contacted to request a PyPI
release on the behalf of the Jazzband members. Please
[open a PyPI Release ticket](/roadies/issue) for that.

!!! note "Why are there project leads?"

	While we strongly favor the idea of providing full access to
	the Jazzband projects to all members, we need to counter-balance
	security requirements with our open development process.

	Otherwise a bad actor may be able to make releases that are not
	in line with our [Code of Conduct] or -- even worse -- contain
	malicious code.

	We sincerely hope that the Jazzband members accept that
	trade-off. We are committed to unrestricted members.
	We're all part of this.

In the following paragraphs we'll explain how you can configure a
Jazzband project to be semi-automatically released to PyPI whenever
a new Git tag is pushed to its repository.

[PyPI]: https://pypi.org/
[Travis CI]: https://travis-ci.org/
[roadies]: /roadies
[Code of Conduct]: /about/conduct

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
[setuptools_scm]: https://pypi.org/project/setuptools_scm/

### Continuous Integration  

Next you will want to set up the project to use Travis CI for
continous testing. Please refer to the [Python specific
documentation][travis-python] for how to accomplish that.

In addition we strongly recommend using [tox-travis] if the
project is using [tox] (which is also recommended).

[travis-python]: https://docs.travis-ci.com/user/languages/python/
[tox-travis]: https://tox-travis.readthedocs.io/
[tox]: https://tox.readthedocs.io/

Steps needed:

- Set up the `.travis.yml` file following the  [Travis CI docs][travis-python].
- Create a `tox.ini` which takes [tox-travis] into account.
- [Open a PyPI Release issue](/roadies/issue) for the
  roadies to enable the auto-release mechanism via the Jazzband.

If you need a project release and you are not a project lead, you
should create a pull request named:
`Prepare release of <project> <version>`
and make sure that everything is ready for the release
(e.g. update AUTHORS, CHANGELOG, documentation, etc.),
to makes it easy for a project lead to review and release.

If you are a project lead, when you are ready to do a release to PyPI
simply make sure that everything is ready for the release you’d like
(e.g. update `AUTHORS`, `CHANGELOG`, documentation, etc.), merge the
release pull-request, tag it with `git tag` and push the code to
GitHub with `git push --tags`. Aternatively, you can use the GitHub UI
to create a GitHub release that will create the tag for you.

If all goes according to plan, Travis CI will run the test suite for the
pushed tag, create release files, uploads it to the Jazzband site, for
the lead members or roadies to review. They will be able to confirm the
uploads and release them to PyPI individually.

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
