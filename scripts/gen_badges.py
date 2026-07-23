#!/usr/bin/env python3
# Обновляет плашки в README.md актуальными числами из GitHub API:
# Stars (сумма звёзд по своим репам), Repositories (всего своих),
# Private repos (приватных), Followers. Плашка Focus — ручная, не трогается.
import json
import os
import re
import urllib.request

TOKEN = os.environ["GH_TOKEN"]


def api(path):
    req = urllib.request.Request(
        "https://api.github.com" + path,
        headers={
            "Authorization": "Bearer " + TOKEN,
            "Accept": "application/vnd.github+json",
            "User-Agent": "profile-stats",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def main():
    u = api("/user")
    followers = u.get("followers", 0)
    public_repos = u.get("public_repos", 0)
    private_repos = u.get("total_private_repos", 0)
    repositories = public_repos + private_repos

    stars, page = 0, 1
    while True:
        repos = api("/user/repos?per_page=100&affiliation=owner&page=%d" % page)
        if not repos:
            break
        stars += sum(r.get("stargazers_count", 0) for r in repos)
        if len(repos) < 100:
            break
        page += 1

    values = {
        "Stars": stars,
        "Repositories": repositories,
        "Private%20repos": private_repos,
        "Followers": followers,
    }

    with open("README.md", encoding="utf-8") as f:
        readme = f.read()

    for label, val in values.items():
        # badge/<label>-<число>-  →  подменяем только число
        readme = re.sub(
            r"(badge/" + re.escape(label) + r"-)\d+(-)",
            lambda m: m.group(1) + str(val) + m.group(2),
            readme,
        )

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme)

    print("stars=%d repos=%d private=%d followers=%d" % (stars, repositories, private_repos, followers))


if __name__ == "__main__":
    main()
