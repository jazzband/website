title: "Project teams"
tags: django, oss, python
published: 2021-06-04T12:42:18+02:00
author: Jannis Leidel
author_link: https://twitter.com/jezdez
summary: Jazzband adds self-service project teams to improve member communication.

[Five years ago][launch-blogpost], Jazzband was launched to help Python
projects that struggle to continue maintenance for various reasons,
e.g. when original authors don't have time anymore to continue the maintenance.

[launch-blogpost]: /news/2015/12/17/launching-jazzband

Jazzband has grown quite a bit since then: over 1300 people in total have
decided to become members over the past 5 years, of which **over 900 current
members** remain as of writing this post.

At the same time over [50 projects][jazzband-projects] have been transferred
to Jazzband and adopted the [Jazzband guidelines][jazzband-guidelines],
[Code of Conduct][jazzband-coc] and project maintenance patterns.

A handful of projects decided to leave Jazzband again for a number
of reasons, which provided plenty of experience for how to improve the
Jazzband processes and documentation. It's clear that Jazzband can be better
and needs to adapt to the members' needs.

One area in particular was brought up often: the communication
between those members that are interested in contributing to only specific
and not all of the existing [Jazzband projects][jazzband-projects].

So as a first step to fix this:

> **Jazzband introduce self-service project teams!**

## What are project teams?

Project teams are optional, self-service groups of
Jazzband members that are interested in working on specific
projects. Project teams are based on [GitHub teams][github-teams]
teams that you may already be familiar with.

[github-teams]: https://docs.github.com/en/organizations/organizing-members-into-teams/about-teams

That means every Jazzband member can show their
interest in individual projects by electing to join a
project team to further participate in the maintenance of
a project.

GitHub offers a number of extra features for organization
teams that will help to improve a culture of communication
and collaboration:

- Ability to "mention" a whole team (e.g. "@jazzband/pip-tools")
  in GitHub's issues and pull-requests
- Team discussions for every project team
- Ability to request code reviews from whole project teams
- More complex per-project code review assignments
- Custom team avatars etc.

Please remember that team discussions also fall under our [Code of Conduct][jazzband-coc]!

## How can I join a project team?

Every Jazzband project has its own dedicated page on the
Jazzband website.

1. Go to the [project list](/projects).

2. Select the project you'd like to join to go to its project page.

3. Click the link to join in the **"Interested in becoming a project
   member?"** box.

That's it, your GitHub account was automatically added to the project
team on GitHub.

## How can I leave a project team?

Leaving a project team is as simple as joining.

1. Go to your [account dashboard](/account).

2. Select the project you'd like to leave from the **"Your projects"** section.

3. Click the link to leave in the **"Thank you for being a project member!"** box.

After confirming that you really want to leave, your GitHub account will be
automatically removed from the project team on GitHub.

## How do you find team discussions?

There are two ways to get to the project team discussions.
For both you need to be a Jazzband member first!

### On the Jazzband site

Each project has a page on the Jazzband website that lists a number of
important URLs on GitHub. One of those links is for project team
discussions.

1. Go to the [project list](/projects).

2. Select a project you'd like to discuss.

3. Click on the link shown next to **"Team discussions"**.

### On GitHub

1. Go to the members team on [Jazzband's GitHub organization page][jazzband-github-org].
   Note: You'll be greeted here with Jazzband-wide discussions.
   Keep going for project-specific discussions.

[jazzband-github-org]: https://github.com/orgs/jazzband/teams/members

2. There, select the ["Teams" tab][jazzband-team-tab]

[jazzband-team-tab]: https://github.com/orgs/jazzband/teams/members/teams

3. Choose one of the existing project teams from the list and
   you'll be directed to the team discussions.

> **Happy discussions!**

[jazzband-projects]: /projects
[jazzband-guidelines]: /about/guidelines
[jazzband-coc]: /about/conduct
