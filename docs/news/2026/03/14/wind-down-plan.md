title: Wind-Down Plan
tags: django, oss, python
published: 2026-03-14T12:01:00+01:00
author: Jannis Leidel
author_link: https://github.com/jezdez
summary: The detailed plan for sunsetting Jazzband, including timeline,
         project transfers, and what happens next.

!!! note "TL;DR"

    Signups disabled now. Project leads contacted by May. Transfers
    June–December 2026. Org archived early 2027.

This post outlines the plan for winding down Jazzband. If you haven't
read them yet, see the
[sunsetting announcement](/news/2026/03/14/sunsetting-jazzband) for
context on why this is happening, and the
[10-year retrospective](/news/2026/03/14/10-years-of-jazzband) for the
full story.

### Timeline

The wind-down will happen in phases over the course of 2026.

#### Phase 1: Announcement (March 2026)

- New member signups are **disabled immediately**
- This announcement and wind-down plan are published
- Existing members retain access to the GitHub organization and all
  repositories

#### Phase 2: Outreach (March – May 2026)

- All **80 project leads** will be contacted via email to discuss
  transferring their projects
- The goal is to have initial conversations with every lead before
  **PyCon US 2026** (May 13–19 in Long Beach, CA)
- Leads who don't respond will be followed up with at PyCon US and
  through other channels

#### Phase 3: Project Transfers (June – December 2026)

- Projects will be transferred out of the Jazzband GitHub organization
  to their new homes – whether that's a lead's personal account,
  a new organization, or another collaborative group
- For each project, the transfer includes:
    - **GitHub repository**: transferred to the new owner
    - **PyPI package ownership**: existing maintainers added, Jazzband
      credentials removed
    - **CI/CD configuration**: updated to work outside Jazzband
- Projects without an active lead or willing recipient will be
  **archived** in the Jazzband GitHub organization

#### Phase 4: Wind Down (Early 2027)

- Remaining repositories archived
- The Jazzband GitHub organization set to read-only
- The jazzband.co website archived (with a redirect or static notice)
- PSF Fiscal Sponsorship status concluded, remaining funds donated
  to the PSF general fund

### What happens to...

#### ...existing members?

You remain a member of the GitHub organization until it is archived.
No action is needed on your part. If you'd like to leave earlier,
you can do so from your [account dashboard](/account).

#### ...projects I contribute to?

The projects aren't going away – they're moving. Your contributions,
issues, and pull requests will transfer with the repository to its
new home. Git history is preserved.

#### ...PyPI packages?

Package ownership on PyPI will be transferred to the project leads
before the Jazzband release credentials are deactivated. If you're
a project lead, we'll coordinate this with you directly.

#### ...the Jazzband release pipeline?

The Jazzband-specific release pipeline (uploading via Twine to
jazzband.co, then releasing to PyPI) will remain functional during
the transition period. After transfer, projects will publish to
PyPI directly using standard tooling.

#### ...the website?

The jazzband.co website will remain online through the transition.
After wind-down, it will be replaced with a static page linking to
this announcement and an archive of the project list.

#### ...the PSF Fiscal Sponsorship?

Jazzband's
[PSF Fiscal Sponsorship](/news/2021/06/04/fiscal-sponsorship)
status will be formally concluded. Any remaining funds will be
donated to the Python Software Foundation's general fund.

### For project leads

!!! note "If you're a project lead, here's what to expect"

    1. **You'll receive an email** with details specific to your
       project(s)
    2. **Decide on a new home** for your project – your personal GitHub
       account, a new organization, or another collaborative group like
       [Django Commons](https://django-commons.org/)
    3. **Coordinate the transfer** – we'll handle the GitHub repo
       transfer and help with PyPI ownership changes
    4. **Update your project** – CI/CD, documentation links, and any
       Jazzband-specific references

Several projects have already successfully transferred to
[Django Commons](https://django-commons.org/), including
django-debug-toolbar and django-simple-history. If you're looking for
a place with shared maintenance and multiple admins, it's a good option.

If you have questions or want to start the process early, please
[contact the roadies](/about/contact).
