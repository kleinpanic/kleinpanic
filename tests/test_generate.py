"""Offline tests for scripts/generate_readme.py using saved API fixtures.

Run: python3 -m unittest discover -s tests -v
Fixtures in tests/fixtures/ are saved GitHub/Hugging Face API responses
(public data only, trimmed to the fields the generator consumes).
"""
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

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


class FetcherAuthTest(unittest.TestCase):
    def _headers_for(self, url):
        resp = mock.Mock()
        resp.json.return_value = []
        with mock.patch.object(g.requests, "get", return_value=resp) as get:
            g.Fetcher(token="ghs_secret")._get(url)
        return get.call_args.kwargs["headers"]

    def test_token_sent_to_github(self):
        headers = self._headers_for(f"{g.GH_API}/users/kleinpanic")
        self.assertEqual(headers["Authorization"], "Bearer ghs_secret")

    def test_token_not_sent_to_huggingface(self):
        headers = self._headers_for(f"{g.HF_API}/models?author=kleinpanic93&limit=50")
        self.assertNotIn("Authorization", headers)

    def test_token_not_sent_to_lookalike_host(self):
        headers = self._headers_for("https://api.github.com.evil.example/x")
        self.assertNotIn("Authorization", headers)


class RenderTest(unittest.TestCase):
    def test_placeholder_like_text_in_content_is_kept(self):
        # A repo description such as "templates with {{NAME}} vars" used to
        # make render() abort the whole regen with "unreplaced placeholders".
        out = g.render("a {{FEATURED}} b", {"FEATURED": "uses {{NAME}} vars"})
        self.assertEqual(out, "a uses {{NAME}} vars b")

    def test_unknown_template_placeholder_still_fails(self):
        with self.assertRaises(SystemExit):
            g.render("{{MISSING}}", {})


class CheckModeTest(unittest.TestCase):
    def test_check_uses_output_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "README.md"
            args = ["--fixtures", str(FIXTURES), "--date", "2026-07-22", "--output", str(out)]
            with mock.patch.dict(g.os.environ, {}, clear=True), \
                    redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(g.main(args), 0)
                self.assertEqual(g.main(args + ["--check"]), 0)
                out.write_text("stale", encoding="utf-8")
                self.assertEqual(g.main(args + ["--check"]), 1)


if __name__ == "__main__":
    unittest.main()
