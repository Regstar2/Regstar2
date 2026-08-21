#!/usr/bin/env python3

import json
import os
import urllib.request
from pathlib import Path

PROJECTS = {
    "dns-switcher": "Regstar2/dns-switcher",
    "white-list-checker": "Regstar2/white-list-checker",
    "wdtt-windows-home-gateway": "Regstar2/wdtt-windows-home-gateway",
    "tg-ws-proxy-android": "Regstar2/tg-ws-proxy-android",
}

OUT_DIR = Path("assets/project-metrics")
TOKEN = os.environ.get("GITHUB_TOKEN", "")


def github_json(url: str):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "Regstar2-profile-metrics",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def release_downloads(repo: str) -> int:
    total = 0
    page = 1
    while True:
        releases = github_json(
            f"https://api.github.com/repos/{repo}/releases?per_page=100&page={page}"
        )
        if not releases:
            break
        for release in releases:
            for asset in release.get("assets", []):
                total += int(asset.get("download_count", 0))
        if len(releases) < 100:
            break
        page += 1
    return total


def compact(value: int) -> str:
    if value < 1_000:
        return str(value)
    if value < 1_000_000:
        number = value / 1_000
        return f"{number:.1f}k".replace(".0k", "k")
    number = value / 1_000_000
    return f"{number:.1f}m".replace(".0m", "m")


def segment_width(text: str, minimum: int = 22) -> int:
    return max(minimum, 9 + len(text) * 7)


def render_svg(stars: int, downloads: int) -> str:
    star_value = compact(stars)
    download_value = compact(downloads)

    icon_w = 20
    star_w = segment_width(star_value)
    download_w = segment_width(download_value)
    total_w = icon_w + star_w + icon_w + download_w

    star_x = icon_w + star_w / 2
    download_icon_x = icon_w + star_w
    download_x = download_icon_x + icon_w + download_w / 2

    label = f"★ {star_value} · ↓ {download_value}"

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{total_w}" height="20" role="img" aria-label="{label}">
  <title>{label}</title>
  <g shape-rendering="crispEdges">
    <rect width="20" height="20" fill="#21262d"/>
    <rect x="20" width="{star_w}" height="20" fill="#6e7681"/>
    <rect x="{20 + star_w}" width="20" height="20" fill="#21262d"/>
    <rect x="{40 + star_w}" width="{download_w}" height="20" fill="#1f6feb"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-size="11">
    <text x="10" y="14">★</text>
    <text x="{star_x:g}" y="14">{star_value}</text>
    <text x="{download_icon_x + 10:g}" y="14">↓</text>
    <text x="{download_x:g}" y="14">{download_value}</text>
  </g>
</svg>
'''


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for slug, repo in PROJECTS.items():
        metadata = github_json(f"https://api.github.com/repos/{repo}")
        stars = int(metadata.get("stargazers_count", 0))
        downloads = release_downloads(repo)
        (OUT_DIR / f"{slug}.svg").write_text(
            render_svg(stars, downloads), encoding="utf-8"
        )
        print(f"{repo}: {stars} stars, {downloads} downloads")


if __name__ == "__main__":
    main()
