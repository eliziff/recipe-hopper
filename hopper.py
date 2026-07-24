#!/usr/bin/env python3
"""Cache a random recipe assortment and convert Recipe JSON-LD to Cooklang."""

from __future__ import annotations

import argparse
import html
import json
import random
import re
import shutil
import sys
import time
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).parent
CACHE = ROOT / "_cache"
USER_AGENT = "Mozilla/5.0 (compatible; recipe-hopper/1.0)"

SOURCES = {
    "HelloFresh": {
        "index": "https://www.hellofresh.com/recipes",
        "pattern": r"https://www\.hellofresh\.com/recipes/[a-z0-9-]+-[0-9a-f]{24}",
        "seeds": [],
    },
    "Serious Eats": {
        "seeds": [
            "https://www.seriouseats.com/foolproof-pan-pizza-recipe",
            "https://www.seriouseats.com/the-best-roast-potatoes-ever-recipe",
            "https://www.seriouseats.com/halal-cart-style-chicken-and-rice-white-sauce-recipe",
            "https://www.seriouseats.com/easy-one-pot-no-knead-bread-recipe",
            "https://www.seriouseats.com/best-chili-recipe",
            "https://www.seriouseats.com/new-york-style-pizza-sauce",
            "https://www.seriouseats.com/perfect-boiled-eggs-recipe",
            "https://www.seriouseats.com/classic-pico-de-gallo-salsa-fresca-recipe",
        ],
    },
    "Allrecipes": {
        "index": "https://www.allrecipes.com/",
        "pattern": r"https://www\.allrecipes\.com/recipe/\d+/[a-z0-9-]+/?",
        "seeds": [
            "https://www.allrecipes.com/recipe/20144/banana-banana-bread/",
            "https://www.allrecipes.com/recipe/21014/good-old-fashioned-pancakes/",
            "https://www.allrecipes.com/recipe/10813/best-chocolate-chip-cookies/",
            "https://www.allrecipes.com/recipe/11679/homemade-mac-and-cheese/",
            "https://www.allrecipes.com/recipe/26317/chicken-pot-pie-ix/",
            "https://www.allrecipes.com/recipe/23600/worlds-best-lasagna/",
            "https://www.allrecipes.com/recipe/16354/easy-meatloaf/",
            "https://www.allrecipes.com/recipe/223042/chicken-parmesan/",
        ],
    },
}

UNITS = (
    "tablespoons?|tbsp|teaspoons?|tsp|cups?|ounces?|oz|pounds?|lbs?|grams?|g|"
    "kilograms?|kg|milliliters?|ml|liters?|l|cloves?|cans?|packages?|pinch(?:es)?|"
    "units?|slices?"
)


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:90] or "recipe"


def clean(value) -> str:
    value = html.unescape(re.sub(r"<[^>]+>", " ", str(value or "")))
    if any(marker in value for marker in ("â€", "Â", "â€¢", "â")):
        try:
            value = value.encode("latin-1").decode("utf-8")
        except UnicodeError:
            pass
    return re.sub(r"\s+", " ", value).strip()


def fetch(url: str, refresh: bool = False, binary: bool = False):
    CACHE.mkdir(exist_ok=True)
    path = CACHE / slug(urlparse(url).netloc + urlparse(url).path)
    if not refresh and path.exists() and not binary:
        return path.read_text(encoding="utf-8")
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"})
    with urlopen(request, timeout=45) as response:
        payload = response.read()
    if binary:
        return payload
    text = payload.decode("utf-8", "replace")
    path.write_text(text, encoding="utf-8")
    time.sleep(0.35)
    return text


def find_recipe(value):
    if isinstance(value, dict):
        kinds = value.get("@type", [])
        if kinds == "Recipe" or "Recipe" in (kinds if isinstance(kinds, list) else []):
            return value
        for child in value.values():
            result = find_recipe(child)
            if result:
                return result
    elif isinstance(value, list):
        for child in value:
            result = find_recipe(child)
            if result:
                return result
    return None


def parse_recipe(page: str):
    scripts = re.findall(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        page,
        re.I | re.S,
    )
    for script in scripts:
        try:
            result = find_recipe(json.loads(html.unescape(script)))
            if result:
                return result
        except json.JSONDecodeError:
            pass
    raise ValueError("no Recipe JSON-LD found")


