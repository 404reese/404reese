#!/usr/bin/env python3
"""Fetch contribution + repo data for the profile cards -> data/github.json.

Needs a token in GH_TOKEN (the workflow passes one). Standard library only.
"""
import datetime
import json
import os
import sys
import urllib.request
from pathlib import Path

LOGIN = os.environ.get("GH_LOGIN", "404reese")
OUT = Path(__file__).resolve().parent.parent / "data" / "github.json"

REPO = "name description url stargazerCount forkCount isFork primaryLanguage { name }"
QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
    createdAt
    followers { totalCount }
    pullRequests { totalCount }
    issues { totalCount }
    owned: repositories(first: 100, ownerAffiliations: OWNER, isFork: false,
                        orderBy: {field: STARGAZERS, direction: DESC}) { totalCount nodes { stargazerCount } }
    pinnedItems(first: 6, types: REPOSITORY) { nodes { ... on Repository { %s } } }
    repositories(first: 12, ownerAffiliations: OWNER, privacy: PUBLIC, isFork: false,
                 orderBy: {field: STARGAZERS, direction: DESC}) { nodes { %s } }
  }
}
""" % (REPO, REPO)


def main():
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit("Set GH_TOKEN to a GitHub token.")

    def gql(query):
        req = urllib.request.Request(
            "https://api.github.com/graphql",
            data=json.dumps({"query": query, "variables": {"login": LOGIN}}).encode(),
            headers={"Authorization": f"bearer {token}", "User-Agent": "profile-cards"},
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            body = json.load(r)
        if body.get("errors") or not body.get("data", {}).get("user"):
            sys.exit(f"GitHub API error: {body.get('errors')}")
        return body["data"]["user"]

    user = gql(QUERY)

    # All-time commits: the API only answers one year at a time, so ask for every year at once.
    first_year = int(user["createdAt"][:4])
    this_year = datetime.datetime.now(datetime.timezone.utc).year
    years = "".join(
        f'y{y}: contributionsCollection(from: "{y}-01-01T00:00:00Z", to: "{y}-12-31T23:59:59Z") '
        "{ totalCommitContributions } "
        for y in range(first_year, this_year + 1)
    )
    per_year = gql("query($login: String!) { user(login: $login) { %s } }" % years)
    stats = {
        "commits": sum(v["totalCommitContributions"] for v in per_year.values()),
        "stars": sum(n["stargazerCount"] for n in user["owned"]["nodes"]),
        "followers": user["followers"]["totalCount"],
        "prs": user["pullRequests"]["totalCount"],
        "issues": user["issues"]["totalCount"],
        "repos": user["owned"]["totalCount"],
        "since": first_year,
    }
    cal = user["contributionsCollection"]["contributionCalendar"]

    days = [
        {"date": d["date"], "count": d["contributionCount"]}
        for w in cal["weeks"] for d in w["contributionDays"]
    ]
    seen, repos = set(), []
    for n in user["pinnedItems"]["nodes"] + user["repositories"]["nodes"]:
        if not n or n["name"] in seen or n["name"].lower() == LOGIN.lower():
            continue
        seen.add(n["name"])
        repos.append({
            "name": n["name"],
            "description": n.get("description") or "",
            "url": n["url"],
            "stars": n["stargazerCount"],
            "forks": n["forkCount"],
            "language": (n.get("primaryLanguage") or {}).get("name") or "",
        })

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps({
        "login": LOGIN,
        "generated": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "total": cal["totalContributions"],
        "days": days,
        "stats": stats,
        "repos": repos,
    }, indent=1))
    print(f"wrote {OUT} ({len(days)} days, {len(repos)} repos)")


if __name__ == "__main__":
    main()
