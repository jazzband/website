title: 10 Years of Jazzband
tags: django, oss, python
published: 2026-03-14T12:02:00+01:00
author: Jannis Leidel
author_link: https://github.com/jezdez
summary: A retrospective on 10 years of Jazzband – the stats, the stories,
         and what actually happened.

!!! note "TL;DR"

    3,135 members, 84 projects, 150M+ PyPI downloads/month, 1,312
    releases. Read on for what worked, what didn't, and what actually
    happened behind the numbers.

Jazzband is [sunsetting](/news/2026/03/14/sunsetting-jazzband). Before
moving on, here's a look at what 10 years of cooperative coding actually
looked like.

### By the numbers

[Five years in](/news/2021/06/04/stats-5-years), we had about 1,350
members and 55 projects. Here's where things stand now:

#### Members

- **3,135 total members** over the years
- **2,133 members** currently – a **68% retention rate** over 10 years
- New members every year, peaking at **424 in 2022**
- Members who left stayed an average of **510 days**
- Based on GitHub profiles (only ~28% of members list a location),
  members from at least **56 countries** across every continent but
  Antarctica – 36% Europe, 30% Asia, 22% North America, 7% South
  America, 3% Africa, 1% Oceania. Real numbers are likely higher. And
  given how widely Python is used in research, someone on Antarctica
  has probably pip-installed a Jazzband project at some point

#### Projects

- **84 projects** total, **71 still active**
- **13 projects** left again over the years
- **~93,000 GitHub stars** across all projects
- **~16,000 forks**

#### Activity

- **~43,800 commits** across all repositories
- **~15,600 pull requests**
- **~12,200 issues**

#### Releases

- **1,429 package uploads** via Jazzband's release pipeline
- **1,312 releases to PyPI** across **56 projects** and **390 versions**
- **281 MB** of release artifacts total
- First upload in November 2017, most recent in March 2026

#### Project teams

- **470 project team memberships**
- **105 lead roles** across **81 project leads**
- Most prolific leads: aleksihakli, hramezani, claudep, and camilonova
  each maintained 4 projects

### How Jazzband was actually used

The numbers above only tell part of the story. Here's what's more
interesting.

#### Not everyone used the release pipeline

20 active projects never shipped a single release through it. Some,
like Watson (2,515 stars) and django-admin2 (1,187), didn't release
at all while under Jazzband. Others, like django-rest-knox,
django-fsm-log, and django-recurrence, published directly to PyPI
on their own – bypassing the pipeline entirely. For these projects,
Jazzband was a collaborative home for shared access and maintenance,
not a release tool.

#### Old projects stayed alive

django-avatar's repo was created in 2008 and shipped its most recent
Jazzband release in January 2026 – a 17-year-old repo still getting
releases. django-axes (2009), sorl-thumbnail (2010), django-constance
(2010), and over 20 other projects created before 2015 were all
still getting releases in 2025 or 2026. Jazzband kept old projects alive
long after their original authors moved on. That was the whole point.

#### Release cadence varied wildly

django-axes had the most active release cadence: 258 release files
across 129 versions, peaking at 28 versions in 2019 – roughly one
every 13 days. pip-tools was second at 146 releases / 73 versions.

Meanwhile, 7 active projects have no team members at all –
django-permission, django-mongonaut, and five others. Nobody was
actively working on them, but they had a home and stayed installable.

#### pip-tools was its own community

With 69 team members it dwarfed every other project (the next largest,
djangorestframework-simplejwt, had 24). It was basically a
sub-organization within Jazzband. And two projects joined as recently
as 2024 (django-tagging, django-summernote) with single-digit stars
and zero releases – people were still finding value in the model right
up to the end.

#### The open access model was genuinely controversial

When django-newsletter
[transferred in](https://github.com/jazzband/django-newsletter/issues/343),
its author @dokterbob worried that giving 800 members write access
would "dissolve the responsibility so much that it might actually
reduce participation." I wrote a long reply defending the open model.

An earlier project, Collectfast,
[actually left Jazzband](https://github.com/jazzband/help/issues/72)
after a member pushed directly to master without review – merging
commits the author had been holding off on. That incident led to real
discussions about code review processes, branch protection, and what
"open access" should actually mean. The tension between openness and
control was never fully resolved.

#### Moderation was another solo job

Over the years I had to block 10 accounts from the GitHub
organization – first crypto spammers who joined just to be in the
org, then community conflicts that needed real moderation decisions,
and finally the AI-driven spam that made the open model untenable.
None of that is unusual for an organization this size, but it all
went through one person.

#### The onboarding bottleneck

Every transferred project got an onboarding checklist – a webhook
automatically opened an "Implement Jazzband guidelines" issue with
TODOs like fixing links, adding badges, setting up CI, adding
`jazzband` to PyPI, deciding on a project lead. 41 projects got one
of these. 28 completed it. 13 are still open.

The pattern in those 13 is telling: contributors would do every item
they could, then get stuck on things that required admin access –
configuring webhooks, fixing CI checks, setting up the release
pipeline – and wait for me. Sometimes for months.

django-user-sessions' original author pinged me five times over two
months about
[broken CI checks](https://github.com/jazzband/django-user-sessions/issues/105)
only an admin could fix. Watson's lead asked twice to
[remove legacy CI tools](https://github.com/jazzband/Watson/issues/509)
blocking PR merges. The checklist was good. The bottleneck was me.

### Projects that moved on

One of the earliest and most visible Jazzband projects was
[django-debug-toolbar](https://github.com/jazzband/help/issues/20),
transferred in back in 2016. It grew to over 8,000 stars under Jazzband
before it
[moved to Django Commons](https://github.com/jazzband/help/issues/369)
in 2024.

[django-simple-history](https://github.com/jazzband/help/issues/382),
[django-oauth-toolkit](https://github.com/jazzband/help/issues/395),
[PrettyTable](https://github.com/jazzband/help/issues/340), and
[tablib](https://github.com/jazzband/help/issues/417) all moved on
too, for similar reasons – they needed more autonomy than Jazzband's
structure could provide.

### Downloads

For context on how widely these projects are used, here are some
numbers from PyPI. All projects that were ever part of Jazzband account
for over **150 million downloads a month**. Current projects alone are
around 95 million.

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

One thing that surprised me: prettytable alone accounts for 42 million
downloads a month, and it isn't even a Django package. contextlib2,
pathlib2, and geojson aren't either. Jazzband ended up being broader
than the Django ecosystem it started in.

django-debug-toolbar
[ranked in the top three most used third-party packages](https://lp.jetbrains.com/django-developer-survey-2023/)
in the Django Developers Survey and is featured in the
[official Django tutorial](https://docs.djangoproject.com/en/5.2/intro/tutorial08/).
It spent 8 years under Jazzband before moving to Django Commons.

If you've come across Jazzband projects before, it was probably through
the [Django News](https://django-news.com/) newsletter, Python Weekly,
or Opensource.com's
[2020 piece on how Jazzband worked](https://opensource.com/article/20/2/python-maintained).

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
