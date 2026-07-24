# Recipe Hopper

A small, cached adapter that samples complete dishes from HelloFresh,
Serious Eats, Allrecipes, Good Food, Budget Bytes, and GitHub recipe
collections, then converts them into [Cooklang](https://cooklang.org/)
`.cook` files.

```sh
python hopper.py --per-source 4
python build_site.py
```

Fetched source pages are cached under `_cache/`. Re-run with `--refresh` to
replace the cache or `--seed NUMBER` to reproduce a particular sample.

The bulk GitHub adapter selects practical complete meals from
[`josephrmartinez/recipe-dataset`](https://github.com/josephrmartinez/recipe-dataset),
whose README identifies the recipe data as CC BY-SA 3.0. Each imported
Cooklang file retains the repository source and license metadata.

The GitHub Actions workflow builds the committed `.cook` files with the
official CookCLI and publishes the static result to GitHub Pages.
