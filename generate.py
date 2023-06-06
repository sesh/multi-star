import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from thttp import request

"""
A bunch of small utilities for generating JSON feeds
"""

AUTHOR_NAME = os.environ["FEED_AUTHOR"]
REPOSITORY_NAME = os.environ["FEED_REPO"]
GITHUB_USERNAME = os.environ["FEED_USERNAME"]
FEED_NAME = os.environ["FEED_NAME"]
GITHUB_TOKEN = os.environ["GH_PAT"]


def url_for_post(post):
    return post["url"]


def content_for_post(post):
    return post["html"]


def save_jsonfeed(posts, *, feed_name, skip_existing_feed=False, duplicate_check_key="id", max_items=1000):
    items = []

    if not skip_existing_feed and (Path("out") / feed_name).exists():
        existing_feed = open(f"out/{feed_name}").read()

        try:
            items = json.loads(existing_feed)["items"]
        except json.decoder.JSONDecodeError:
            pass

    for post in posts:
        if post[duplicate_check_key] not in [item[duplicate_check_key] for item in items]:
            items.append(
                {
                    "id": post["id"],
                    "url": url_for_post(post),
                    "content_html": content_for_post(post),
                    "date_published": post["created_at"] + "Z",
                    "authors": [
                        {
                            "name": AUTHOR_NAME,
                        }
                    ],
                }
            )

    j = {
        "version": "https://jsonfeed.org/version/1.1",
        "title": "Multi Star",
        "home_page_url": f"https://github.com/{GITHUB_USERNAME}/{REPOSITORY_NAME}",
        "feed_url": f"https://{GITHUB_USERNAME}.github.io/{REPOSITORY_NAME}/{feed_name}",
        "items": sorted(items, key=lambda item: item["date_published"], reverse=True)[:max_items],
    }

    return j


def parse_header_links(value):
    """Return a list of parsed link headers proxies.
    i.e. Link: <http:/.../front.jpeg>; rel=front; type="image/jpeg",<http://.../back.jpeg>; rel=back;type="image/jpeg"
    :rtype: list

    Taken from psf/requests
    """

    links = []
    replace_chars = " '\""
    value = value.strip(replace_chars)

    if not value:
        return links

    for val in re.split(", *<", value):
        try:
            url, params = val.split(";", 1)
        except ValueError:
            url, params = val, ""

        link = {"url": url.strip("<> '\"")}

        for param in params.split(";"):
            try:
                key, value = param.split("=")
            except ValueError:
                break

            link[key.strip(replace_chars)] = value.strip(replace_chars)

        links.append(link)

    return links


def following():
    """
    Get all the followers for the current user
    """
    url = "https://api.github.com/user/following"
    data = []

    while url:
        response = request(url, headers={"Authorization": f"token {GITHUB_TOKEN}"})
        data.extend(response.json)

        if "next" in response.headers.get("link"):
            links = parse_header_links(response.headers.get("link"))
            url = [link["url"] for link in links if link["rel"] == "next"][0]
            continue
        url = None

    return data


def starred(user):
    """
    Get all stars for a user, no pagination
    """
    url = f"https://api.github.com/users/{user}/starred"
    params = {"per_page": 100}

    response = request(
        url,
        params=params,
        headers={"Accept": "application/vnd.github.v3.star+json", "Authorization": f"token {GITHUB_TOKEN}"},
    )

    stars = []
    for star in response.json:
        stars.append(star)

    print(user, len(stars))
    return stars


if __name__ == "__main__":
    feed_name = f"{FEED_NAME}.json"

    all_usernames = [x["login"] for x in following()]

    stars = []
    for u in all_usernames:
        stars.extend(starred(u))

    # filter to stars in the last ~60 days
    print("All stars:", len(stars))
    after = (datetime.utcnow() - timedelta(days=60)).replace(tzinfo=timezone.utc)
    stars = [star for star in stars if datetime.fromisoformat(star["starred_at"]).replace(tzinfo=timezone.utc) > after]
    print("Filtered by date:", len(stars))

    repos = []
    multi_stars = []
    for s in stars:
        repo = s["repo"]["full_name"]
        if repo in repos and repo not in multi_stars:
            multi_stars.append(repo)
        repos.append(repo)

    print("Multi stars:", len(multi_stars))

    posts = [
        {
            "html": f'<a href="https://github.com/{repo}">{repo}</a>',
            "id": repo,
            "created_at": datetime.utcnow().isoformat(),
            "url": f"https://github.com/{repo}",
        }
        for repo in multi_stars
    ]

    jsonfeed = save_jsonfeed(posts, feed_name=feed_name)

    with open(f"out/{feed_name}", "w") as f:
        f.write(json.dumps(jsonfeed, indent=2))
