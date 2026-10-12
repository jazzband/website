title: Wind-Down Plan
tags: django, oss, python
published: 2026-03-14T12:01:00+01:00
author: Jannis Leidel
author_link: https://github.com/jezdez
summary: The detailed plan for sunsetting Jazzband, including timeline,
         project transfers, and what happens next.

!!! note "At a glance"

    Signups are disabled now. Project leads will be contacted by May,
    transfers will take place from June to December 2026, and the
    organization will be archived in early 2027.

Jazzband will wind down over the course of 2026. The
[sunsetting announcement](/news/2026/03/14/sunsetting-jazzband) explains
why. The [10-year retrospective](/news/2026/03/14/10-years-of-jazzband)
looks back at the projects and people involved.

### Timeline

#### Phase 1: Announcement (March 2026)

- New member signups are disabled immediately.
- This announcement and wind-down plan are published.
- Existing members retain access to the GitHub organization and all
  repositories.

#### Phase 2: Outreach (March to May 2026)

- I'll email all 80 project leads to discuss transferring their projects.
- The goal is to have an initial conversation with every lead before
  PyCon US 2026 (May 13–19 in Long Beach, CA).
- I'll follow up with leads who haven't responded at PyCon US and through
  other channels.

#### Phase 3: Project transfers (June to December 2026)

Projects will move out of the Jazzband GitHub organization to a lead's
personal account, a new organization or another collaborative group.
Each transfer includes:

- Moving the GitHub repository to its new owner.
- Updating PyPI package ownership, adding existing maintainers and
  removing Jazzband credentials.
- Updating CI/CD configuration to work outside Jazzband.

Projects without an active lead or willing recipient will be archived
in the Jazzband GitHub organization.

#### Phase 4: Wind-down (Early 2027)

- Archive remaining repositories.
- Set the Jazzband GitHub organization to read-only.
- Archive jazzband.co with a redirect or static notice.
- Conclude the PSF Fiscal Sponsorship and distribute remaining funds in
  coordination with the PSF.

### What happens to...

#### ...existing members?

You remain a member of the GitHub organization until it is archived.
No action is needed on your part. If you'd like to leave earlier, you
can do so from your [account dashboard](/account).

#### ...projects I contribute to?

Projects will move to new homes with their contributions, issues and
pull requests. Git history is preserved.

#### ...PyPI packages?

Package ownership on PyPI will be transferred to project leads before
the Jazzband release credentials are deactivated. If you're a project
lead, we'll coordinate this with you directly.

#### ...the Jazzband release pipeline?

The Jazzband release pipeline, which accepts Twine uploads at
jazzband.co and then releases them to PyPI, will keep working during the
transition. After transfer, projects will publish directly to PyPI using
standard tooling.

#### ...the website?

The jazzband.co website will stay online through the transition. After
wind-down, a static page will replace it, linking to this announcement
and an archive of the project list.

#### ...the PSF Fiscal Sponsorship?

Jazzband's [PSF Fiscal Sponsorship](/news/2021/06/04/fiscal-sponsorship)
will formally end. Distribution of any remaining funds will be
coordinated with the PSF board.

### For project leads

!!! note "What to expect"

    1. You'll receive an email with details specific to your project(s).
    2. Decide on a new home: your personal GitHub account, a new
       organization or another collaborative group such as
       [Django Commons](https://django-commons.org/).
    3. Coordinate the transfer with us. We'll handle the GitHub
       repository transfer and help with PyPI ownership changes.
    4. Update your project's CI/CD, documentation links and
       Jazzband-specific references.

Several projects have already transferred to
[Django Commons](https://django-commons.org/), including
django-debug-toolbar and django-simple-history. If you're looking for
shared maintenance and multiple admins, it's a good option.

If you have questions or want to start the process early, please
[contact the roadies](/about/contact).
