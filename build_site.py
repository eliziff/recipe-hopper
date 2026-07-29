#!/usr/bin/env python3
"""Build CookCLI output and apply Recipe Hopper's static-site additions."""

import argparse
import atexit
import html
import json
import os
import re
import shutil
import stat
import subprocess
import tempfile
from fractions import Fraction
from pathlib import Path

from hopper import normalize_cook_source

ROOT = Path(__file__).parent
SITE = ROOT / "_site"

parser = argparse.ArgumentParser()
parser.add_argument("--cook", default="cook")
args = parser.parse_args()

if SITE.exists():
    shutil.rmtree(SITE, onerror=lambda function, path, _: (
        os.chmod(path, stat.S_IWRITE), function(path)
    ))

# Build from a normalized copy so the curated catalogue is fixed without
# rewriting every source file. Newly imported recipes are normalized by the
# same helper in hopper.py before they reach this step.
BUILD_RECIPES = Path(tempfile.mkdtemp(prefix="build-recipes-", dir=ROOT))
atexit.register(shutil.rmtree, BUILD_RECIPES, ignore_errors=True)
shutil.copytree(ROOT / "recipes", BUILD_RECIPES, dirs_exist_ok=True)
for cook_path in BUILD_RECIPES.glob("*.cook"):
    source = cook_path.read_text(encoding="utf-8")
    cook_path.write_text(normalize_cook_source(source), encoding="utf-8")
subprocess.run([
    args.cook, "build", "web", "--base-path", str(BUILD_RECIPES),
    "--base-url", "/recipe-hopper/",
], cwd=ROOT, check=True)

css = (ROOT / "site.css").read_text(encoding="utf-8")
with (SITE / "static/css/custom-styles.css").open("a", encoding="utf-8") as output:
    output.write("\n" + css)
shutil.copy2(ROOT / "planner.html", SITE / "planner.html")
shutil.copy2(ROOT / "breakfast.html", SITE / "breakfast.html")
shutil.copy2(ROOT / "curriculum.js", SITE / "static/js/curriculum.js")
shutil.copy2(ROOT / "breakfast-data.js", SITE / "static/js/breakfast-data.js")

header = """
<header class="site-header print:hidden">
  <a class="site-brand" href="/recipe-hopper/">
    <span class="site-mark" aria-hidden="true">RH</span>
    <span><strong>Recipe Hopper</strong><small>32 weeks of Sunday cooking</small></span>
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
portion_panel = """
<section class="portion-panel print:hidden" id="portion-panel" aria-label="Recipe portions">
  <a class="portion-back" id="portion-back" href="/recipe-hopper/planner.html" hidden>← Back to weekly plan</a>
  <div>
    <p class="eyebrow">Serving reference</p>
    <strong id="portion-label">Sunday batch · 5 adult portions</strong>
    <small id="portion-context">Enough for one meal on five weekdays</small>
  </div>
  <div class="portion-actions" role="group" aria-label="Scale recipe">
    <button type="button" data-servings="1">1 portion · reference</button>
    <button type="button" data-servings="5">Sunday batch · 5</button>
  </div>
