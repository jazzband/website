title: 10 Years of Jazzband
tags: django, oss, python
published: 2026-03-14T12:02:00+01:00
author: Jannis Leidel
author_link: https://github.com/jezdez
summary: A retrospective on 10 years of Jazzband – the stats, the stories,
         and what actually happened.

!!! note "At a glance"

    Over 10 years, Jazzband had 3,135 members and 84 projects. Those
    projects receive 150M+ PyPI downloads/month, and the Jazzband release
    pipeline shipped 1,312 releases.

Jazzband is [sunsetting](/news/2026/03/14/sunsetting-jazzband). Before
moving on, I wanted to look back at how people used it over the past
10 years, including where it let them down.

### By the numbers

[Five years in](/news/2021/06/04/stats-5-years), we had about 1,350
members and 55 projects.

#### Members

- 3,135 total members over the years.
- 2,133 current members, a 68% retention rate over 10 years.
- New members every year, peaking at 424 in 2022.
- Members who left stayed an average of 510 days.
- GitHub profiles place members in at least 56 countries across every
  continent but Antarctica: 36% Europe, 30% Asia, 22% North America,
  7% South America, 3% Africa and 1% Oceania. Only ~28% of members list
  a location, so the real numbers are likely higher. Given how widely
  Python is used in research, I suspect someone on Antarctica has
  pip-installed a Jazzband project too.

#### Projects

- 84 projects in total, with 71 still active.
- 13 projects left again over the years.
- ~93,000 GitHub stars across all projects.
- ~16,000 forks.

#### Activity

- ~43,800 commits across all repositories.
- ~15,600 pull requests.
- ~12,200 issues.

#### Releases

- 1,429 package uploads through Jazzband's release pipeline.
- 1,312 releases to PyPI across 56 projects and 390 versions.
- 281 MB of release artifacts in total.
- First upload in November 2017, most recent in March 2026.

#### Project teams

- 470 project team memberships.
- 105 lead roles across 81 project leads.
- aleksihakli, hramezani, claudep and camilonova each maintained
  4 projects, the most of any lead.

### How people used Jazzband

#### Not everyone used the release pipeline

20 active projects never shipped a release through it. Watson (2,515
stars) and django-admin2 (1,187), for example, didn't release at all
while under Jazzband. Others, including django-rest-knox, django-fsm-log
and django-recurrence, published directly to PyPI on their own. They
used Jazzband for shared access and maintenance while keeping their own
release process.

#### Old projects stayed alive

django-avatar's repo was created in 2008 and shipped its most recent
Jazzband release in January 2026. A 17-year-old repo was still getting
releases. django-axes (2009), sorl-thumbnail (2010), django-constance
(2010) and over 20 other projects created before 2015 were still getting
releases in 2025 or 2026. Jazzband helped keep them alive long after
their original authors moved on.

#### Release cadence varied wildly

django-axes had the most active release cadence: 258 release files
across 129 versions, peaking at 28 versions in 2019, roughly one every
13 days. pip-tools was second at 146 releases across 73 versions.

Meanwhile, 7 active projects have no team members at all, including
django-permission and django-mongonaut. Nobody was actively working on
those seven projects, but they had a home and stayed installable.

#### pip-tools was its own community

With 69 team members, pip-tools was much larger than any other project.
The next largest, djangorestframework-simplejwt, had 24. pip-tools was
almost an organization within Jazzband.

People were still finding value in the model near the end. django-tagging
and django-summernote joined in 2024 with single-digit stars and zero
releases.

#### Open access was controversial

