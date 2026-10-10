import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import update_project_metrics as metrics


class ProjectMetricsTests(unittest.TestCase):
    def test_each_project_has_an_asset_filter(self):
        self.assertEqual(set(metrics.PROJECTS), set(metrics.ASSET_PATTERNS))

    def test_installable_assets_are_included_for_all_projects(self):
        expected = {
            "dns-switcher": ["DnsSwitcher-1.5.0-win-x64-setup.exe", "DnsSwitcher-1.5.0-win-x64.zip"],
            "white-list-checker": ["WhiteListChecker-v1.0.0-release.apk"],
            "wdtt-windows-home-gateway": ["wdtt-windows-home-gateway-v1.0.0-windows-x64.zip"],
            "tg-ws-proxy-android": ["TgWsProxy-Android-v1.11.1-arm64-v8a.apk", "tgwsproxy-release.apk", "tgwsproxy-v1.6.0.apk"],
            "telegram-wsp": ["Telegram-WSP-release.apk"],
            "pwdtt": ["pwdtt-linux-amd64", "PWDTT-macos.zip", "pwdtt-windows-amd64-setup.exe", "pwdtt-windows-amd64.exe"],
            "windows-iso-builder": ["windows-iso-builder-v1.0.0.exe", "windows-iso-builder-v1.0.0.zip"],
            "music-ark": ["MusicArk-1.0.0-win-x64.zip", "MusicArk-Setup-1.0.0-x64.exe"],
            "notify-mark": ["NotifyMark-v0.10.1-beta.1.apk"],
            "text-quest-anthology": ["text-quest-anthology-v0.4.0-rc.2.apk", "text-quest-anthology-v0.4.0-rc.1-qf1.apk", "text-quest-anthology-v0.1.8.apk"],
        }
        for slug, names in expected.items():
            for name in names:
                with self.subTest(slug=slug, name=name):
                    self.assertTrue(metrics.matches_download_asset(name, metrics.ASSET_PATTERNS[slug]))

    def test_technical_files_and_source_archives_are_excluded(self):
        ignored = [
            "latest.json", "update-manifest.json", "SOURCE_MANIFEST.json",
            "SHA256SUMS", "SHA256SUMS.txt", "package.apk.sha256",
            "telegram-submodule-ffmpeg-source-123.zip",
            "Telegram-upstream-source-12.10.6-7112.zip",
            "Telegram-WSP-overlay-source-12.10.6.zip",
            "windows-iso-builder-v1.0.0.zip.sha256",
            "windows-iso-builder-v1.0.0-source.zip",
            "text-quest-anthology-v0.4.0-rc.2.aab",
            "text-quest-anthology-v0.4.0-rc.2.apk.sha256",
        ]
        for slug, patterns in metrics.ASSET_PATTERNS.items():
            for name in ignored:
                with self.subTest(slug=slug, name=name):
                    self.assertFalse(metrics.matches_download_asset(name, patterns))

    def test_text_quest_counts_only_apk_assets_across_releases(self):
        releases = [
            {
                "tag_name": "v0.4.0-rc.2",
                "assets": [
                    {"name": "text-quest-anthology-v0.4.0-rc.2.apk", "download_count": 2},
                    {"name": "text-quest-anthology-v0.4.0-rc.2.aab", "download_count": 50},
                ],
            },
            {
                "tag_name": "v0.4.0-rc.1",
                "assets": [
                    {"name": "text-quest-anthology-v0.4.0-rc.1.apk", "download_count": 3},
                ],
            },
            {
                "tag_name": "v0.4.0-rc.1-qf1",
                "assets": [
                    {"name": "text-quest-anthology-v0.4.0-rc.1-qf1.apk", "download_count": 2},
                    {"name": "latest.json", "download_count": 2006},
                ],
            },
            {
                "tag_name": "v0.1.8",
                "assets": [
                    {"name": "text-quest-anthology-v0.1.8.apk", "download_count": 1},
                ],
            },
        ]
        with patch.object(metrics, "github_json", return_value=releases):
            count = metrics.release_downloads(
                "Regstar2/text-quest-anthology",
                metrics.ASSET_PATTERNS["text-quest-anthology"],
            )
        self.assertEqual(count, 8)

    def test_release_downloads_excludes_metadata_across_pages(self):
        release = lambda n: {"tag_name": "v1", "assets": [
            {"name": "Telegram-WSP-release.apk", "download_count": n},
            {"name": "latest.json", "download_count": 2006},
        ]}
        with patch.object(metrics, "github_json", side_effect=[
            [release(1) for _ in range(100)], [release(3)]
        ]) as github_json:
            total = metrics.release_downloads("Regstar2/telegram-wsp", metrics.ASSET_PATTERNS["telegram-wsp"])
        self.assertEqual(total, 103)
        self.assertEqual(github_json.call_count, 2)

    def test_unknown_asset_name_warns_instead_of_counting(self):
        with patch.object(metrics, "github_json", return_value=[{
            "tag_name": "v2", "assets": [{"name": "unknown-installer.bin", "download_count": 99}]
        }]), patch("sys.stderr") as stderr:
            total = metrics.release_downloads("Regstar2/telegram-wsp", metrics.ASSET_PATTERNS["telegram-wsp"])
        self.assertEqual(total, 0)
        self.assertTrue(stderr.write.called)

    def test_render_svg_preserves_compact_badge_format(self):
        badge = metrics.render_svg(1134)
        self.assertIn("↓ 1.1k", badge)
        self.assertIn('<svg xmlns="http://www.w3.org/2000/svg"', badge)


if __name__ == "__main__":
    unittest.main()
