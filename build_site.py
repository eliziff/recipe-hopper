#!/usr/bin/env python3
"""Build CookCLI output and apply Recipe Hopper's static-site additions."""

import argparse
import html
import os
import re
import shutil
import stat
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent
SITE = ROOT / "_site"

parser = argparse.ArgumentParser()
parser.add_argument("--cook", default="cook")
args = parser.parse_args()

if SITE.exists():
    shutil.rmtree(SITE, onerror=lambda function, path, _: (
        os.chmod(path, stat.S_IWRITE), function(path)
    ))
subprocess.run([
    args.cook, "build", "web", "--base-path", str(ROOT / "recipes"),
    "--base-url", "/recipe-hopper/",
], cwd=ROOT, check=True)

css = (ROOT / "site.css").read_text(encoding="utf-8")
with (SITE / "static/css/custom-styles.css").open("a", encoding="utf-8") as output:
    output.write("\n" + css)
shutil.copy2(ROOT / "planner.html", SITE / "planner.html")

header = """
<header class="site-header print:hidden">
  <a class="site-brand" href="/recipe-hopper/">
    <span class="site-mark" aria-hidden="true">RH</span>
    <span><strong>Recipe Hopper</strong><small>Eight weeks of Sunday cooking</small></span>
  </a>
  <div class="site-search" id="search-container">
    <label class="sr-only" for="search-input">Search recipes</label>
    <input id="search-input" type="search" placeholder="Search dishes or ingredients">
    <div id="search-results" class="hidden"></div>
  </div>
  <a class="site-plan-link" href="/recipe-hopper/planner.html">Weekly plan</a>
</header>
"""
recipe_count = len(list((ROOT / "recipes").glob("*.cook")))
for page in SITE.rglob("*.html"):
    text = page.read_text(encoding="utf-8")
    text = re.sub(
        r'<nav class="bg-white shadow-lg rounded-2xl mb-8 relative">.*?</nav>',
        header,
        text,
        count=1,
        flags=re.S,
    )
    text = text.replace("Recipes - Cook</title>", "Recipe Hopper</title>")
    text = text.replace(" - Cook</title>", " · Recipe Hopper</title>")
    text = re.sub(
        r'<a href="[^"]+\.cook"\s+download.*?title="Download \.cook source".*?</a>',
        "",
        text,
        flags=re.S,
    )
    text = re.sub(
        r'<span class="metadata-pill metadata-source">.*?(https?://[^<]+)</span>',
        lambda match: (
            f'<a class="metadata-pill metadata-source" href="{html.escape(match.group(1))}">'
            "Original recipe</a>"
        ),
        text,
    )
    text = re.sub(
        r">skill-([a-z-]+)</span>",
        lambda match: f">{match.group(1).replace('-', ' ').title()}</span>",
        text,
    )
    text = text.replace(">approachable</span>", ">Approachable</span>")
    text = text.replace(">stretch</span>", ">Stretch</span>")
    text = re.sub(
        r">#skill-([a-z-]+)</span>",
        lambda match: f">Skill · {match.group(1).replace('-', ' ').title()}</span>",
        text,
    )
    text = text.replace(">#approachable</span>", ">Approachable</span>")
    text = text.replace(">#stretch</span>", ">Stretch recipe</span>")
    text = text.replace("🥘 Ingredients", "Ingredients")
    text = text.replace("👤 ", "")
    if page.name == "index.html":
        text = re.sub(
            r"(>\s*)All Recipes(\s*</h1>)",
            lambda match: (
                f"{match.group(1)}Plan, cook, repeat{match.group(2)}"
                f'<p class="catalog-intro">{recipe_count} complete dishes selected '
                "for one-shop weeks and steady skill building.</p>"
            ),
            text,
            count=1,
        )
    page.write_text(text, encoding="utf-8")
