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
catalogue_toolbar = """
<section class="catalogue-toolbar" aria-label="Recipe filters">
  <div class="catalogue-filters" role="group" aria-label="Filter recipes">
    <button class="is-active" type="button" data-filter="all">All dishes</button>
    <button type="button" data-filter="stretch">Skill-building</button>
    <button type="button" data-filter="vegetarian">Vegetarian</button>
    <button type="button" data-filter="poultry">Chicken &amp; turkey</button>
    <button type="button" data-filter="meat">Beef &amp; pork</button>
    <button type="button" data-filter="seafood">Seafood</button>
    <button type="button" data-filter="soup">Soups &amp; stews</button>
    <button type="button" data-filter="pasta">Pasta &amp; noodles</button>
  </div>
  <p id="catalogue-status" class="catalogue-status" aria-live="polite"></p>
</section>
"""
catalogue_script = """
<script>
(() => {
  const grid = document.getElementById("recipes-grid");
  if (!grid) return;
  const cards = [...grid.querySelectorAll(".recipe-card")];
  const status = document.getElementById("catalogue-status");
  const search = document.getElementById("search-input");
  const buttons = [...document.querySelectorAll("[data-filter]")];
  const PAGE = 18;
  let filter = "all";
  let limit = PAGE;

  const category = (card) => {
    const title = card.querySelector("h3").textContent.toLowerCase();
    if (card.textContent.includes("Stretch")) return "stretch";
    if (/\\b(chicken|turkey)\\b/.test(title)) return "poultry";
    if (/\\b(beef|pork|sausage|burger|chorizo|bacon)\\b/.test(title)) return "meat";
    if (/\\b(shrimp|fish|salmon|cod|seafood)\\b/.test(title)) return "seafood";
    if (/\\b(soup|stew|chowder|chili)\\b/.test(title)) return "soup";
    if (/\\b(pasta|noodle|linguine|lasagna|gnocchi|orzo|risotto|penne)\\b/.test(title)) return "pasta";
    return "vegetarian";
  };

  cards.forEach(card => {
    card.dataset.category = category(card);
    card.classList.toggle("recipe-card--text", !card.querySelector("img"));
    if (!card.querySelector("img")) {
      card.dataset.initial = card.querySelector("h3").textContent.trim()
        .split(/\\s+/).slice(0, 2).map(word => word[0]).join("").toUpperCase();
    }
  });

  const draw = () => {
    const query = (search?.value || "").trim().toLowerCase();
    const matches = cards.filter(card => {
      const categoryMatch = filter === "all" || card.dataset.category === filter;
      return categoryMatch && (!query || card.textContent.toLowerCase().includes(query));
    });
    cards.forEach(card => { card.hidden = true; });
    matches.slice(0, limit).forEach(card => { card.hidden = false; });
    const shown = Math.min(matches.length, limit);
    status.innerHTML = `Showing ${shown} of ${matches.length} dishes` +
      (shown < matches.length ? ` <button type="button" id="show-more">Show ${Math.min(PAGE, matches.length - shown)} more</button>` : "");
    document.getElementById("show-more")?.addEventListener("click", () => {
      limit += PAGE;
      draw();
    });
  };

  buttons.forEach(button => button.addEventListener("click", () => {
    filter = button.dataset.filter;
    limit = PAGE;
    buttons.forEach(item => item.classList.toggle("is-active", item === button));
    draw();
  }));
  search?.addEventListener("input", () => {
    limit = PAGE;
    draw();
  });
  draw();
})();
</script>
"""
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
    text = text.replace(" - Cook</title>", " &middot; Recipe Hopper</title>")
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
        lambda match: f">Skill: {match.group(1).replace('-', ' ').title()}</span>",
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
                f"{match.group(1)}Recipes{match.group(2)}"
            ),
            text,
            count=1,
        )
        text = text.replace(
            '<div id="recipes-grid"',
            catalogue_toolbar + '\n<div id="recipes-grid"',
            1,
        )
        text = text.replace("</body>", catalogue_script + "\n</body>")
    page.write_text(text, encoding="utf-8")