</section>
"""
portion_script = """
<script>
(() => {
  const dataNode = document.getElementById("cooking-mode-data");
  const portionDataNode = document.getElementById("portion-data");
  const panel = document.getElementById("portion-panel");
  if (!dataNode || !portionDataNode || !panel) return;
  const data = JSON.parse(dataNode.textContent);
  const portionIngredients = JSON.parse(portionDataNode.textContent);
  const portionAmounts = new Map();
  portionIngredients.forEach(ingredient => {
    const key = ingredient.name.toLowerCase();
    const amounts = portionAmounts.get(key) || [];
    amounts.push(ingredient.display);
    portionAmounts.set(key, amounts);
  });
  const ingredients = data.sections.flatMap(section => section.ingredients || []);
  const heading = [...document.querySelectorAll("h2")]
    .find(node => node.textContent.trim() === "Ingredients");
  const directions = [...document.querySelectorAll("h3")]
    .find(node => node.textContent.trim() === "Directions");
  if (directions) directions.textContent = "Directions · cook Sunday batch";
  const rows = [...(heading?.parentElement.querySelectorAll("ul li") || [])];
  const unspecified = name => /\bsalt\b/i.test(name)
    ? "to taste (start with 1/2 tsp)"
    : /\bpepper\b/i.test(name)
      ? "to taste (start with 1/4 tsp)"
    : /\b(?:cilantro|scallions?|parsley|basil)\b/i.test(name) && /optional/i.test(name)
      ? "for serving (about 1 tbsp per portion)"
      : /\b(?:oil|butter|spray)\b/i.test(name)
        ? "for cooking (about 1 tbsp)"
        : "see directions for amount";
  const batchAmounts = rows.map((row, index) =>
    row.lastElementChild.textContent.trim() || unspecified(ingredients[index]?.name || "")
  );
  const params = new URLSearchParams(location.search);
  const baseServings = 5;
  let servings = Number(params.get("servings")) === 1 ? 1 : baseServings;

  function renderPortions() {
    const occurrences = new Map();
    rows.forEach((row, index) => {
      if (!ingredients[index]) return;
      const key = ingredients[index].name.toLowerCase();
      const occurrence = occurrences.get(key) || 0;
      occurrences.set(key, occurrence + 1);
      row.lastElementChild.textContent = servings === 1
        ? portionAmounts.get(key)?.[occurrence] || unspecified(ingredients[index].name)
        : batchAmounts[index];
    });
    document.getElementById("portion-label").textContent = servings === 1
      ? "1 adult portion · reheat reference"
      : "Sunday batch · 5 adult portions";
    const day = params.get("day");
    const meal = params.get("meal");
    document.getElementById("portion-context").textContent = servings === 1 && day
      ? `${day} ${meal || "meal"} · reheat only; directions use Sunday batch`
      : servings === 1
        ? "Reference only; directions use Sunday batch"
        : "Enough for one meal on five weekdays";
    panel.querySelectorAll("[data-servings]").forEach(button => {
      const current = Number(button.dataset.servings) === servings;
      button.classList.toggle("is-current", current);
      button.setAttribute("aria-pressed", String(current));
    });
  }

  panel.querySelectorAll("[data-servings]").forEach(button =>
    button.addEventListener("click", () => {
      servings = Number(button.dataset.servings);
      params.set("servings", servings);
      history.replaceState(null, "", `${location.pathname}?${params}`);
      renderPortions();
    })
  );
  if (params.has("week")) {
    const week = Math.min(32, Math.max(1, Number(params.get("week")) || 1));
    const back = document.getElementById("portion-back");
    back.hidden = false;
    back.href = `/recipe-hopper/planner.html?week=${week}`;
    back.textContent = `← Back to Week ${week}`;
  }
  renderPortions();
})();
</script>
"""


def number_value(value):
    try:
        parts = str(value).strip().split()
        if not parts:
            return None
        return float(sum((Fraction(part) for part in parts), Fraction()))
    except (ValueError, ZeroDivisionError):
        return None


def parsed_value(value):
    if value is None:
        return None
    parts = re.split(r"\s*(?:-|to)\s*", str(value).replace("–", "-").replace("—", "-"))
    numbers = [number_value(part) for part in parts]
    return max(numbers) if len(numbers) <= 2 and all(item is not None for item in numbers) else None


def human_fraction(value):
    """Render a decimal amount as a compact kitchen fraction."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    fraction = Fraction(str(number)).limit_denominator(48)
    if abs(float(fraction) - number) > 0.02:
        return f"{number:.2f}".rstrip("0").rstrip(".")
    whole, remainder = divmod(fraction.numerator, fraction.denominator)
    if not remainder:
        return str(whole)
    part = f"{remainder}/{fraction.denominator}"
    return f"{whole} {part}" if whole else part


def kitchen_cups(value):
    """Render cups as common cup measures plus tablespoons/teaspoons."""
    total_teaspoons = max(0, round(float(value) * 48))
    whole, remainder = divmod(total_teaspoons, 48)
    common = {
        12: "1/4", 16: "1/3", 18: "3/8", 24: "1/2", 32: "2/3",
        36: "3/4", 40: "5/6", 42: "7/8",
    }
    if remainder in common:
        cup_text = f"{whole} {common[remainder]}" if whole else common[remainder]
        return f"{cup_text} cup{'s' if whole != 0 or remainder != 48 else ''}"
    parts = []
    if whole:
        parts.append(f"{whole} cup{'s' if whole != 1 else ''}")
    tablespoons, teaspoons = divmod(remainder, 3)
    if tablespoons:
        parts.append(f"{tablespoons} tbsp")
    if teaspoons:
        parts.append(f"{teaspoons} tsp")
    return " + ".join(parts) or "0 tsp"


