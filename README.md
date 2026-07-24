# Recipe Hopper

A small, cached adapter that samples recipes from HelloFresh, Serious Eats,
and Allrecipes and converts their Recipe Schema.org data into
[Cooklang](https://cooklang.org/) `.cook` files.

```sh
python hopper.py --per-source 4
cook build web --base-url /recipe-hopper/
```

Fetched source pages are cached under `_cache/`. Re-run with `--refresh` to
replace the cache or `--seed NUMBER` to reproduce a particular sample.

The GitHub Actions workflow builds the committed `.cook` files with the
official CookCLI and publishes the static result to GitHub Pages.