When django-newsletter
[transferred in](https://github.com/jazzband/django-newsletter/issues/343),
its author @dokterbob worried that giving 800 members write access
would "dissolve the responsibility so much that it might actually
reduce participation." I wrote a long reply defending the open model.

An earlier project, Collectfast,
[left Jazzband](https://github.com/jazzband/help/issues/72) after a
member pushed directly to master without review and merged commits the
author had been holding off on. We discussed code review, branch
protection and what "open access" should mean. We never fully resolved
the tension between openness and control.

#### Moderation was another solo job

Over the years I had to block 10 accounts from the GitHub organization.
First came crypto spammers who joined just to be in the org, then
community conflicts that needed moderation decisions, and finally the
AI-driven spam that made the open model untenable. None of that is
unusual for an organization this size, but it all went through me.

#### The onboarding bottleneck

Every transferred project got an onboarding checklist. A webhook opened
an "Implement Jazzband guidelines" issue with TODOs such as fixing
links, adding badges, setting up CI, adding `jazzband` to PyPI and
choosing a project lead. Of the 41 projects that received one, 28
completed it and 13 still have it open.

In those 13 projects, contributors would finish the work they could do,
then get stuck on things that required admin access: configuring
webhooks, fixing CI checks or setting up the release pipeline. They had
to wait for me, sometimes for months.

django-user-sessions' original author pinged me five times over two
months about [broken CI checks](https://github.com/jazzband/django-user-sessions/issues/105)
that only an admin could fix. Watson's lead asked twice to
[remove legacy CI tools](https://github.com/jazzband/Watson/issues/509)
that blocked PR merges. The checklist was useful, but I couldn't keep
up with the work it left for me.

### Projects that moved on

[django-debug-toolbar](https://github.com/jazzband/help/issues/20) was
one of the earliest and most visible Jazzband projects. It transferred
in during 2016, grew to over 8,000 stars, and
[moved to Django Commons](https://github.com/jazzband/help/issues/369)
in 2024.

[django-simple-history](https://github.com/jazzband/help/issues/382),
[django-oauth-toolkit](https://github.com/jazzband/help/issues/395),
[PrettyTable](https://github.com/jazzband/help/issues/340) and
[tablib](https://github.com/jazzband/help/issues/417) also moved on.
They needed more autonomy than Jazzband's structure could provide.

### Downloads

Projects that were ever part of Jazzband account for over 150 million
PyPI downloads a month. Current projects alone account for around
95 million.

Top 15 by monthly downloads:

| Project | Downloads/month | Note |
|---------|----------------:|------|
| prettytable | 42.4M | left Jazzband |
| pip-tools | 23.3M | |
| contextlib2 | 10.7M | |
| django-redis | 9.6M | |
| django-debug-toolbar | 7.3M | left, now Django Commons |
| djangorestframework-simplejwt | 6.1M | |
| dj-database-url | 5.5M | |
| pathlib2 | 4.9M | |
| django-model-utils | 4.8M | |
| geojson | 4.6M | |
| tablib | 4.1M | |
| django-oauth-toolkit | 3.7M | left |
| django-simple-history | 3.1M | left, now Django Commons |
| django-silk | 2.7M | |
| django-formtools | 2.1M | |

I was surprised that prettytable alone accounts for 42 million downloads
a month. It isn't a Django package, and neither are contextlib2, pathlib2
or geojson. Jazzband ended up being broader than the Django ecosystem
it started in.

django-debug-toolbar
[ranked in the top three most used third-party packages](https://lp.jetbrains.com/django-developer-survey-2023/)
in the Django Developers Survey and is featured in the
[official Django tutorial](https://docs.djangoproject.com/en/5.2/intro/tutorial08/).
It spent 8 years under Jazzband before moving to Django Commons.

You may have come across these projects through the
[Django News](https://django-news.com/) newsletter, Python Weekly or
Opensource.com's [2020 piece on how Jazzband worked](https://opensource.com/article/20/2/python-maintained).

### Top 10 projects by stars

| Project | Stars |
|---------|------:|
| [pip-tools](https://github.com/jazzband/pip-tools) | 7,997 |
| [django-silk](https://github.com/jazzband/django-silk) | 4,939 |
| [tablib](https://github.com/jazzband/tablib) | 4,752 |
| [djangorestframework-simplejwt](https://github.com/jazzband/djangorestframework-simplejwt) | 4,310 |
| [django-taggit](https://github.com/jazzband/django-taggit) | 3,429 |
| [django-redis](https://github.com/jazzband/django-redis) | 3,059 |
| [django-model-utils](https://github.com/jazzband/django-model-utils) | 2,759 |
| [Watson](https://github.com/jazzband/Watson) | 2,515 |
| [django-push-notifications](https://github.com/jazzband/django-push-notifications) | 2,384 |
| [django-widget-tweaks](https://github.com/jazzband/django-widget-tweaks) | 2,165 |
