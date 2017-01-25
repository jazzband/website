title: Releases

Releasing packages to the [Python Package Index][PyPI] can be partially
automated for Jazzband projects. To achieve this, we require new or
transfered projects to add the `jazzband` PyPI user as a maintainer role
on [PyPI].

Once that's done, the [roadies] are able to set up the recommended
continuous testing solution [Travis-CI] to automatically do releases
to a private and secure package index where Jazzband members can
review the uploaded files and release them to [PyPI] on their own.

### Security

For security reasons we can't grant the ability to release to [PyPI]
to all Jazzband members but only to those who have shown significant
contributions to the projects in question. All other Jazzband features
(as of writing this) continue to be open to all Jazzband members.

To become a "lead" project member, please also [open an issue with the
"lead" label](/roadies/issue?labels=lead).

In case no such "lead" project member(s) can be found for an individual
project the [roadies] will act as surrogate leads and can be requested
to make a PyPI release on the behalf of the Jazzband members. Please
[open a ticket with a PyPI label](/roadies/issue?labels=pypi) for that.

!!! note "Why are there "lead" project members?"

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

[PyPI]: https://pypi.python.org/
[Travis-CI]: https://travis-ci.org/
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
[setuptools_scm]: https://pypi.python.org/pypi/setuptools_scm

### Travis

Next you will want to set up the project to use Travis-CI for
continous testing. Please refer to the [Python specific
documentation][travis-python] for how to accomplish that.

In addition we strongly recommend using [tox-travis] if the
project is using [tox] (which is also recommended).

[travis-python]: https://docs.travis-ci.com/user/languages/python/
[tox-travis]: https://tox-travis.readthedocs.io/
[tox]: https://tox.readthedocs.io/

Steps needed:

- Set up the `.travis.yml` file following the  [Travis-CI docs][travis-python].
- Create a `tox.ini` which takes [tox-travis] into account.
- [Open an issue](/roadies/issue?labels=pypi) for the
  roadies to enable the auto-release mechanism via the Jazzband.

When you’re ready to do a release to PyPI simply make sure to prepare all
the code you’d like just as before (e.g. update `AUTHORS`, `CHANGELOG`,
documentation, etc.), commit the changes, tag them with `git tag` and push
the code to GitHub with `git push --tags`.

If all goes according to plan, Travis-CI will run the test suite for the
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
