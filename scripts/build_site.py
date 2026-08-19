#!/usr/bin/env python3
"""
build_site.py
--------------
Tiny static site generator. Reads Markdown articles (with a small YAML-ish
front-matter block) from content/articles/, renders them through
templates/base.html, and writes finished HTML + an index + sitemap.xml
into site/.

No framework, no build step beyond "run this script" -- deploy the site/
folder as-is to GitHub Pages, Cloudflare Pages, or Netlify (all free).

Usage: python3 scripts/build_site.py
"""
import re
import shutil
from datetime import datetime
from pathlib import Path

import markdown as md
from jinja2 import Template

ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / "content" / "articles"
TEMPLATE_PATH = ROOT / "templates" / "base.html"
SITE_DIR = ROOT / "docs"  # GitHub Pages can serve straight from a /docs folder, no extra config
SITE_URL = "https://example.com"  # TODO: replace once you have a real domain

# Per-game color-coding + a little emoji personality for tags/cards.
GAME_META = {
    "Magic: The Gathering": {"slug": "game-mtg", "icon": "\U0001F52E"},
    "Pokemon TCG": {"slug": "game-pokemon", "icon": "⚡"},
    "One Piece Card Game": {"slug": "game-onepiece", "icon": "\U0001F3F4‍☠️"},
    "Disney Lorcana": {"slug": "game-lorcana", "icon": "✨"},
    "Riftbound TCG": {"slug": "game-riftbound", "icon": "⚔️"},
    "Collecting & Community": {"slug": "game-community", "icon": "\U0001F4E6"},
}


def game_slug(game: str) -> str:
    return GAME_META.get(game, {}).get("slug", "game-default")


def game_icon(game: str) -> str:
    return GAME_META.get(game, {}).get("icon", "\U0001F0CF")


def style_buy_cta(html_body: str) -> str:
    """Give the '**Where to buy:**' paragraph a class so CSS can turn its
    links into big, clickable CTA buttons instead of plain text links."""
    html_body = html_body.replace(
        "<p><strong>Where to buy:</strong>",
        "<p class=\"buy-cta\"><strong>Where to buy:</strong>",
    )
    # The buttons already have their own spacing -- drop the plain-text
    # middle-dot separator that made sense between plain links, not buttons.
    html_body = html_body.replace("</a> · <a", "</a><a")
    return html_body


def parse_front_matter(text: str):
    """Very small front-matter parser: expects a leading --- block of key: value lines."""
    fm = {}
    body = text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            block = text[3:end].strip()
            body = text[end + 4:].lstrip("\n")
            for line in block.splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    fm[k.strip()] = v.strip()
    return fm, body


def build():
    SITE_DIR.mkdir(exist_ok=True)
    (SITE_DIR / "articles").mkdir(exist_ok=True)

    # copy static assets
    shutil.copyfile(ROOT / "templates" / "style.css", SITE_DIR / "style.css")

    template = Template(TEMPLATE_PATH.read_text(encoding="utf-8"))
    articles = []

    for path in sorted(CONTENT_DIR.glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        fm, body = parse_front_matter(raw)
        html_body = md.markdown(body, extensions=["extra", "sane_lists"])
        html_body = style_buy_cta(html_body)
        title = fm.get("title", path.stem)
        description = fm.get("description", "")
        date = fm.get("date", datetime.now().strftime("%Y-%m-%d"))
        game = fm.get("game", "")
        slug = path.stem

        tag_html = (
            f"<span class='tag {game_slug(game)}'>{game_icon(game)} {game}</span> "
            if game else ""
        )
        page_html = template.render(
            title=title,
            description=description,
            content=f"<article><h1>{title}</h1><p class='meta'>{tag_html}{date}</p>{html_body}</article>",
            root="../",
            year=datetime.now().year,
        )
        out_path = SITE_DIR / "articles" / f"{slug}.html"
        out_path.write_text(page_html, encoding="utf-8")
        articles.append({"title": title, "description": description, "date": date, "slug": slug, "game": game})

    articles.sort(key=lambda a: a["date"], reverse=True)

    # index page
    def index_item(a):
        gslug = game_slug(a["game"])
        tag = (
            f"<span class='tag {gslug}'>{game_icon(a['game'])} {a['game']}</span>"
            if a["game"] else ""
        )
        return (
            f'<li class="article-card {gslug}">'
            f'<span class="meta">{tag} <span>{a["date"]}</span></span>'
            f'<a class="card-title" href="articles/{a["slug"]}.html">{a["title"]}</a>'
            f'<p>{a["description"]}</p>'
            f'<a class="card-cta" href="articles/{a["slug"]}.html">Read the breakdown</a>'
            f'</li>'
        )

    list_items = "\n".join(index_item(a) for a in articles)
    game_pills = "".join(
        f"<span>{meta['icon']} {name}</span>" for name, meta in GAME_META.items()
    )
    index_html = template.render(
        title="CardPulse -- Trading Card Market Data & Analysis",
        description="Plain-English trading card market breakdowns, backed by real price data.",
        content=(
            "<div class='hero'>"
            "<h1>\U0001F525 CardPulse</h1>"
            "<p>Real trading-card market data, tracked regularly, explained simply -- "
            "no fluff, just what's moving and why it matters.</p>"
            f"<div class='game-strip'>{game_pills}</div>"
            "</div>"
            f"<ul class='article-grid'>{list_items}</ul>"
        ),
        root="",
        year=datetime.now().year,
    )
    (SITE_DIR / "index.html").write_text(index_html, encoding="utf-8")

    # about / disclosure page
    about_html = template.render(
        title="About & Affiliate Disclosure",
        description="About CardPulse and how it makes money.",
        content=(
            "<h1>About CardPulse</h1>"
            "<p>CardPulse tracks real trading-card market prices and publishes plain-English "
            "breakdowns of what's moving and why. Data comes from public marketplace APIs.</p>"
            "<h2>Affiliate Disclosure</h2>"
            "<p>Some links on this site are affiliate links (TCGplayer, eBay Partner Network). "
            "If you click through and make a purchase, this site may earn a small commission "
            "at no extra cost to you. We only link to products we'd genuinely point you to.</p>"
            "<h2>Ownership Disclosure</h2>"
            "<p>CardPulse is run by the same person behind "
            "<a href=\"https://proxylair.com\" target=\"_blank\" rel=\"noopener\">ProxyLair</a>, "
            "a custom TCG proxy card design and production studio. We're upfront about that "
            "connection anywhere the two come up -- if an article mentions ProxyLair, treat it "
            "the same way you'd treat any other disclosed relationship on this site.</p>"
        ),
        root="",
        year=datetime.now().year,
    )
    (SITE_DIR / "about.html").write_text(about_html, encoding="utf-8")

    # sitemap.xml
    urls = ["", "about.html"] + [f"articles/{a['slug']}.html" for a in articles]
    sitemap = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        sitemap.append(f"  <url><loc>{SITE_URL}/{u}</loc></url>")
    sitemap.append("</urlset>")
    (SITE_DIR / "sitemap.xml").write_text("\n".join(sitemap), encoding="utf-8")

    # robots.txt
    (SITE_DIR / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n", encoding="utf-8"
    )

    print(f"Built {len(articles)} article(s) into {SITE_DIR}/")


if __name__ == "__main__":
    build()
