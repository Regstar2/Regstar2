#!/usr/bin/env python3

import json
import os
import sys
import urllib.request
from fnmatch import fnmatchcase
from pathlib import Path

PROJECTS = {
    "dns-switcher": "Regstar2/dns-switcher",
    "white-list-checker": "Regstar2/white-list-checker",
    "wdtt-windows-home-gateway": "Regstar2/wdtt-windows-home-gateway",
    "tg-ws-proxy-android": "Regstar2/tg-ws-proxy-android",
    "telegram-wsp": "Regstar2/telegram-wsp",
    "pwdtt": "Regstar2/pwdtt",
    "windows-iso-builder": "Regstar2/windows-iso-builder",
    "music-ark": "Regstar2/music-ark",
    "notify-mark": "Regstar2/notify-mark",
}

# Count only installable releases, not metadata, checksums or source archives.
ASSET_PATTERNS = {
    "dns-switcher": ("DnsSwitcher-*-win-x64-setup.exe", "DnsSwitcher-*-win-x64.zip"),
    "white-list-checker": ("WhiteListChecker-*.apk",),
    "wdtt-windows-home-gateway": ("wdtt-windows-home-gateway-*-windows-x64.zip",),
    "tg-ws-proxy-android": ("TgWsProxy-Android-*.apk", "tgwsproxy*.apk"),
    "telegram-wsp": ("Telegram-WSP-release.apk",),
    "pwdtt": (
        "pwdtt-linux-amd64",
        "PWDTT-macos.zip",
        "pwdtt-windows-amd64-setup.exe",
        "pwdtt-windows-amd64.exe",
    ),
    "windows-iso-builder": ("windows-iso-builder-v*.exe", "windows-iso-builder-v*.zip"),
    "music-ark": ("MusicArk-*-win-x64.zip", "MusicArk-Setup-*-x64.exe"),
    "notify-mark": ("NotifyMark-*.apk",),
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


def matches_download_asset(name: str, patterns: tuple[str, ...]) -> bool:
    # Source archives can otherwise match a broad ZIP distributable pattern.
    lower_name = name.lower()
    if any(marker in lower_name for marker in ("-source", "_source", "-src")):
        return False
    return any(fnmatchcase(name, pattern) for pattern in patterns)


def release_downloads(repo: str, patterns: tuple[str, ...]) -> int:
    total = 0
    page = 1
    while True:
        releases = github_json(
            f"https://api.github.com/repos/{repo}/releases?per_page=100&page={page}"
        )
        if not releases:
            break
        for release in releases:
            assets = release.get("assets", [])
            matched = [
                asset for asset in assets
                if matches_download_asset(asset.get("name", ""), patterns)
            ]
            if assets and not matched:
                print(
                    f"Warning: no installable assets matched for {repo} "
                    f"release {release.get('tag_name', '<unknown>')}",
                    file=sys.stderr,
                )
            total += sum(int(asset.get("download_count", 0)) for asset in matched)
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


def render_svg(downloads: int) -> str:
    download_value = compact(downloads)

    icon_w = 20
    download_w = segment_width(download_value)
    total_w = icon_w + download_w
    download_x = icon_w + download_w / 2

    label = f"↓ {download_value}"

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{total_w}" height="20" role="img" aria-label="{label}">
  <title>{label}</title>
  <g shape-rendering="crispEdges">
    <rect width="20" height="20" fill="#21262d"/>
    <rect x="20" width="{download_w}" height="20" fill="#1f6feb"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-size="11">
    <text x="10" y="14">↓</text>
    <text x="{download_x:g}" y="14">{download_value}</text>
  </g>
</svg>
'''


def main() -> None:
    if set(PROJECTS) != set(ASSET_PATTERNS):
        raise ValueError("Every project must have a corresponding asset filter")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for slug, repo in PROJECTS.items():
        downloads = release_downloads(repo, ASSET_PATTERNS[slug])
        (OUT_DIR / f"{slug}-downloads.svg").write_text(
            render_svg(downloads), encoding="utf-8"
        )
        print(f"{repo}: {downloads} downloads")


if __name__ == "__main__":
    main()
