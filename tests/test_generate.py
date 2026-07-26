"""Offline tests for scripts/generate_readme.py using saved API fixtures.

Run: python3 -m unittest discover -s tests -v
Fixtures in tests/fixtures/ are saved GitHub/Hugging Face API responses
(public data only, trimmed to the fields the generator consumes).
"""
import sys
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
        self.assertIn(f"**{self.user['public_repos']}** public repos", stats)
        self.assertIn(f"**{self.user['followers']}** followers", stats)

    def test_pypi_hidden(self):
        self.assertNotIn("pypi.org", self.output)

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
        # Sanity: rendering still produces no PyPI content when disabled.
        self.assertNotIn("pypi.org", self.output)


if __name__ == "__main__":
    unittest.main()
