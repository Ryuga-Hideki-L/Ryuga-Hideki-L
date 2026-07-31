#!/usr/bin/env python3
# Обновляет плашки в README.md: Stars, Repositories, Private repos, Followers.
# Плашка Focus — ручная, не трогается.
#
# Всё берётся ОДНИМ запросом GraphQL, и это принципиально.
#
# Раньше числа приходили из двух разных мест REST: количество репозиториев из
# /user (поля public_repos и total_private_repos), а звёзды — обходом
# /user/repos. У этих двух источников РАЗНАЯ видимость под одним и тем же
# токеном: /user/repos с affiliation=owner отдавал все репозитории, а /user
# показывал total_private_repos=0, если токену не хватало областей. В итоге
# плашки противоречили друг другу — «Stars 4» при двадцати девяти звёздах и
# «Repositories 29» при шести видимых.
#
# У GraphQL видимость одна на весь запрос: либо токен видит приватное целиком,
# либо не видит ничего, и тогда это заметно сразу, а не превращается в
# правдоподобную чушь.
import json
import os
import re
import sys
import urllib.request

TOKEN = os.environ["GH_TOKEN"]

QUERY = """
{
  viewer {
    login
    followers { totalCount }
    private: repositories(ownerAffiliations: OWNER, privacy: PRIVATE) { totalCount }
    all: repositories(ownerAffiliations: OWNER, first: 100) {
      totalCount
      nodes { stargazerCount }
    }
  }
}
"""


def graphql(query):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query}).encode(),
        headers={
            "Authorization": "Bearer " + TOKEN,
            "Content-Type": "application/json",
            "User-Agent": "profile-badges",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        out = json.load(r)
    if "errors" in out:
        sys.exit("GraphQL: " + json.dumps(out["errors"], ensure_ascii=False))
    return out["data"]


def main():
    v = graphql(QUERY)["viewer"]
    stars = sum(n["stargazerCount"] for n in v["all"]["nodes"])
    counts = {
        "Stars": stars,
        "Repositories": v["all"]["totalCount"],
        "Private%20repos": v["private"]["totalCount"],
        "Followers": v["followers"]["totalCount"],
    }

    # Токен без доступа к приватному отдаёт ноль приватных репозиториев и
    # заниженные звёзды. Молча записать это в плашки — значит показать миру
    # неправду и не узнать об этом: падаем, чтобы поломка была видна в логе
    # Actions, а плашки остались прежними.
    if counts["Private%20repos"] == 0 and counts["Repositories"] <= 10:
        sys.exit("Токен не видит приватные репозитории — плашки не трогаю. "
                 "Нужен classic PAT с областями repo и read:user.")

    with open("README.md", encoding="utf-8") as f:
        readme = f.read()

    before = readme
    for label, value in counts.items():
        # badge/<label>-<число>-  →  подменяем только число
        readme = re.sub(
            r"(badge/" + re.escape(label) + r"-)\d+(-)",
            lambda m, v=value: m.group(1) + str(v) + m.group(2),
            readme,
        )

    if readme != before:
        with open("README.md", "w", encoding="utf-8") as f:
            f.write(readme)

    print("stars={} repos={} private={} followers={}".format(
        counts["Stars"], counts["Repositories"],
        counts["Private%20repos"], counts["Followers"]))


if __name__ == "__main__":
    main()
