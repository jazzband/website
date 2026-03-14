title: Sunsetting Jazzband
tags: django, oss, python
published: 2026-03-14T12:00:00+01:00
author: Jannis Leidel
author_link: https://github.com/jezdez
summary: After more than 10 years, Jazzband is sunsetting.

**TL;DR:** Jazzband is sunsetting. New signups are disabled. Project
leads will be contacted before PyCon US 2026 to coordinate transfers.
The [wind-down plan](/news/2026/03/14/wind-down-plan) has the timeline,
the [retrospective](/news/2026/03/14/10-years-of-jazzband) has the
full story.

[Over 10 years ago](/news/2015/12/17/launching-jazzband), Jazzband started
as a cooperative experiment to reduce the stress of maintaining Open Source
software projects. The idea was simple – everyone who joins gets access to
push code, triage issues, merge pull requests. _"We are all part of this."_

It had a good run. More than 10 years, actually.

But it's time to wind things down.

### What happened

#### The slopocalypse

GitHub's [slopocalypse](https://www.theregister.com/2026/02/18/godot_maintainers_struggle_with_draining/) –
the flood of AI-generated spam PRs and issues – has made Jazzband's model
of open membership and shared push access untenable.

Jazzband was designed for a world where the worst case was someone
accidentally merging the wrong PR. In a world where
[only 1 in 10 AI-generated PRs meets project standards](https://www.devclass.com/ai-ml/2026/02/19/github-itself-to-blame-for-ai-slop-prs-say-devs/4091420),
where curl had to
[shut down its bug bounty](https://daniel.haxx.se/blog/2026/01/26/the-end-of-the-curl-bug-bounty/)
because confirmation rates dropped below 5%, and where GitHub's own
response was a
[kill switch to disable pull requests entirely](https://www.theregister.com/2026/02/03/github_kill_switch_pull_requests_ai) –
an organization that gives push access to everyone who joins simply
can't operate safely anymore.

#### The one-roadie problem

But honestly, the cracks have been showing for much longer than that.

Jazzband was always a one-roadie operation. People
[asked for more roadies](https://github.com/jazzband/help/issues/196)
and
[offered to help](https://github.com/jazzband/help/issues/423)
over the years, and I tried a number of times to make it work – but it
never stuck. I dropped the ball on organizing it properly, and when
volunteers did step up they'd quietly step back after a while. That's
not a criticism of them, it's just how volunteer work goes when there's
no structure to support it.

The result was the same though: every release request, every project
transfer, every lead assignment, every PyPI permission change – it all
went through me.

#### The warnings

The [sustainability question](https://github.com/jazzband/help/issues/125)
was raised as early as 2017. I gave a
[keynote at DjangoCon Europe 2021](https://www.youtube.com/watch?v=n8EEhdFUl90)
about it – five years in. In that talk I said out loud that the "social
coding" experiment had failed to create an equitable community, and that
a sustainable solution didn't exist without serious financial support.

The roadmap I presented – revamp infrastructure, grow the management
team, formalize guidelines, reach out for funding – none of that
happened. The [PSF fiscal sponsorship](/news/2021/06/04/fiscal-sponsorship)
was the one thing that did.

In the years since, I've been on the PSF board – which faced its own
crises – and now serve as PSF chair. That work matters and I don't
regret prioritizing it, but it meant Jazzband got even less of my time.

#### GitHub went the other way

Meanwhile, GitHub moved in the opposite direction. Copilot launched in
2022, trained on open source code that maintainers were burning out
maintaining for free. GitHub Sponsors participation sits at
[0.0014%](https://byteiota.com/open-source-maintainer-crisis-60-unpaid-burnout-hits-44/).
60% of maintainers are still unpaid.

The [XZ Utils backdoor](https://en.wikipedia.org/wiki/XZ_Utils_backdoor)
in 2024 showed what happens when a lone maintainer burns out and someone
malicious fills the gap. And Jazzband's own infrastructure started
[getting in the way](https://github.com/jazzband/help/issues/393) of
the projects it was supposed to help – the release pipeline couldn't
support
[trusted publishing](https://github.com/jazzband/help/issues/384),
projects that needed admin access were stuck.

So projects started leaving. And that's OK – that was always supposed
to be part of the deal.

#### Django Commons

I want to specifically thank [Django Commons](https://django-commons.org/)
and Tim Schilling for picking up where Jazzband fell short. They have
5 admins, 15 active projects (including django-debug-toolbar,
django-simple-history, and django-cookie-consent from Jazzband), and
django-polymorphic is
[transferring over right now](https://github.com/django-commons/membership/issues/445).
They solved the governance problem from day one. If you're a Jazzband
project lead looking for a new home for your Django project, start there.

For non-Django projects like pip-tools, contextlib2, geojson, or
tablib – I'm not aware of an equivalent. If someone wants to build
one for the broader Python tooling ecosystem, I'd love to see it.

#### By the numbers

Over 10 years, Jazzband grew to 3,135 members from every continent
but Antarctica, maintained 84 projects with ~93,000 GitHub stars,
and shipped 1,312 releases to PyPI.

Projects that passed through Jazzband are downloaded over 150 million
times a month – pip-tools at 23 million, prettytable at 42 million.
django-debug-toolbar spent 8 years under Jazzband and ended up in the
official Django tutorial. django-avatar, a repo from 2008, was still
getting releases in 2026. And django-axes shipped 127 versions – a
release every 13 days in its peak year.

The [full 10-year retrospective](/news/2026/03/14/10-years-of-jazzband)
has all the numbers, the stories, and what actually happened.

### What happens next

I'm not pulling the plug overnight. There is a
[detailed wind-down plan](/news/2026/03/14/wind-down-plan) that covers
the timeline, but the short version:

- **New signups are disabled** as of today
- **Project leads will be contacted** before PyCon US 2026 to coordinate
  transferring projects to new homes
- **The GitHub organization and website** will remain available during
  the transition period through end of 2026

If you're a project lead, expect an email soon.

### Thank you

None of this would have been possible without the people who showed
up – strangers on the internet who decided to maintain something
together. Thanks to the 81 project leads who kept things going despite
the bottlenecks I created, and to everyone who joined, contributed,
filed issues, and shipped releases over the years.

I started Jazzband because maintaining Open Source alone was exhausting.
The irony of then becoming a single point of failure for 71 projects is
not lost on me. But the experiment worked in the ways that mattered –
projects got maintained, releases got shipped, people collaborated.

Anyways, the projects will move on to new homes, and that's fine. That
was always the point.

**We are all part of this.**