def metric_amount(value, unit):
    unit = (unit or "").lower().rstrip(".")
    number = number_value(value)
    if number is None:
        return str(value), unit
    if unit in {"oz", "ounce", "ounces"}:
        number *= 28.3495
        unit = "g"
    elif unit in {"lb", "lbs", "pound", "pounds"}:
        number *= 453.592
        unit = "g"
    else:
        return str(value), unit
    amount = f"{number:.1f}".rstrip("0").rstrip(".") if number < 10 else str(int(number + 0.5))
    return amount, unit


def display_quantity(quantity):
    if not quantity:
        return "as needed"
    value = quantity["value"]
    if value["type"] == "text":
        amount = value["value"]
    else:
        number = value["value"]
        if number["type"] == "fraction":
            fraction = number["value"]
            whole, top, bottom = fraction["whole"], fraction["num"], fraction["den"]
            amount = " ".join(filter(None, (
                str(whole) if whole else "",
                f"{top}/{bottom}" if top else "",
            ))) or "0"
        else:
            amount = f'{number["value"]:.2f}'.rstrip("0").rstrip(".")
    unit = quantity.get("unit")
    if unit and unit.lower().rstrip(".") in {"oz", "ounce", "ounces", "lb", "lbs", "pound", "pounds"}:
        amount, unit = metric_amount(amount, unit)
    if unit in {"c", "cup", "cups"}:
        try:
            return kitchen_cups(number_value(amount))
        except (TypeError, ValueError):
            pass
    if unit not in {"c", "cup", "cups", "g", "kg", "ml", "l"}:
        amount = human_fraction(amount)
    if unit in {"g", "kg", "ml", "l"}:
        try:
            metric = float(amount)
            amount = f"{metric:.1f}".rstrip("0").rstrip(".") if metric < 10 else str(round(metric))
        except ValueError:
            pass
    return " ".join(filter(None, (amount, unit)))


def unspecified_amount(name):
    label = name.lower()
    if re.search(r"\bsalt\b", label):
        return "to taste (start with 1/2 tsp)"
    if re.search(r"\bpepper\b", label):
        return "to taste (start with 1/4 tsp)"
    if re.search(r"\b(?:cilantro|scallions?|parsley|basil)\b", label) and "optional" in label:
        return "for serving (about 1 tbsp per portion)"
    if re.search(r"\b(?:oil|butter|spray)\b", label):
        return "for cooking (about 1 tbsp)"
    return "see directions for amount"


def human_duration(match):
    prefix = match.group(1)
    hours, minutes, seconds = (int(value or 0) for value in match.groups()[1:])
    parts = []
    if hours:
        parts.append(f"{hours} hr")
    if minutes:
        parts.append(f"{minutes} min")
    if seconds and not parts:
        parts.append(f"{seconds} sec")
    return prefix + (" ".join(parts) or "0 min")


def humanize_static_ingredients(text):
    def row_amount(match):
        value = match.group(2).strip()
        unit = match.group(3)
        if unit and unit.lower().rstrip(".") in {"oz", "ounce", "ounces", "lb", "lbs", "pound", "pounds"}:
            value, unit = metric_amount(value, unit)
        elif unit in {"c", "cup", "cups"}:
            value = kitchen_cups(value)
            unit = None
        else:
            value = human_fraction(value)
        return f"{match.group(1)}{value}{f' {unit}' if unit else ''}{match.group(4)}"

    text = re.sub(
        r'(<span class="text-orange-700 font-semibold ml-2">\s*)'
        r'(\d+(?:\.\d+)?)(?:\s+([A-Za-z]+))?(\s*</span>)',
        row_amount,
        text,
    )
    return re.sub(
        r'(:\s*)(\d+(?:\.\d+)?)(?:\s+([A-Za-z]+))?(?=,?\s*</span>)',
        lambda match: (
            f"{match.group(1)}"
            f"{kitchen_cups(match.group(2)) if match.group(3) in {'c', 'cup', 'cups'} else metric_amount(match.group(2), match.group(3))[0] if match.group(3) and match.group(3).lower().rstrip('.') in {'oz', 'ounce', 'ounces', 'lb', 'lbs', 'pound', 'pounds'} else human_fraction(match.group(2))}"
            f"{'' if match.group(3) in {'c', 'cup', 'cups'} else f' {metric_amount(match.group(2), match.group(3))[1]}' if match.group(3) and match.group(3).lower().rstrip('.') in {'oz', 'ounce', 'ounces', 'lb', 'lbs', 'pound', 'pounds'} else f' {match.group(3)}' if match.group(3) else ''}"
        ),
        text,
    )


