#!/usr/bin/env python3
"""Regenerate README.md from README.template.md + profile.yml with live API data.

Data sources:
  - GitHub REST API (user stats + repo list). Token optional via GITHUB_TOKEN
    or GH_TOKEN; unauthenticated works but is rate-limited to 60 req/hr.
  - Hugging Face public API (models + datasets for the configured author).

Usage:
  python3 scripts/generate_readme.py                              # live fetch, write README.md
  python3 scripts/generate_readme.py --check                      # exit 1 if README.md is stale
  python3 scripts/generate_readme.py --fixtures tests/fixtures    # offline, no network
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import quote

import requests
import yaml

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = ROOT / "README.template.md"
PROFILE_PATH = ROOT / "profile.yml"
OUTPUT_PATH = ROOT / "README.md"

GH_API = "https://api.github.com"
HF_API = "https://huggingface.co/api"

PLACEHOLDER = re.compile(r"\{\{([A-Z_]+)\}\}")


def esc_cell(text):
    """Escape a string for use inside a Markdown table cell."""
    return (text or "").replace("|", "\\|").replace("\n", " ").strip()


def trunc(text, limit=100):
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


class Fetcher:
    """Reads API data either live (HTTP) or offline from a fixtures directory."""

    def __init__(self, fixtures=None, token=None):
        self.fixtures = Path(fixtures) if fixtures else None
        self.token = token

    def _fixture(self, name):
        return json.loads((self.fixtures / name).read_text(encoding="utf-8"))

    def _get(self, url):
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "kleinpanic-readme-generator",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def github_user(self, user):
        if self.fixtures:
            return self._fixture("github_user.json")
        return self._get(f"{GH_API}/users/{user}")

    def github_repos(self, user):
        if self.fixtures:
            return self._fixture("github_repos.json")
        repos, page = [], 1
        while True:
            batch = self._get(
                f"{GH_API}/users/{user}/repos?per_page=100&sort=pushed&page={page}"
            )
            if not batch:
                break
            repos.extend(batch)
            if len(batch) < 100:
                break
            page += 1
        return repos

    def hf_models(self, user):
        if self.fixtures:
            return self._fixture("hf_models.json")
        return self._get(f"{HF_API}/models?author={user}&limit=50")

    def hf_datasets(self, user):
        if self.fixtures:
            return self._fixture("hf_datasets.json")
        return self._get(f"{HF_API}/datasets?author={user}&limit=50")


def sec_links(profile):
    items = []
    for link in profile.get("links", []):
        badge = (
            f"https://img.shields.io/badge/{link['label']}"
            f"-{quote(str(link['text']), safe='.')}-{link['color']}"
            f"?style=flat-square&logo={link['logo']}&logoColor=white"
        )
        items.append(f'  <a href="{link["url"]}"><img src="{badge}" /></a>')
    return "<p>\n" + "\n".join(items) + "\n</p>"


def sec_stats(user_json, repos):
    owned = [r for r in repos if not r.get("fork")]
    stars = sum(r.get("stargazers_count", 0) for r in owned)
    return (
        f"**{user_json.get('public_repos', len(owned))}** public repos · "
        f"**{user_json.get('followers', 0)}** followers · "
        f"**{stars}** stars across owned repos"
    )


def sec_featured(profile, repos):
    by_name = {r["name"]: r for r in repos}
    rows = ["| Repo | About | ★ |", "| --- | --- | --- |"]
    missing = []
    for name in profile["github"].get("featured", []):
        repo = by_name.get(name)
        if repo is None:
            missing.append(name)
            continue
        rows.append(
            f"| [{name}]({repo['html_url']}) | "
            f"{esc_cell(trunc(repo.get('description') or '—', 110))} | "
            f"{repo.get('stargazers_count', 0)} |"
        )
    if missing:
        print(
            f"warning: featured repos not found on GitHub: {', '.join(missing)}",
            file=sys.stderr,
        )
    return "\n".join(rows)


def sec_recent(profile, repos):
    cfg = profile["github"]
    excluded = set(cfg.get("recent_exclude", []))
    owned = [r for r in repos if not r.get("fork") and r["name"] not in excluded]
    owned.sort(key=lambda r: r.get("pushed_at") or "", reverse=True)
    rows = ["| Repo | About | Last push |", "| --- | --- | --- |"]
    for repo in owned[: int(cfg.get("recent_count", 5))]:
        rows.append(
            f"| [{repo['name']}]({repo['html_url']}) | "
            f"{esc_cell(trunc(repo.get('description') or '—', 90))} | "
            f"{(repo.get('pushed_at') or '')[:10]} |"
        )
    return "\n".join(rows)


def sec_languages(repos):
    counts = Counter(
        r["language"] for r in repos if not r.get("fork") and r.get("language")
    )
    if not counts:
        return "_No language data._"
    top = " · ".join(f"**{lang}** {n}" for lang, n in counts.most_common(8))
    return (
        f"{top}  \n<sub>{sum(counts.values())} owned repos "
        f"with a detected primary language</sub>"
    )


def sec_hf(profile, models, datasets):
    cfg = profile.get("huggingface") or {}
    user = cfg.get("user")
    if not user:
        return "_Hugging Face integration disabled._"
    limit = int(cfg.get("max_items", 5))
    if not models and not datasets:
        return f"_No public assets under [{user}](https://huggingface.co/{user}) yet._"
    lines = [
        f"Everything under [huggingface.co/{user}](https://huggingface.co/{user}), "
        "refreshed weekly.",
        "",
    ]
    if models:
        lines += ["**Models**", "", "| Model | Downloads | Likes |", "| --- | --- | --- |"]
        for m in models[:limit]:
            mid = m.get("id") or m.get("modelId", "")
            lines.append(
                f"| [{mid.split('/', 1)[-1]}](https://huggingface.co/{mid}) | "
                f"{m.get('downloads', 0)} | {m.get('likes', 0)} |"
            )
        lines.append("")
    if datasets:
        lines += ["**Datasets**", "", "| Dataset | Downloads |", "| --- | --- |"]
        for d in datasets[:limit]:
            did = d.get("id", "")
            lines.append(
                f"| [{did.split('/', 1)[-1]}](https://huggingface.co/datasets/{did}) | "
                f"{d.get('downloads', 0)} |"
            )
    return "\n".join(lines).strip()


def sec_now(profile):
    items = profile.get("now") or []
    if not items:
        return ""
    lines = [
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "",
        "## Currently",
        "",
    ]
    lines.extend(f"- {item}" for item in items)
    return "\n".join(lines)


def sec_highlights(profile):
    items = profile.get("highlights") or []
    if not items:
        return ""
    blocks = [
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "",
        "## Things I've built that I actually use",
        "",
    ]
    for h in items:
        name = esc_cell(h.get("name", ""))
        desc = esc_cell(h.get("description", ""))
        lang = h.get("lang", "")
        code = (h.get("code") or "").rstrip()
        blocks.append(
            f"<details>\n"
            f"<summary><kbd>{name}</kbd> — {desc}</summary>\n"
            f"<br/>\n\n"
            f"```{lang}\n{code}\n```\n\n"
            f"</details>"
        )
    return "\n\n".join(blocks)


def sec_last_updated(today):
    return (
        f'<p align="center"><sub>Last refreshed {today} · generated from '
        f'<a href="profile.yml">profile.yml</a> + live GitHub / Hugging Face data by '
        f'<a href="scripts/generate_readme.py">scripts/generate_readme.py</a></sub></p>'
    )


def render(template, sections):
    def repl(match):
        key = match.group(1)
        if key not in sections:
            raise SystemExit(f"error: unknown placeholder {{{{{key}}}}}")
        return sections[key]

    out = PLACEHOLDER.sub(repl, template)
    leftover = PLACEHOLDER.findall(out)
    if leftover:
        raise SystemExit(f"error: unreplaced placeholders: {leftover}")
    return out


def build_sections(profile, fetcher, today):
    gh_user = profile["github"]["user"]
    user_json = fetcher.github_user(gh_user)
    repos = fetcher.github_repos(gh_user)

    hf_user = (profile.get("huggingface") or {}).get("user")
    try:
        models = fetcher.hf_models(hf_user) if hf_user else []
        datasets = fetcher.hf_datasets(hf_user) if hf_user else []
        hf_section = sec_hf(profile, models, datasets)
    except Exception as exc:  # an HF outage must not kill the whole regen
        print(f"warning: Hugging Face fetch failed: {exc}", file=sys.stderr)
        hf_section = "_Hugging Face data temporarily unavailable._"

    return {
        "LINKS": sec_links(profile),
        "STATS": sec_stats(user_json, repos),
        "FEATURED": sec_featured(profile, repos),
        "RECENT": sec_recent(profile, repos),
        "LANGUAGES": sec_languages(repos),
        "HUGGINGFACE": hf_section,
        "NOW": sec_now(profile),
        "HIGHLIGHTS": sec_highlights(profile),
        "LAST_UPDATED": sec_last_updated(today),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fixtures",
        help="read API responses from this directory instead of the network",
    )
    parser.add_argument(
        "--output",
        default=str(OUTPUT_PATH),
        help="where to write the rendered README (default: README.md)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit 1 if regenerating would change README.md",
    )
    parser.add_argument(
        "--date",
        default=None,
        help="override the 'last refreshed' date (used by tests)",
    )
    args = parser.parse_args(argv)

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    profile = yaml.safe_load(PROFILE_PATH.read_text(encoding="utf-8"))
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    today = args.date or datetime.date.today().isoformat()

    fetcher = Fetcher(fixtures=args.fixtures, token=token)
    sections = build_sections(profile, fetcher, today)
    rendered = render(template, sections)

    if args.check:
        current = OUTPUT_PATH.read_text(encoding="utf-8") if OUTPUT_PATH.exists() else ""
        if current != rendered:
            print("README.md is stale — run scripts/generate_readme.py", file=sys.stderr)
            return 1
        print("README.md is up to date")
        return 0

    Path(args.output).write_text(rendered, encoding="utf-8")
    print(f"wrote {args.output} ({len(rendered)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
