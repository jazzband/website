#!/usr/bin/env python
"""
Check GitHub team structure and permissions.
Run with: dokku run jazzband python check_teams.py
"""
from jazzband.factory import create_app
from jazzband.account import github
from jazzband.projects.models import Project

app = create_app()

with app.app_context():
    print("=" * 80)
    print("GITHUB TEAM PERMISSION AUDIT")
    print("=" * 80)
    
    # Get all teams from org (not just children of Members)
    # Note: github.get_teams() only returns child teams of Members
    # We need to use the org-level endpoint
    all_teams = github.admin_session.get(
        f"orgs/{github.org_name}/teams",
        all_pages=True,
        headers={"Accept": "application/vnd.github.v3+json"},
    )
    print(f"\nFound {len(all_teams)} total teams in GitHub org\n")
    
    # Also check child teams of Members (these should be minimal after flattening)
    members_child_teams = github.get_teams()
    print(f"Child teams of Members (should be few after flattening): {len(members_child_teams)}\n")
    
    # Get active project team slugs from database
    active_projects = Project.query.filter_by(is_active=True).all()
    active_team_slugs = {p.team_slug for p in active_projects if p.team_slug}
    active_leads_team_slugs = {p.leads_team_slug for p in active_projects if p.leads_team_slug}
    
    print(f"Active projects in database: {len(active_projects)}")
    print(f"Active project team slugs: {len(active_team_slugs)}")
    print(f"Active leads team slugs: {len(active_leads_team_slugs)}")
    
    # Check Members team
    print("\n" + "=" * 80)
    print("MEMBERS TEAM")
    print("=" * 80)
    
    members_repos = github.get_team_repos(github.members_team_slug)
    print(f"\nMembers team ({github.members_team_slug}) has {len(members_repos)} repos:")
    
    push_count = 0
    read_count = 0
    other_count = 0
    
    for repo in members_repos:
        perms = repo.get('permissions', {})
        if perms.get('push'):
            push_count += 1
        elif perms.get('pull'):
            read_count += 1
        else:
            other_count += 1
    
    print(f"  - Push (write): {push_count}")
    print(f"  - Read: {read_count}")
    print(f"  - Other: {other_count}")
    
    # Identify repos with non-push permissions
    if read_count > 0 or other_count > 0:
        print(f"\n⚠️  WARNING: Repos without PUSH permission in Members team:")
        for repo in members_repos:
            perms = repo.get('permissions', {})
            if not perms.get('push'):
                perm_str = "pull" if perms.get('pull') else "admin" if perms.get('admin') else "unknown"
                print(f"  - {repo['name']}: {perm_str} (should be push)")
    
    # Sample repos
    print(f"\nSample repos (first 10):")
    for repo in members_repos[:10]:
        perms = repo.get('permissions', {})
        perm_str = "push" if perms.get('push') else "pull" if perms.get('pull') else "unknown"
        print(f"  - {repo['name']}: {perm_str}")
    
    # Check project teams
    print("\n" + "=" * 80)
    print("PROJECT TEAMS")
    print("=" * 80)
    
    project_teams = []
    stale_teams = []
    teams_with_parents = []
    
    for team in all_teams:
        slug = team['slug']
        
        # Skip special teams
        if slug in [github.members_team_slug, github.roadies_team_slug]:
            continue
        
        # Check if it's a leads team
        if slug.endswith('-leads'):
            continue
        
        # Check if team still has a parent
        if team.get('parent'):
            teams_with_parents.append((slug, team['parent'].get('name', 'unknown')))
        
        # Check if it's an active project team
        if slug in active_team_slugs:
            project_teams.append(team)
        else:
            # Might be a stale team
            stale_teams.append(team)
    
    print(f"\nActive project teams: {len(project_teams)}")
    print(f"Potentially stale teams: {len(stale_teams)}")
    
    if teams_with_parents:
        print(f"\n⚠️  WARNING: {len(teams_with_parents)} project teams still have parents (should be 0 after flattening):")
        for slug, parent_name in teams_with_parents[:10]:
            print(f"  - {slug} → parent: {parent_name}")
    else:
        print(f"\n✓ No project teams have parents (correctly flattened)")
    
    # Check repo assignments for active project teams
    print(f"\nChecking repo assignments for active project teams...")
    teams_with_repos = []
    
    for team in project_teams[:20]:  # Check first 20 to avoid rate limits
        slug = team['slug']
        repos = github.get_team_repos(slug)
        if repos:
            teams_with_repos.append((slug, len(repos), repos))
    
    if teams_with_repos:
        print(f"\n{len(teams_with_repos)} project teams have repos assigned:")
        for slug, count, repos in teams_with_repos[:10]:
            print(f"\n  {slug} ({count} repos):")
            for repo in repos[:3]:  # Show first 3
                perms = repo.get('permissions', {})
                perm_str = "push" if perms.get('push') else "pull" if perms.get('pull') else "admin" if perms.get('admin') else "unknown"
                print(f"    - {repo['name']}: {perm_str}")
    else:
        print("\n✓ No project teams have repos assigned (correct!)")
    
    # Check leads teams
    print("\n" + "=" * 80)
    print("LEADS TEAMS")
    print("=" * 80)
    
    leads_teams = [t for t in all_teams if t['slug'].endswith('-leads')]
    print(f"\nFound {len(leads_teams)} leads teams")
    
    active_leads = [t for t in leads_teams if t['slug'] in active_leads_team_slugs]
    stale_leads = [t for t in leads_teams if t['slug'] not in active_leads_team_slugs]
    
    print(f"  - Active: {len(active_leads)}")
    print(f"  - Potentially stale: {len(stale_leads)}")
    
    # Sample some leads teams
    print(f"\nSample leads teams (first 5):")
    for team in leads_teams[:5]:
        slug = team['slug']
        repos = github.get_team_repos(slug)
        parent = team.get('parent', {})
        parent_name = parent.get('name', 'None') if parent else 'None'
        print(f"  - {slug}: {len(repos)} repos, parent: {parent_name}")
    
    # Stale teams report
    if stale_teams:
        print("\n" + "=" * 80)
        print("POTENTIALLY STALE TEAMS")
        print("=" * 80)
        print(f"\nFound {len(stale_teams)} teams not in active projects:")
        for team in stale_teams[:20]:
            slug = team['slug']
            repos = github.get_team_repos(slug)
            print(f"  - {slug}: {len(repos)} repos")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"""
Active Projects: {len(active_projects)}
Total Teams: {len(all_teams)}
  - Members team: 1 ({len(members_repos)} repos)
  - Active project teams: {len(project_teams)}
  - Active leads teams: {len(active_leads)}
  - Stale teams: {len(stale_teams)}
  - Stale leads teams: {len(stale_leads)}

Members Team Permissions:
  - Push (write): {push_count} repos
  - Read: {read_count} repos
  - Other: {other_count} repos

Expected Structure:
  ✓ Members team should have ~{len(active_projects)} repos with PUSH
  ✓ Project teams should have 0 repos (just for @mentions)
  ✓ Leads teams should have 1 repo each with MAINTAIN
""")
    
    print("\n" + "=" * 80)