def humanize_ingredient_text(value):
    match = re.match(r"^\s*(\d+(?:\.\d+)?(?:\s+\d+/\d+)?)\s+([A-Za-z]+)\s+(.+)$", value)
    if not match:
        return value
    amount, unit, name = match.groups()
    normalized = unit.lower().rstrip(".")
    if normalized in {"oz", "ounce", "ounces", "lb", "lbs", "pound", "pounds"}:
        amount, unit = metric_amount(amount, unit)
    elif normalized in {"c", "cup", "cups"}:
        amount = kitchen_cups(amount)
        return f"{amount} {name}"
    else:
        amount = human_fraction(amount)
    return f"{amount} {unit} {name}"


def scaled_ingredients(path):
    result = subprocess.run(
        [args.cook, "recipe", str(path), "--format", "json", "--scale", "0.2"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return [
        {
            "name": ingredient["name"],
            "display": (
                display_quantity(ingredient.get("quantity"))
                if ingredient.get("quantity")
                else unspecified_amount(ingredient["name"])
            ),
        }
        for ingredient in json.loads(result.stdout)["ingredients"]
    ]


search_path = SITE / "static/search-index.json"
search_index = sorted(
    json.loads(search_path.read_text(encoding="utf-8")),
    key=lambda recipe: recipe["path"],
)
portion_by_path = {}
for recipe in search_index:
    page = SITE / recipe["path"]
    source = BUILD_RECIPES / f'{Path(recipe["path"]).stem}.cook'
    source_text = source.read_text(encoding="utf-8")
    yield_verified = bool(re.search(r"^yield_verified:\s*true\s*$", source_text, re.M | re.I))
    planner_ready = bool(re.search(r"^planner_ready:\s*true\s*$", source_text, re.M | re.I))
    if planner_ready and not yield_verified:
        raise ValueError(f"{source.name}: planner-ready recipes require a verified yield")
    text = page.read_text(encoding="utf-8")
    match = re.search(
        r'<script id="cooking-mode-data" type="application/json">\s*(.*?)\s*</script>',
        text,
        re.S,
    )
    data = json.loads(match.group(1))
    for section in data["sections"]:
        for ingredient in section.get("ingredients", []):
            quantity = ingredient.get("quantity")
            if isinstance(quantity, str) and re.fullmatch(r"\d+(?:\.\d+)?", quantity):
                if ingredient.get("unit") and ingredient["unit"].lower().rstrip(".") in {"oz", "ounce", "ounces", "lb", "lbs", "pound", "pounds"}:
                    ingredient["quantity"], ingredient["unit"] = metric_amount(quantity, ingredient["unit"])
                else:
                    ingredient["quantity"] = human_fraction(quantity)
        for step in section.get("steps", []):
            for ingredient in step.get("ingredients", []):
                quantity = ingredient.get("quantity")
                if isinstance(quantity, str) and re.fullmatch(r"\d+(?:\.\d+)?", quantity):
                    if ingredient.get("unit") and ingredient["unit"].lower().rstrip(".") in {"oz", "ounce", "ounces", "lb", "lbs", "pound", "pounds"}:
                        ingredient["quantity"], ingredient["unit"] = metric_amount(quantity, ingredient["unit"])
                    else:
                        ingredient["quantity"] = human_fraction(quantity)
    serialized_data = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    text = text[:match.start(1)] + serialized_data + text[match.end(1):]
    page.write_text(text, encoding="utf-8")
    details = [
        ingredient
        for section in data["sections"]
        for ingredient in section.get("ingredients", [])
    ]
    recipe["yieldVerified"] = yield_verified
    recipe["plannerReady"] = planner_ready
    if yield_verified:
        recipe["servings"] = 5
    recipe["ingredientDetails"] = [
        {
            "name": ingredient["name"],
            "value": parsed_value(ingredient.get("quantity")),
            "unit": ingredient.get("unit"),
        }
        for ingredient in details
    ]
    if planner_ready:
        portion_by_path[recipe["path"]] = scaled_ingredients(source)
planner_recipes = [recipe for recipe in search_index if recipe["plannerReady"]]
planner_stretch = [recipe for recipe in planner_recipes if "stretch" in recipe.get("tags", [])]
if len(planner_recipes) - len(planner_stretch) < 8 or len(planner_stretch) < 8:
    raise ValueError("planner needs at least eight approachable and eight stretch recipes")
(SITE / "static/planner-index.json").write_text(
    json.dumps(planner_recipes, ensure_ascii=False, separators=(",", ":")),
    encoding="utf-8",
)
search_path.write_text(
    json.dumps(
        [
            {
                key: value
                for key, value in recipe.items()
                if key not in {"yieldVerified", "plannerReady", "servings", "ingredientDetails"}
            }
            for recipe in search_index
        ],
        ensure_ascii=False,
        separators=(",", ":"),
    ),
    encoding="utf-8",
)
recipe_by_path = {recipe["path"]: recipe for recipe in search_index}

for page in SITE.rglob("*.html"):
    text = page.read_text(encoding="utf-8")
    schema_match = re.search(
        r'<script type="application/ld\+json">\s*(.*?)\s*</script>',
        text,
        re.S,
    )
    if schema_match:
        schema = json.loads(schema_match.group(1))
        if isinstance(schema.get("recipeIngredient"), list):
            schema["recipeIngredient"] = [
                humanize_ingredient_text(item) if isinstance(item, str) else item
                for item in schema["recipeIngredient"]
            ]
            serialized_schema = json.dumps(schema, ensure_ascii=False, separators=(",", ":"))
            text = text[:schema_match.start(1)] + serialized_schema + text[schema_match.end(1):]
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
        r"(Time:\s*)PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?\b",
        human_duration,
        text,
        flags=re.I,
    )
    text = humanize_static_ingredients(text)
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
    text = text.replace(">spaced-review</span>", ">Spaced practice</span>")
    text = re.sub(
        r">#skill-([a-z-]+)</span>",
        lambda match: f">Skill: {match.group(1).replace('-', ' ').title()}</span>",
        text,
    )
    text = text.replace(">#approachable</span>", ">Approachable</span>")
    text = text.replace(">#stretch</span>", ">Stretch recipe</span>")
    text = text.replace(">#spaced-review</span>", ">Spaced practice</span>")
    text = re.sub(
        r'(<span class="metadata-pill metadata-servings">).*?(5 servings</span>)',
        r"\1Base batch · \2",
        text,
    )
    text = text.replace("🥘 Ingredients", "Ingredients")
    text = text.replace("👤 ", "")
    recipe_path = f"recipe/{page.name}"
    if page.parent.name == "recipe" and recipe_path in recipe_by_path:
        text = text.replace(
            f'<span class="text-gray-900">{html.escape(page.stem)}</span>',
            f'<span class="text-gray-900">{html.escape(recipe_by_path[recipe_path]["title"])}</span>',
            1,
        )
    if page.parent.name == "recipe" and recipe_path in portion_by_path:
        portion_data = json.dumps(
            portion_by_path[recipe_path],
            ensure_ascii=False,
            separators=(",", ":"),
        ).replace("</", "<\\/")
        text = text.replace(
            '<div class="grid md:grid-cols-3 gap-8 mb-8">',
            portion_panel + '\n<div class="grid md:grid-cols-3 gap-8 mb-8">',
            1,
        )
        text = text.replace(
            '<script id="cooking-mode-data" type="application/json">',
            f'<script id="portion-data" type="application/json">{portion_data}</script>\n'
            '<script id="cooking-mode-data" type="application/json">',
            1,
        )
        text = text.replace("</body>", portion_script + "\n</body>")
    if page.name == "index.html":
        text = text.replace(
            '<script src="/recipe-hopper/static/js/search.js"></script>',
            "",
        )
        text = re.sub(
            r"<img(?![^>]*\bloading=)",
            '<img loading="lazy" decoding="async"',
            text,
        )
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