def flatten_steps(value) -> list[str]:
    if isinstance(value, str):
        return [clean(value)]
    steps = []
    for item in value or []:
        if isinstance(item, str):
            steps.append(clean(item))
        elif item.get("@type") == "HowToSection":
            steps.extend(flatten_steps(item.get("itemListElement")))
        else:
            steps.append(clean(item.get("text") or item.get("name")))
    return [step for step in steps if step]


def author(value) -> str:
    if isinstance(value, list):
        return ", ".join(filter(None, map(author, value)))
    return clean(value.get("name")) if isinstance(value, dict) else clean(value)


def image_url(value) -> str:
    if isinstance(value, list):
        return image_url(value[0]) if value else ""
    if isinstance(value, dict):
        return value.get("url") or value.get("contentUrl") or ""
    return value if isinstance(value, str) else ""


def cook_ingredient(value: str) -> str:
    value = clean(value).replace("@", "")
    match = re.match(
        rf"^([\d¼½¾⅓⅔⅛⅜⅝⅞./–— -]+)\s*(?:({UNITS})\b)?\s+(.+)$",
        value,
        re.I,
    )
    if not match:
        return f"@{value}{{}}"
    quantity, unit, name = (clean(part) for part in match.groups())
    quantity = quantity.replace("–", "-").replace("—", "-")
    return f"@{name}{{{quantity}{'%' + unit if unit else ''}}}"


def yaml(value) -> str:
    return json.dumps(clean(value), ensure_ascii=False)


def make_cook(data: dict, source_name: str, url: str) -> tuple[str, str, str]:
    title = clean(data.get("name") or data.get("headline"))
    ingredients = [clean(item) for item in data.get("recipeIngredient", []) if clean(item)]
    steps = flatten_steps(data.get("recipeInstructions"))
    if not title or not ingredients or not steps:
        raise ValueError("recipe is missing a title, ingredients, or instructions")
    filename = slug(title)
    total_time = clean(data.get("totalTime") or data.get("cookTime") or data.get("prepTime"))
    servings = clean(data.get("recipeYield"))
    description = clean(data.get("description"))
    metadata = [
        "---",
        f"title: {yaml(title)}",
        f"source: {yaml(url)}",
        f"author: {yaml(author(data.get('author')) or source_name)}",
        f"site: {yaml(source_name)}",
    ]
    if description:
        metadata.append(f"description: {yaml(description)}")
    metadata.extend(["---", ""])
    pantry = "Gather " + ", ".join(cook_ingredient(item) for item in ingredients) + "."
    details = " · ".join(filter(None, (
        f"Servings: {servings}" if servings else "",
        f"Time: {total_time}" if total_time else "",
    )))
    notes = [f"> {details}", ""] if details else []
    return filename, "\n".join(metadata + notes + [pantry, ""] + steps) + "\n", image_url(data.get("image"))


def candidates(config: dict, refresh: bool) -> list[str]:
    urls = list(config.get("seeds", []))
    if config.get("index"):
        try:
            page = fetch(config["index"], refresh)
            urls.extend(re.findall(config["pattern"], page))
        except Exception as error:
            print(f"Index skipped: {error}")
    return sorted(set(urls))


def save_image(url: str, destination: Path, refresh: bool) -> None:
    if not url:
        return
    extension = Path(urlparse(url).path).suffix.lower()
    if extension not in {".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif"}:
        extension = ".jpg"
    target = destination.with_suffix(extension)
    if target.exists() and not refresh:
        return
    try:
        target.write_bytes(fetch(url, refresh, binary=True))
    except Exception as error:
        print(f"  image skipped: {error}")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-source", type=int, default=4)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    rng = random.Random(args.seed)
    written = 0
    for source_name, config in SOURCES.items():
        output = ROOT / "recipes" / slug(source_name)
        output.mkdir(parents=True, exist_ok=True)
        pool = candidates(config, args.refresh)
        rng.shuffle(pool)
        source_written = 0
        for url in pool:
            if source_written >= args.per_source:
                break
            try:
                data = parse_recipe(fetch(url, args.refresh))
                stem, recipe, picture = make_cook(data, source_name, url)
                path = output / f"{stem}.cook"
                path.write_text(recipe, encoding="utf-8")
                save_image(picture, output / stem, args.refresh)
                print(f"{source_name}: {data.get('name')}")
                source_written += 1
                written += 1
            except Exception as error:
                print(f"{source_name}: skipped {url}: {error}")
        if source_written < args.per_source:
            print(f"{source_name}: only {source_written}/{args.per_source} recipes converted")
    if not written:
        raise SystemExit("No recipes converted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
