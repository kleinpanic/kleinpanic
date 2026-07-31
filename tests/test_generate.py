"""Offline tests for scripts/generate_readme.py using saved API fixtures.

Run: python3 -m unittest discover -s tests -v
Fixtures in tests/fixtures/ are saved GitHub/Hugging Face API responses
(public data only, trimmed to the fields the generator consumes).
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import generate_readme as g

FIXTURES = Path(__file__).resolve().parent / "fixtures"


class GenerateReadmeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = g.yaml.safe_load(
            (g.ROOT / "profile.yml").read_text(encoding="utf-8")
        )
        fetcher = g.Fetcher(fixtures=FIXTURES)
        cls.user = fetcher.github_user("kleinpanic")
        cls.repos = fetcher.github_repos("kleinpanic")
        cls.models = fetcher.hf_models("kleinpanic93")
        cls.datasets = fetcher.hf_datasets("kleinpanic93")
        cls.template = (g.ROOT / "README.template.md").read_text(encoding="utf-8")
        cls.output = g.render(
            cls.template,
            {
                "LINKS": g.sec_links(cls.profile),
                "STATS": g.sec_stats(cls.user, cls.repos),
                "FEATURED": g.sec_featured(cls.profile, cls.repos),
                "RECENT": g.sec_recent(cls.profile, cls.repos),
                "LANGUAGES": g.sec_languages(cls.repos),
                "HUGGINGFACE": g.sec_hf(cls.profile, cls.models, cls.datasets),
                "PYPI": g.sec_pypi(cls.profile, fetcher),
                "NPM": g.sec_npm(cls.profile, fetcher),
                "NOW": g.sec_now(cls.profile),
                "HIGHLIGHTS": g.sec_highlights(cls.profile),
                "LAST_UPDATED": g.sec_last_updated("2026-07-22"),
            },
        )

    def test_no_placeholders_left(self):
        self.assertNotRegex(self.output, r"\{\{[A-Z_]+\}\}")

    def test_all_featured_repos_render(self):
        for name in self.profile["github"]["featured"]:
            self.assertIn(f"](https://github.com/kleinpanic/{name})", self.output)

    def test_recent_table_row_count(self):
        section = g.sec_recent(self.profile, self.repos)
        data_rows = [r for r in section.splitlines() if r.startswith("| [")]
        self.assertEqual(len(data_rows), self.profile["github"]["recent_count"])

    def test_recent_excludes_configured_repos(self):
        section = g.sec_recent(self.profile, self.repos)
        for name in self.profile["github"]["recent_exclude"]:
            self.assertNotIn(f"| [{name}](", section)

    def test_recent_sorted_by_push_date(self):
        section = g.sec_recent(self.profile, self.repos)
        dates = [r.rsplit("|", 2)[-2].strip() for r in section.splitlines() if r.startswith("| [")]
        self.assertEqual(dates, sorted(dates, reverse=True))

    def test_hf_uses_correct_handle(self):
        self.assertIn("huggingface.co/kleinpanic93", self.output)
        self.assertNotIn("huggingface.co/kleinpanic)", self.output)

    def test_hf_models_render_with_downloads(self):
        hf = g.sec_hf(self.profile, self.models, self.datasets)
        self.assertIn("Qwen3-Coder-30B-A3B-Instruct-NVFP4", hf)
        self.assertIn("| 385 |", hf)  # downloads fixture value

    def test_stats_from_fixture(self):
        stats = g.sec_stats(self.user, self.repos)
        self.assertIn(f"{self.user['public_repos']} repos", stats)
        self.assertIn(f"{self.user['followers']} followers", stats)
        self.assertIn("┌─", stats)
        self.assertIn("└", stats)

    def test_stats_panel_well_formed(self):
        stats = g.sec_stats(self.user, self.repos)
        # Box drawing: top and bottom borders match width, content fits inside.
        lines = [ln for ln in stats.splitlines() if ln.startswith(("┌", "│", "└"))]
        self.assertEqual(len(lines), 3)
        self.assertEqual(lines[0][0], "┌")
        self.assertEqual(lines[-1][0], "└")
        self.assertEqual(lines[0][-1], "┐")
        self.assertEqual(lines[-1][-1], "┘")
        self.assertEqual(len(lines[0]), len(lines[-1]))
        self.assertEqual(len(lines[0]), len(lines[1]))

    def test_pypi_hidden(self):
        # PyPI body section is disabled, but the LINKS-row badge is now
        # intentionally present (links to pypi.org/user/kleinpanic).
        self.assertNotIn("## PyPI", self.output)

    def test_pypi_badge_in_links(self):
        # The LINKS row should include the pypi.org/user/kleinpanic badge.
        self.assertIn("pypi.org/user/kleinpanic", self.output)

    def test_links_skip_unconfigured(self):
        links = g.sec_links(self.profile)
        self.assertIn("kleinpanic.com", links)
        self.assertNotIn("youtube", links)  # handle not configured yet

    def test_esc_cell_pipes(self):
        self.assertEqual(g.esc_cell("a | b\nc"), "a \\| b c")

    def test_trunc(self):
        self.assertEqual(g.trunc("short"), "short")
        self.assertTrue(g.trunc("x" * 200, 100).endswith("…"))
        self.assertLessEqual(len(g.trunc("x" * 200, 100)), 100)

    def test_now_renders_when_items(self):
        section = g.sec_now(self.profile)
        self.assertIn("## Currently", section)
        self.assertIn("Memory-spark", section)
        self.assertIn("GSD-OC", section)

    def test_now_hidden_when_empty(self):
        bare = dict(self.profile)
        bare["now"] = []
        self.assertEqual(g.sec_now(bare), "")

    def test_highlights_render_all_items(self):
        section = g.sec_highlights(self.profile)
        for h in self.profile["highlights"]:
            self.assertIn(f"<kbd>{h['name']}</kbd>", section)
            self.assertIn(h["description"], section)

    def test_highlights_hidden_when_empty(self):
        bare = dict(self.profile)
        bare["highlights"] = []
        self.assertEqual(g.sec_highlights(bare), "")

    def test_highlights_open_with_details_tag(self):
        section = g.sec_highlights(self.profile)
        self.assertIn("<details>", section)
        self.assertIn("</details>", section)
        self.assertIn("```bash", section)

    def test_pypi_hidden_with_now_and_highlights(self):
        # Sanity: rendering still produces no PyPI body content when disabled.
        self.assertNotIn("## PyPI", self.output)

    def test_pypi_disabled_returns_empty(self):
        self.assertEqual(g.sec_pypi(self.profile, g.Fetcher(fixtures=FIXTURES)), "")

    def test_pypi_enabled_renders_table(self):
        profile = dict(self.profile)
        profile["pypi"] = {
            "enabled": True,
            "user": "kleinpanic",
            "packages": [{"name": "sample-pkg"}, {"name": "another-pkg"}],
        }
        section = g.sec_pypi(profile, g.Fetcher(fixtures=FIXTURES))
        self.assertIn("## PyPI", section)
        self.assertIn("[sample-pkg](https://pypi.org/project/sample-pkg/)", section)
        self.assertIn("1.2.3", section)
        self.assertIn("[another-pkg](https://pypi.org/project/another-pkg/)", section)

    def test_pypi_enabled_no_packages_returns_empty(self):
        profile = dict(self.profile)
        profile["pypi"] = {"enabled": True, "user": "kleinpanic", "packages": []}
        self.assertEqual(g.sec_pypi(profile, g.Fetcher(fixtures=FIXTURES)), "")

    def test_pypi_skips_missing_packages(self):
        profile = dict(self.profile)
        profile["pypi"] = {
            "enabled": True,
            "user": "kleinpanic",
            "packages": [{"name": "sample-pkg"}, {"name": "does-not-exist-xyz"}],
        }
        section = g.sec_pypi(profile, g.Fetcher(fixtures=FIXTURES))
        self.assertIn("[sample-pkg]", section)
        self.assertNotIn("does-not-exist-xyz", section)

    def test_npm_disabled_returns_empty(self):
        self.assertEqual(g.sec_npm(self.profile, g.Fetcher(fixtures=FIXTURES)), "")

    def test_npm_enabled_renders_table(self):
        profile = dict(self.profile)
        profile["npm"] = {
            "enabled": True,
            "user": "kleinpanic",
            "max_items": 5,
        }
        section = g.sec_npm(profile, g.Fetcher(fixtures=FIXTURES))
        self.assertIn("## npm", section)
        self.assertIn("[kleinpanic-cli](https://www.npmjs.com/package/kleinpanic-cli)", section)
        self.assertIn("0.1.0", section)
        self.assertIn("Weekly DL", section)

    def test_npm_no_packages_returns_empty(self):
        class _EmptyNpmFetcher:
            def npm_search(self, user):
                return {"objects": []}
        profile = dict(self.profile)
        profile["npm"] = {"enabled": True, "user": "nobody-here-xyz"}
        section = g.sec_npm(profile, _EmptyNpmFetcher())
        self.assertEqual(section, "")

    def test_featured_includes_language_column(self):
        section = g.sec_featured(self.profile, self.repos)
        self.assertIn("| Lang |", section)
        # Every featured row should have a non-empty Lang cell.
        for line in section.splitlines():
            if line.startswith("| [") and "](https://github.com/" in line:
                cells = [c.strip() for c in line.split("|")]
                # cells: ['', ' [name](url) ', ' desc ', ' Lang ', ' ★ ', '']
                self.assertGreater(len(cells), 4)
                self.assertTrue(cells[4], f"empty Lang cell in: {line}")


# ---------------------------------------------------------------------------
# Hardening tests: API cache, License/Latest columns, safe_section isolation.
# These cover the changes from the 2026-07-30 hardening pass.
# ---------------------------------------------------------------------------


class CacheTest(unittest.TestCase):
    """The 24h on-disk API cache must not slow CI or break fixtures mode."""

    def setUp(self):
        # Point CACHE_DIR at a tmp dir so tests don't pollute the real cache.
        self._orig_cache_dir = g.CACHE_DIR
        self._tmp = tempfile.TemporaryDirectory()
        g.CACHE_DIR = Path(self._tmp.name)

    def tearDown(self):
        g.CACHE_DIR = self._orig_cache_dir
        self._tmp.cleanup()

    def test_fixtures_mode_bypasses_cache(self):
        """When --fixtures is set, the fetcher must not touch the disk cache."""
        fetcher = g.Fetcher(fixtures=FIXTURES, use_cache=True)
        # Should not raise or write to CACHE_DIR even though use_cache=True.
        data = fetcher.github_user("kleinpanic")
        self.assertEqual(data["login"], "kleinpanic")
        # Nothing should be written under CACHE_DIR.
        self.assertFalse(any(Path(self._tmp.name).iterdir()))

    def test_no_cache_flag_disables_writes(self):
        """--no-cache must skip cache writes even on live fetches."""
        fetcher = g.Fetcher(use_cache=False)
        url = "https://example.test/api"
        fetcher._write_cache(url, {"hello": "world"})
        # No file should appear in the tmp cache dir.
        self.assertFalse(list(Path(self._tmp.name).iterdir()))

    def test_cache_round_trip(self):
        """A write followed by a read returns the same payload."""
        fetcher = g.Fetcher(use_cache=True)
        url = "https://example.test/round-trip"
        payload = {"commits": [1, 2, 3], "user": "kleinpanic"}
        fetcher._write_cache(url, payload)
        cached = fetcher._read_cache(url)
        self.assertEqual(cached, payload)

    def test_cache_ttl_expiry(self):
        """Cache entries older than TTL are ignored (returns None)."""
        fetcher = g.Fetcher(use_cache=True)
        url = "https://example.test/expired"
        fetcher._write_cache(url, {"v": 1})
        # Backdate the file's mtime past the TTL.
        path = fetcher._cache_path(url)
        old = path.stat().st_mtime - (g.CACHE_TTL_SECONDS + 60)
        import os
        os.utime(path, (old, old))
        self.assertIsNone(fetcher._read_cache(url))

    def test_cache_handles_corrupt_file(self):
        """A corrupted cache file must not raise — treat as cache miss."""
        fetcher = g.Fetcher(use_cache=True)
        url = "https://example.test/corrupt"
        path = fetcher._cache_path(url)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("not valid json {{{", encoding="utf-8")
        self.assertIsNone(fetcher._read_cache(url))


class FeaturedMetaTest(unittest.TestCase):
    """Featured table adds License + Latest columns when a fetcher is supplied."""

    @classmethod
    def setUpClass(cls):
        cls.profile = g.yaml.safe_load(
            (g.ROOT / "profile.yml").read_text(encoding="utf-8")
        )
        cls.repos = g.Fetcher(fixtures=FIXTURES).github_repos("kleinpanic")
        cls.meta_fixture = json.loads((FIXTURES / "github_repo_meta.json").read_text())

    def test_with_fetcher_adds_meta_columns(self):
        fetcher = g.Fetcher(fixtures=FIXTURES)
        section = g.sec_featured(self.profile, self.repos, fetcher=fetcher)
        self.assertIn("| License |", section)
        self.assertIn("| Latest |", section)

    def test_without_fetcher_uses_short_header(self):
        """Old behaviour is preserved when no fetcher is passed (e.g. legacy callers)."""
        section = g.sec_featured(self.profile, self.repos)
        self.assertNotIn("| License |", section)
        self.assertNotIn("| Latest |", section)

    def test_meta_fixture_populates_license_and_latest(self):
        """When the meta fixture has data for a featured repo, it appears in the table."""
        fetcher = g.Fetcher(fixtures=FIXTURES)
        section = g.sec_featured(self.profile, self.repos, fetcher=fetcher)
        # fblogin is in the fixture — confirm its license + release show up.
        fblogin_row = next(
            (ln for ln in section.splitlines() if "| fblogin" in ln), None
        )
        self.assertIsNotNone(fblogin_row, "fblogin row missing from featured table")
        self.assertIn("MIT", fblogin_row)
        self.assertIn("1.0.0", fblogin_row)

    def test_fetcher_failures_dont_kill_section(self):
        """If license/release fetches throw, the row still renders with em-dashes."""

        class _BrokenFetcher:
            def __init__(self, outer):
                self.outer = outer

            def github_repo_license(self, owner, repo):
                raise RuntimeError("simulated outage")

            def github_repo_latest_release(self, owner, repo):
                raise RuntimeError("simulated outage")

            # Other methods still delegate to the working fetcher.
            def __getattr__(self, name):
                return getattr(self.outer, name)

        fetcher = _BrokenFetcher(g.Fetcher(fixtures=FIXTURES))
        # Should not raise — license/latest just show "—".
        section = g.sec_featured(self.profile, self.repos, fetcher=fetcher)
        self.assertIn("| License |", section)
        self.assertIn("| — |", section)


class SafeSectionTest(unittest.TestCase):
    """safe_section must isolate failures so one bad section never kills the regen."""

    @classmethod
    def setUpClass(cls):
        cls.profile = g.yaml.safe_load(
            (g.ROOT / "profile.yml").read_text(encoding="utf-8")
        )

    def test_returns_renderer_output_on_success(self):
        self.assertEqual(
            g.safe_section("t", lambda: "hello", fallback="fb"),
            "hello",
        )

    def test_returns_fallback_on_exception(self):
        def boom():
            raise RuntimeError("kaboom")

        result = g.safe_section("t", boom, fallback="fb")
        self.assertEqual(result, "fb")

    def test_uses_default_fallback_when_none_provided(self):
        def boom():
            raise ValueError("nope")

        result = g.safe_section("my-section", boom)
        self.assertEqual(result, "_my-section data temporarily unavailable._")

    def test_empty_string_return_passes_through(self):
        """A section that successfully returns '' stays as '' — that's how
        sec_pypi/sec_npm/sec_now signal 'section disabled, hide it' to the
        template. The default fallback message must NOT fire on empty
        successful results, only on exceptions.
        """

        def empty():
            return ""

        # With explicit fallback: empty result is replaced by fallback.
        self.assertEqual(g.safe_section("t", empty, fallback="fb"), "fb")
        # Without fallback: empty result passes through. The placeholder
        # then resolves to "" in the template, which is the correct signal
        # for "this section is intentionally hidden".
        self.assertEqual(g.safe_section("t", empty), "")

    def test_build_sections_continues_when_one_section_raises(self):
        """Integration check: a section that raises must not crash build_sections."""

        class _HalfBrokenFetcher:
            def __init__(self, good):
                self._good = good

            def github_user(self, user):
                raise RuntimeError("simulated GitHub outage")

            def github_repos(self, user):
                return self._good.github_repos(user)

            def hf_models(self, user):
                return self._good.hf_models(user)

            def hf_datasets(self, user):
                return self._good.hf_datasets(user)

            def github_repo_license(self, owner, repo):
                return None

            def github_repo_latest_release(self, owner, repo):
                return (None, None)

            def pypi_package(self, name):
                return None

            def npm_search(self, user):
                return {"objects": []}

        fetcher = _HalfBrokenFetcher(g.Fetcher(fixtures=FIXTURES))
        # github_user raises — build_sections catches that at the top level and
        # substitutes skeleton user_json. All other sections still render.
        sections = g.build_sections(self.profile, fetcher, "2026-07-30")
        self.assertIn("STATS", sections)
        self.assertIn("RECENT", sections)
        self.assertIn("LANGUAGES", sections)
        # STATS rendered with the skeleton (0 repos, 0 followers) rather than
        # crashing the whole build.
        self.assertIn("0 repos", sections["STATS"])
        self.assertIn("0 followers", sections["STATS"])


class FetcherLicenseReleaseTest(unittest.TestCase):
    """The two new fetcher methods must handle 404s and other failures gracefully."""

    def test_github_repo_license_returns_spdx_id(self):
        fetcher = g.Fetcher(fixtures=FIXTURES)
        spdx = fetcher.github_repo_license("kleinpanic", "fblogin")
        self.assertEqual(spdx, "MIT")

    def test_github_repo_license_missing_returns_none(self):
        fetcher = g.Fetcher(fixtures=FIXTURES)
        self.assertIsNone(fetcher.github_repo_license("kleinpanic", "no-license-repo"))

    def test_github_repo_latest_release_returns_tag_and_url(self):
        fetcher = g.Fetcher(fixtures=FIXTURES)
        tag, url = fetcher.github_repo_latest_release("kleinpanic", "fblogin")
        self.assertEqual(tag, "v1.0.0")
        self.assertIn("github.com/kleinpanic/fblogin/releases/tag/v1.0.0", url)

    def test_github_repo_latest_release_missing_returns_none_pair(self):
        fetcher = g.Fetcher(fixtures=FIXTURES)
        tag, url = fetcher.github_repo_latest_release("kleinpanic", "no-release-repo")
        self.assertEqual((tag, url), (None, None))


if __name__ == "__main__":
    unittest.main()