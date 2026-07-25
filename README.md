# Recipe Hopper

Recipe Hopper is a static [Cooklang](https://cooklang.org/) recipe catalogue
and eight-week meal planner for one adult. It keeps 306 complete lunch and
dinner dishes in one flat collection, without grouping them by source.

A recipe can enter the planner only when its source provides a verifiable
yield and its directions have been checked against the scaled ingredient list.
Twenty-two catalogue entries have verified yields; 16 are currently curated
for the eight-week planner. CookCLI scales planned recipes to a five-portion
Sunday batch. The rest remain searchable and readable, but are not used for
quantity-driven plans.

## Weekly plan

- Sunday is the single grocery and prep day; lunch and dinner that day are
  takeout.
- Two batches provide five weekday lunches and five weekday dinners.
- Exactly two quick breakfasts—one Easy and one Hard—alternate across the seven
  days, are made fresh daily, and are shopped for on Sunday.
- Every meal card opens its exact recipe at the quantity needed for one adult.
- Pairing favours shared ingredients, while the second dish introduces the
  week's cooking technique.
- The grocery list sums and deduplicates recipe quantities by aisle. Durable
  bulk ingredients from earlier weeks are carried forward and pre-checked.
- Later-week portions are selected for freezer and reheating suitability.

## Build locally

Install [CookCLI](https://cooklang.org/cli/) and run:

```sh
python build_site.py --cook /path/to/cook
```

The generated site is written to `_site/`.

## Recipe adapters

`hopper.py` samples complete dishes from HelloFresh, Serious Eats, Allrecipes,
Good Food, Budget Bytes, and GitHub recipe repositories. Fetched pages are
cached under `_cache/`; use `--refresh` to replace the cache and `--seed` for a
repeatable sample.

```sh
python hopper.py --per-source 4 --seed 42
```

The bulk catalogue includes
[`josephrmartinez/recipe-dataset`](https://github.com/josephrmartinez/recipe-dataset)
(CC BY-SA 3.0), while verified-yield repository imports use
[`nicholaswilde/recipes`](https://github.com/nicholaswilde/recipes)
(Apache-2.0). Every imported `.cook` file retains its original source and, when
available, author and licence metadata. Yield-aware repository imports can be
added with `--verified-repo`; only recipes with numeric serving metadata become
eligible for the planner.

## Publish

Every push to `main` runs `.github/workflows/deploy.yml`. The workflow downloads
the latest official CookCLI Linux release, builds `_site/`, and deploys it to
GitHub Pages. Set the repository's Pages source to **GitHub Actions** once; the
workflow can then also be started manually from the Actions tab.
