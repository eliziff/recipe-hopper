#!/usr/bin/env python3
"""Cache a random recipe assortment and convert Recipe JSON-LD to Cooklang."""

from __future__ import annotations

import argparse
import ast
import csv
import html
import io
import json
import random
import re
import shutil
import subprocess
import sys
import time
from fractions import Fraction
from pathlib import Path
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).parent
CACHE = ROOT / "_cache"
USER_AGENT = "Mozilla/5.0 (compatible; recipe-hopper/1.0)"
TARGET_SERVINGS = 5

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
    "Canadian Living": {
        "seeds": [
            "https://www.canadianliving.com/food/lunch-and-dinner/recipe/simple-broccoli-sausage-pasta",
            "https://www.canadianliving.com/food/lunch-and-dinner/recipe/one-pot-turkey-bean-pasta",
            "https://www.canadianliving.com/food/lunch-and-dinner/recipe/easy-oven-baked-crispy-tofu",
            "https://www.canadianliving.com/food/lunch-and-dinner/recipe/one-pot-pasta-e-fagioli",
        ],
    },
    "Good Food": {
        "seeds": [
            "https://www.bbcgoodfood.com/recipes/sausage-ragu",
            "https://www.bbcgoodfood.com/recipes/speedy-lentil-coconut-curry",
            "https://www.bbcgoodfood.com/recipes/spiced-chicken-skewers-chopped-salad-flatbreads",
            "https://www.bbcgoodfood.com/recipes/teriyaki-tofu",
        ],
    },
    "Budget Bytes": {
        "seeds": [
            "https://www.budgetbytes.com/one-pot-veggie-pasta/",
            "https://www.budgetbytes.com/sweet-and-spicy-glazed-chicken-thighs/",
            "https://www.budgetbytes.com/one-pot-roasted-red-pepper-pasta/",
            "https://www.budgetbytes.com/beef-taco-pasta/",
        ],
    },
}

GITHUB_COOKS = [
    {
        "title": "Kluski",
        "url": "https://github.com/justintout/recipes/blob/main/Food/Kluski.cook",
        "raw": "https://raw.githubusercontent.com/justintout/recipes/main/Food/Kluski.cook",
        "author": "Mary Gdovka",
    },
]

DATASET = {
    "url": "https://raw.githubusercontent.com/josephrmartinez/recipe-dataset/main/13k-recipes.csv",
    "source": "https://github.com/josephrmartinez/recipe-dataset",
    "site": "GitHub · josephrmartinez/recipe-dataset",
}

VERIFIED_COOKLANG_REPOSITORY = {
    "name": "GitHub · nicholaswilde/recipes",
    "url": "https://github.com/nicholaswilde/recipes",
    "license": "Apache-2.0",
}

