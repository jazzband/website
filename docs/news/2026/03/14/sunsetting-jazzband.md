title: Sunsetting Jazzband
tags: django, oss, python
published: 2026-03-14T12:00:00+01:00
author: Jannis Leidel
author_link: https://github.com/jezdez
summary: After more than 10 years, Jazzband is sunsetting.

!!! note "At a glance"

    Jazzband is sunsetting. New signups are disabled. Project leads will
    be contacted before PyCon US 2026 to coordinate transfers. The
    [wind-down plan](/news/2026/03/14/wind-down-plan) has the timeline.
    The [retrospective](/news/2026/03/14/10-years-of-jazzband) looks back
    at the past decade.

[Over 10 years ago](/news/2015/12/17/launching-jazzband), I started
Jazzband as a cooperative experiment to reduce the stress of maintaining
Open Source software. Everyone who joined got access to push code,
triage issues, and merge pull requests. _"We are all part of this."_

It's time to wind things down.

### What happened

#### The slopocalypse

GitHub's [slopocalypse](https://www.theregister.com/2026/02/18/godot_maintainers_struggle_with_draining/),
the flood of AI-generated spam PRs and issues, has made Jazzband's model
of open membership and shared push access untenable.

Jazzband was designed for a world where the worst case was someone
accidentally merging the wrong PR. Now
[only 1 in 10 AI-generated PRs meets project standards](https://www.devclass.com/ai-ml/2026/02/19/github-itself-to-blame-for-ai-slop-prs-say-devs/4091420).
Curl had to
[shut down its bug bounty](https://daniel.haxx.se/blog/2026/01/26/the-end-of-the-curl-bug-bounty/)
after confirmation rates dropped below 5%. GitHub's own response was a
[kill switch to disable pull requests entirely](https://www.theregister.com/2026/02/03/github_kill_switch_pull_requests_ai).
I can't keep giving push access to everyone who joins and expect to
operate Jazzband safely.

#### The one-roadie problem

The cracks have been showing for much longer, though.

Jazzband was always a one-roadie operation. People
[asked for more roadies](https://github.com/jazzband/help/issues/196)
and [offered to help](https://github.com/jazzband/help/issues/423)
over the years. I tried a number of times to make it work, but it never
stuck. I dropped the ball on organizing it properly. When volunteers
stepped up, they'd step back after a while. I don't blame them. Volunteer
work needs a structure that supports people, and I hadn't provided one.

Every project transfer, lead assignment, PyPI permission change and
infrastructure decision still went through me.

#### The warnings

The [sustainability question](https://github.com/jazzband/help/issues/125)
was raised as early as 2017. Five years into Jazzband, I gave a
[keynote at DjangoCon Europe 2021](https://www.youtube.com/watch?v=n8EEhdFUl90)
about it. I said out loud that the "social coding" experiment had failed
to create an equitable community, and that there wasn't a sustainable
solution without serious financial support.

I presented a roadmap to revamp the infrastructure, grow the management
team, formalize guidelines and reach out for funding. None of that
happened. The [PSF fiscal sponsorship](/news/2021/06/04/fiscal-sponsorship)
was the one thing that did.

In the years since, I've been on the PSF board, which faced its own
crises, and now serve as PSF chair. That work matters and I don't regret
prioritizing it. But Jazzband got even less of my time.

#### GitHub went the other way

Meanwhile, GitHub moved in the opposite direction. Copilot launched in
2022, trained on open source code that maintainers were burning out
maintaining for free. [60% of maintainers are still unpaid](https://www.theregister.com/2024/09/18/open_source_maintainers_underpaid).

The [XZ Utils backdoor](https://en.wikipedia.org/wiki/XZ_Utils_backdoor)
in 2024 showed what can happen when a lone maintainer burns out and
someone malicious fills the gap. Jazzband's own infrastructure was also
[getting in the way](https://github.com/jazzband/help/issues/393).
The release pipeline couldn't support
[trusted publishing](https://github.com/jazzband/help/issues/384),
and projects that needed admin access were stuck waiting.

Projects started leaving. That's OK. Moving on was always supposed to
be part of the deal.

#### Django Commons

I want to thank [Django Commons](https://django-commons.org/) and Tim
Schilling for picking up where Jazzband fell short. They have 5 admins
and 15 active projects, including django-debug-toolbar,
django-simple-history and django-cookie-consent from Jazzband.
django-polymorphic is
[transferring over right now](https://github.com/django-commons/membership/issues/445).
They solved the governance problem from day one. If you're a Jazzband
project lead looking for a new home for your Django project, start there.

For non-Django projects like pip-tools, contextlib2, geojson or tablib,
I'm not aware of an equivalent. If someone wants to build one for the
broader Python tooling ecosystem, I'd love to see it.

#### By the numbers

Over 10 years, Jazzband grew to 3,135 members from every continent but
Antarctica, maintained 84 projects with ~93,000 GitHub stars, and shipped
1,312 releases to PyPI.

Projects that passed through Jazzband are downloaded over 150 million
times a month. That includes pip-tools at 23 million and prettytable at
42 million. django-debug-toolbar spent 8 years under Jazzband and ended
up in the official Django tutorial. django-avatar, a repo from 2008, was
still getting releases in 2026. django-axes shipped 129 versions, with a
release every 13 days in its peak year.

The [full 10-year retrospective](/news/2026/03/14/10-years-of-jazzband)
has more of the numbers and stories.

### What happens next

I'm not pulling the plug overnight. The
[detailed wind-down plan](/news/2026/03/14/wind-down-plan) covers the
timeline.

!!! note "Timeline"

    - New signups are disabled as of today.
    - Project leads will be contacted before PyCon US 2026 to coordinate
      transferring their projects to new homes.
    - The GitHub organization and website will remain available during
      the transition period through the end of 2026.

If you're a project lead, expect an email soon.

### Thank you

Thanks to the 81 project leads who kept things going despite the
bottlenecks I created, and to everyone who joined, contributed, filed
issues and shipped releases over the years. You were strangers on the
internet who decided to maintain something together. Jazzband depended
on that willingness to show up.

I started Jazzband because maintaining Open Source alone was exhausting.
The irony of becoming a single point of failure for 71 projects is not
lost on me. Even so, people collaborated, maintained projects and shipped
releases. Those projects will move on to new homes, as they were always
free to do.

**We are all part of this.**