CURRICULUM = {
    "Foolproof Pan Pizza": "dough-fermentation",
    "Chicken Pot Pie": "roux-making",
    "World's Best Lasagna": "layering-and-baking",
    "Chicken Parmesan": "breading-and-shallow-frying",
    "Speedy lentil coconut curry": "blooming-spices",
    "Sweet and Spicy Glazed Chicken Thighs": "pan-searing-and-glazing",
    "Sausage ragu": "building-and-reducing-a-ragu",
    "Gochujang Buttered Noodles": "emulsifying-a-pan-sauce",
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
    if any(marker in value for marker in ("Ã", "Â", "â€", "Å")):
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
        return [part for part in re.split(r"\s*•\s*", clean(value)) if part]
    steps = []
    for item in value or []:
        if isinstance(item, str):
            steps.append(clean(item))
        elif item.get("@type") == "HowToSection":
            steps.extend(flatten_steps(item.get("itemListElement")))
        else:
            steps.extend(flatten_steps(item.get("text") or item.get("name")))
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


def serving_scale(value) -> Fraction | None:
    text = clean(value).lower()
    if re.search(r"\d\s*(?:to|[-–—])\s*\d", text):
        return None
    match = re.search(r"(\d+(?:\.\d+)?)\s*(?:to|-)?\s*\d*(?:\.\d+)?\s*servings?", text)
    if not match:
        match = re.search(r"(\d+(?:\.\d+)?)", text)
    if not match:
        return None
    servings = Fraction(match.group(1))
    return Fraction(TARGET_SERVINGS, 1) / servings if servings else None


def scaled_quantity(value: str, factor: Fraction) -> str:
    fractions = {"¼": " 1/4", "½": " 1/2", "¾": " 3/4", "⅓": " 1/3",
                 "⅔": " 2/3", "⅛": " 1/8", "⅜": " 3/8", "⅝": " 5/8", "⅞": " 7/8"}
    normalized = value
    for symbol, replacement in fractions.items():
        normalized = normalized.replace(symbol, replacement)

    def amount(text: str):
        try:
            return sum((Fraction(part) for part in text.strip().split()), Fraction())
        except (ValueError, ZeroDivisionError):
            return None

    def display(number: Fraction) -> str:
        whole, remainder = divmod(number.numerator, number.denominator)
        if not remainder:
            return str(whole)
        fraction = f"{remainder}/{number.denominator}"
        return f"{whole} {fraction}" if whole else fraction

    range_match = re.fullmatch(r"(.+?)\s*(?:-|to)\s*(.+)", normalized)
    if range_match:
        low, high = map(amount, range_match.groups())
        if low is not None and high is not None:
            return f"{display(low * factor)}-{display(high * factor)}"
    parsed = amount(normalized)
    return display(parsed * factor) if parsed is not None else value


def cook_ingredient(value: str, factor: Fraction = Fraction(1)) -> str:
    value = clean(value).replace("@", "")
    amount = r"(?:\d+\s*[¼½¾⅓⅔⅛⅜⅝⅞]|\d+(?:\.\d+)?(?:\s+\d+/\d+)?|\d+/\d+|[¼½¾⅓⅔⅛⅜⅝⅞])"
    match = re.match(
        rf"^({amount}(?:\s*(?:-|–|—|to)\s*{amount})?)\s*(?:({UNITS})\b\.?)?\s+(.+)$",
        value,
        re.I,
    )
    if not match:
        return f"@{value}{{}}"
    quantity, unit, name = (clean(part) for part in match.groups())
    quantity = scaled_quantity(quantity.replace("–", "-").replace("—", "-"), factor)
    return f"@{name}{{{quantity}{'%' + unit if unit else ''}}}"


def self_check() -> None:
    assert serving_scale("4 servings") == Fraction(5, 4)
    assert serving_scale("4 to 6 servings") is None
    assert serving_scale(None) is None
    assert scaled_quantity("400", Fraction(5, 4)) == "500"
    assert scaled_quantity("1 1/2", Fraction(5, 4)) == "1 7/8"
    assert scaled_quantity("1/2", Fraction(5, 6)) == "5/12"
    assert cook_ingredient("2 to 3 cloves garlic", Fraction(5, 4)) == "@garlic{2 1/2-3 3/4%cloves}"
    assert cook_ingredient("1 Tbsp. lemon juice", Fraction(5, 4)) == "@lemon juice{1 1/4%Tbsp}"
    assert cook_ingredient("1½ lbs. chicken thighs", Fraction(5, 4)) == "@chicken thighs{1 7/8%lbs}"
    assert cook_ingredient("1 ½ tbsp butter") == "@butter{1 1/2%tbsp}"


def yaml(value) -> str:
    return json.dumps(clean(value), ensure_ascii=False)


def learning_tags(data: dict) -> list[str]:
    """Tag only the eight deliberate curriculum techniques."""
    title = clean(data.get("name"))
    if title in CURRICULUM:
        return ["stretch", f"skill-{CURRICULUM[title]}"]
    return ["approachable"]


def budget_score(data: dict) -> int:
    """Rough Edmonton cost/availability signal; lower is friendlier."""
    text = " ".join([clean(data.get("name")), *map(clean, data.get("recipeIngredient", []))]).lower()
    staples = ("bean", "lentil", "chickpea", "potato", "rice", "pasta", "egg",
               "cabbage", "carrot", "frozen", "canned", "chicken thigh", "ground ")
    costly = ("lamb", "tenderloin", "sashimi", "scallop", "prosciutto", "blue cheese",
              "truffle", "lobster", "salmon")
    return sum(word in text for word in costly) * 4 - sum(word in text for word in staples)


def is_meal(data: dict) -> bool:
    """Reject components and non-meals before they reach the weekly hopper."""
    title = clean(data.get("name")).lower()
    ingredients = " ".join(map(clean, data.get("recipeIngredient", []))).lower()
    blocked = (
        "sauce", "dressing", "dip", "hard-boiled egg", "roast potatoes",
        "cookie", "cake", "pancake", "custard", "crumb bar", "apple crisp",
        "banana bread", "pico de gallo", "salsa",
    )
    return "tofu" not in f"{title} {ingredients}" and not any(word in title for word in blocked)


def is_practical_dataset_meal(data: dict) -> bool:
    """Keep complete meals with ordinary Edmonton supermarket ingredients."""
    title = clean(data.get("name")).lower()
    ingredients = [clean(item) for item in data.get("recipeIngredient", [])]
    meal_markers = (
        "chicken", "turkey", "beef", "pork", "sausage", "fish", "shrimp",
        "lentil", "bean", "chickpea", "pasta", "lasagna", "stew", "soup",
        "curry", "chili", "risotto", "noodle", "casserole", "burger",
        "taco", "pizza",
    )
    text = f"{title} {' '.join(ingredients).lower()}"
    specialty = (
        "tofu", "octopus", "squid", "rabbit", "venison", "foie gras",
        "caviar", "truffle", "lobster", "scallop", "quail", "saffron",
        "veal", "duck", "lamb", "liver", "brandy", "bourbon", "sherry",
        "dry wine", "dry white wine", "dry red wine", "pinot noir",
        "chanterelle", "morel", "kurobuta",
        "rib roast", "tenderloin", "smoked salmon", "prosciutto",
        "sushi-grade", "goat shoulder", "nduja", "korean sesame leaves",
        "corona beans", "purple sweet potato", "baby artichokes", "halibut",
        "smoker", "swordfish", "cipolline", "dark rum", "grand marnier",
        "iranian lime", "standard bricks", "cinder block", "fresh curry leaves",
        "sturgeon", "nasturtium", "orvieto", "yellowtail", "kaffir lime",
        "quince", "shirataki", "shiritaki", "coconut aminos",
    )
    component_titles = (
        "stock", "broth", "jam", "pickle", "relish", "bread", "rolls",
        "stuffing", "amandine", "mashed potatoes", "crostini", "tartare",
        "breakfast", "onion rings", "apple \"pizza\"", "kong jaban",
        "marinated mixed beans", "green beans with shallots",
        "green beans with", "charred green beans", "stir-fried green beans",
        "sweet potato casserole", "fritters (panelle)", "kolaches",
        "sorbet", "bite-size", " bites", "wings", "croquettes", "fritters",
        "shrimp toasts", "baked beans", "green beans and peas", "refried",
        "marinated japanese eggplant", "turkey skin cracklings",
        "thanksgiving turkey", "holiday turkey", "tea-brined turkey",
        "chile-rubbed turkey", "turkey for twenty",
        "buttermilk fried shrimp", "coconut shrimp",
        "fava bean, radish, and corn salad",
        "buttermilk cabbage soup", "celery root soup", "chilled zucchini soup",
        "cool jade soup", "roasted squash, pear, and ginger soup",
        "golden beet soup", "porcini mushroom soup", "roasted asparagus soup",
        "roasted beet soup", "roasted peanut soup", "spinach and mint soup",
        "gefilte fish", "pot stickers", "thanksgiving",
        "herb-butter turkey", "roasted pepper turkey",
        "grilled turkey under a brick", "turkey tonnato",
        "simple smoked beef short ribs", "celery-root soup", "chicken satés",
        "sausage-stuffed rack of pork", "the cabbage soup diet",
        "watercress soup", "big-batch instant pot white beans", "celery soup",
        "ginger garlic green beans", "chocolate soup",
        "mixed beans with peanuts", "3-ingredient tomato soup",
        "carrot soup with star anise", "herbed bean salad",
        "lemongrass-ginger-carrot soup", "agave-glazed pork belly",
        "trail mix", "cheesy shrimp enchilada bake",
    )
    dessert_titles = (
        "cake", "cookie", "pie", "cobbler", "gelato", "ice cream", "rugelach",
        "whoopie", "brownie", "pudding", "scone", "bark", "wet nuts", "puff",
    )
    steps = flatten_steps(data.get("recipeInstructions"))
    oversized_turkey = any(
        "turkey" in ingredient.lower()
        and (
            re.search(
                r"\b(?:1\d|[2-9]\d)(?:\s*-\s*to\s*\d+)?\s*-?\s*(?:lb|pound)",
                ingredient,
                re.I,
            )
            or (
                "breasts" in ingredient.lower()
                and re.search(
                    r"\b(?:[3-9]|1\d)(?:\s*-\s*to\s*\d+)?\s*-?\s*(?:lb|pound)",
                    ingredient,
                    re.I,
                )
            )
        )
        for ingredient in ingredients
    )
    requires_liquor_store = any(
        re.search(
            r"\b(?:beer|stout|porter|tequila|triple sec|liqueur|vermouth|sak[eé]|"
            r"(?:white|red|rice)\s+wine)\b(?!\s+vinegar)",
            ingredient,
            re.I,
        )
        for ingredient in ingredients
    )
    missing_components = (
        "roasted winter vegetables", "big-batch marinated lentils",
        "ancho chile sauce", "semolina gnocchi", "whole-wheat pizza crust",
        "three-chile harissa", "chicken meatballs with ginger and miso",
        "chile-lime sauce", "tea-and-lemon gravy", "sticky rice",
        "red-curry peanut dipping sauce", "herb flower pesto",
        "pizza dough",
    )
    return (
        is_meal(data)
        and any(word in title for word in meal_markers)
        and not any(word in text for word in specialty)
        and not any(word in title for word in component_titles)
        and not any(word in title for word in dessert_titles)
        and not any(word in text for word in missing_components)
        and not any(re.search(r"\brecipe\b", ingredient, re.I) for ingredient in ingredients)
        and not oversized_turkey
        and not requires_liquor_store
        and budget_score(data) <= 1
        and 6 <= len(ingredients) <= 20
        and 3 <= len(steps) <= 15
    )


def make_cook(data: dict, source_name: str, url: str) -> tuple[str, str, str]:
    title = clean(data.get("name") or data.get("headline"))
    ingredients = [clean(item) for item in data.get("recipeIngredient", []) if clean(item)]
    steps = flatten_steps(data.get("recipeInstructions"))
    if not title or not ingredients or not steps:
        raise ValueError("recipe is missing a title, ingredients, or instructions")
    filename = slug(title)
    total_time = clean(data.get("totalTime") or data.get("cookTime") or data.get("prepTime"))
    factor = serving_scale(data.get("recipeYield"))
    yield_verified = factor is not None
    description = clean(data.get("description"))
    metadata = [
        "---",
        f"title: {yaml(title)}",
        *( [f"servings: {TARGET_SERVINGS}"] if yield_verified else [] ),
        f"yield_verified: {'true' if yield_verified else 'false'}",
        f"source: {yaml(url)}",
        f"author: {yaml(author(data.get('author')) or source_name)}",
        f"site: {yaml(source_name)}",
        f"tags: {json.dumps(learning_tags(data))}",
    ]
    if description:
        metadata.append(f"description: {yaml(description)}")
    if data.get("license"):
        metadata.append(f"license: {yaml(data['license'])}")
    metadata.extend(["---", ""])
    pantry = "\\\n".join(cook_ingredient(item, factor or Fraction(1)) for item in ingredients)
    details = f"Time: {total_time}" if total_time else ""
    notes = [f"> {details}", ""] if details else []
    body = metadata + notes + ["= Ingredients", "", pantry, "", "= Directions", ""]
    return filename, "\n".join(body) + "\n\n".join(steps) + "\n", image_url(data.get("image"))


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


def import_dataset(output: Path, count: int, rng: random.Random, refresh: bool) -> int:
    rows = list(csv.DictReader(io.StringIO(fetch(DATASET["url"], refresh))))
    rng.shuffle(rows)
    existing = {path.stem for path in output.glob("*.cook")}
    written = 0
    for row in rows:
        try:
            ingredients = ast.literal_eval(row["Ingredients"])
            data = {
                "name": row["Title"],
                "recipeIngredient": ingredients,
                "recipeInstructions": row["Instructions"].splitlines(),
                "author": DATASET["site"],
                "license": "CC BY-SA 3.0 (per dataset README)",
            }
            stem = slug(data["name"])
            if stem in existing or not is_practical_dataset_meal(data):
                continue
            stem, recipe, _ = make_cook(data, DATASET["site"], DATASET["source"])
            (output / f"{stem}.cook").write_text(recipe, encoding="utf-8")
            existing.add(stem)
            written += 1
            if written >= count:
                break
        except (SyntaxError, ValueError, TypeError):
            continue
    if written != count:
        raise RuntimeError(f"dataset yielded {written}/{count} practical recipes")
    print(f"{DATASET['site']}: {written} recipes")
    return written


def metadata_value(recipe: str, key: str) -> str:
    match = re.search(rf"^(?:>>\s*)?{re.escape(key)}:\s*(.+?)\s*$", recipe, re.M | re.I)
    return clean(match.group(1)).strip("\"'") if match else ""


def exact_servings(recipe: str) -> Fraction | None:
    value = metadata_value(recipe, "servings")
    match = re.fullmatch(r"(\d+(?:\.\d+)?)\s*(?:servings?)?", value, re.I)
    return Fraction(match.group(1)) if match else None


def verified_repository_dish(path: Path, recipe: str) -> bool:
    relative = path.as_posix().lower()
    title = metadata_value(recipe, "title") or path.stem
    meal_folder = any(folder in relative for folder in (
        "/main/", "/soups-and-stews/", "/mediterranean/",
    ))
    component_title = re.search(
        r"\b(sauce|dressing|marmalade|bread|rolls?|buns?|cookies?|cake|"
        r"dessert|salad|gazpacho)\b",
        title,
        re.I,
    )
    excluded_ingredient = re.search(
        r"\b(tofu|red wine|white wine|brandy|vodka|beer)\b",
        recipe,
        re.I,
    )
    return (
        meal_folder
        and exact_servings(recipe) is not None
        and not component_title
        and not excluded_ingredient
        and recipe.count("@") >= 5
    )


def import_verified_repository(
    output: Path,
    repository: Path,
    cook: str,
    count: int,
    rng: random.Random,
) -> int:
    candidates = []
    for path in repository.rglob("*.cook"):
        recipe = path.read_text(encoding="utf-8")
        if verified_repository_dish(path, recipe):
            candidates.append((path, recipe))
    rng.shuffle(candidates)
    written = 0
    for path, recipe in candidates:
        if written >= count:
            break
        title = metadata_value(recipe, "title") or path.stem
        servings = exact_servings(recipe)
        result = subprocess.run(
            [
                cook, "recipe", str(path), "--format", "cooklang",
                "--scale", str(float(Fraction(TARGET_SERVINGS, 1) / servings)),
            ],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        body = re.sub(
            r"\A---\s*\n.*?\n---\s*\n",
            "",
            result.stdout,
            count=1,
            flags=re.S,
        ).lstrip()
        body = body.replace(
            "@salt and @pepper",
            "@salt{} and @black pepper{}",
        ).replace(
            "@cilantro or @scallions (if using)",
            "@cilantro (optional){} or @scallions (optional){}",
        )
        relative = path.relative_to(repository).as_posix()
        blob_url = (
            f"{VERIFIED_COOKLANG_REPOSITORY['url']}/blob/main/"
            f"{quote(relative, safe='/')}"
        )
        metadata = [
            "---",
            f"title: {yaml(title)}",
            f"servings: {TARGET_SERVINGS}",
            "yield_verified: true",
            f"source: {yaml(metadata_value(recipe, 'source') or blob_url)}",
            f"repository: {yaml(blob_url)}",
            f"author: {yaml(metadata_value(recipe, 'author') or 'nicholaswilde/recipes contributors')}",
            f"site: {yaml(VERIFIED_COOKLANG_REPOSITORY['name'])}",
            f"tags: {json.dumps(learning_tags({'name': title}))}",
            f"license: {yaml(VERIFIED_COOKLANG_REPOSITORY['license'])}",
            "---",
            "",
        ]
        (output / f"{slug(title)}.cook").write_text(
            "\n".join(metadata) + body,
            encoding="utf-8",
        )
        print(f"{VERIFIED_COOKLANG_REPOSITORY['name']}: {title}")
        written += 1
    print(f"{VERIFIED_COOKLANG_REPOSITORY['name']}: {written} verified-yield dishes")
    return written


def refresh_existing_verified(output: Path, refresh: bool) -> int:
    written = 0
    for path in sorted(output.glob("*.cook")):
        recipe = path.read_text(encoding="utf-8")
        if metadata_value(recipe, "planner_ready").lower() == "true":
            print(f"Preserved curated planner recipe: {path.name}")
            continue
        site = metadata_value(recipe, "site")
        source = metadata_value(recipe, "source")
        if (
            "josephrmartinez/recipe-dataset" in source
            or "github.com/justintout/recipes" in source
        ):
            recipe = re.sub(r"^servings:\s*.+\n", "", recipe, count=1, flags=re.M)
            if "yield_verified:" not in recipe:
                recipe = re.sub(
                    r"(^title:\s*.+\n)",
                    r"\1yield_verified: false\n",
                    recipe,
                    count=1,
                    flags=re.M,
                )
            if path.stem == "kluski":
                recipe = re.sub(
                    r'^tags:\s*.+$',
                    'tags: ["approachable"]',
                    recipe,
                    count=1,
                    flags=re.M,
                )
            path.write_text(recipe, encoding="utf-8")
            continue
        if (
            not source.startswith("http")
            or site == VERIFIED_COOKLANG_REPOSITORY["name"]
        ):
            continue
        data = parse_recipe(fetch(source, refresh))
        _, converted, _ = make_cook(data, site or urlparse(source).netloc, source)
        if "yield_verified: true" not in converted:
            print(f"Unverified yield, left catalogue-only: {path.name}")
            continue
        path.write_text(converted, encoding="utf-8")
        print(f"Refreshed verified yield: {path.name}")
        written += 1
    return written


def main() -> int:
    self_check()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-source", type=int, default=4)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--replace", action="store_true", help="replace the flat collection")
    parser.add_argument("--github-count", type=int, default=283)
    parser.add_argument("--cook", default="cook")
    parser.add_argument("--refresh-existing-verified", action="store_true")
    parser.add_argument("--verified-repo", type=Path)
    parser.add_argument("--verified-count", type=int, default=20)
    args = parser.parse_args()
    rng = random.Random(args.seed)
    output = ROOT / "recipes"
    if args.refresh_existing_verified or args.verified_repo:
        output.mkdir(parents=True, exist_ok=True)
        written = 0
        if args.refresh_existing_verified:
            written += refresh_existing_verified(output, args.refresh)
        if args.verified_repo:
            written += import_verified_repository(
                output,
                args.verified_repo.resolve(),
                args.cook,
                args.verified_count,
                rng,
            )
        print(f"Verified recipe updates: {written}")
        return 0
    if args.replace and output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True, exist_ok=True)
    written = 0
    for source_name, config in SOURCES.items():
        pool = candidates(config, args.refresh)
        rng.shuffle(pool)
        parsed = []
        for url in pool:
            try:
                data = parse_recipe(fetch(url, args.refresh))
                if not is_meal(data):
                    raise ValueError("not a complete lunch or dinner dish")
                parsed.append((budget_score(data), url, data))
            except Exception as error:
                print(f"{source_name}: skipped {url}: {error}")
        parsed.sort(key=lambda item: item[0])
        source_written = 0
        for _, url, data in parsed:
            if source_written >= args.per_source:
                break
            try:
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
    for item in GITHUB_COOKS:
        try:
            data = {"name": item["title"]}
            metadata = "\n".join([
                "---",
                f"title: {yaml(item['title'])}",
                "yield_verified: false",
                f"source: {yaml(item['url'])}",
                f"author: {yaml(item['author'])}",
                'site: "GitHub · justintout/recipes"',
                f"tags: {json.dumps(learning_tags(data))}",
                "---",
                "",
            ])
            (output / f"{slug(item['title'])}.cook").write_text(
                metadata + fetch(item["raw"], args.refresh).strip() + "\n",
                encoding="utf-8",
            )
            print(f"GitHub · justintout/recipes: {item['title']}")
            written += 1
        except Exception as error:
            print(f"GitHub recipe skipped: {error}")
    written += import_dataset(output, args.github_count, rng, args.refresh)
    if not written:
        raise SystemExit("No recipes converted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
