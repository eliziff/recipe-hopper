# Recipe Hopper: Project Goals

## Objective

Build a simple, attractive Cooklang-based meal-planning site that turns a
large recipe collection into one practical weekly cooking routine.

## Weekly routine

- Show one explicitly selectable week at a time in an eight-week cycle.
- Open on week 1 by default; do not derive the selected week from the calendar.
- Sunday is the only grocery and meal-prep day.
- Sunday lunch and dinner are takeout.
- Cook two recipes on Sunday: one five-portion lunch and one five-portion
  dinner.
- Eat those meals Monday through Friday; Saturday remains open.
- Make one quick, easy breakfast fresh every day.
- Include two distinct Whey-protein smoothie components in each week.
- Pair one easy recipe with one skill-building recipe and introduce one
  deliberate cooking technique each week.

## Recipe library

- Maintain 300 complete lunch or dinner dishes in a flat Cooklang collection.
- Keep the 300-recipe catalogue focused on lunch and dinner; manage breakfast
  through a small curated planner rotation.
- Exclude tofu, desserts, standalone sauces, sides, condiments, incomplete
  recipes, and specialty or impractically expensive dishes.
- Prefer ingredients available at ordinary Edmonton supermarkets and favour
  lower-cost staples.
- Normalize every recipe to five portions.
- Preserve the original source, author, and applicable licence metadata
  without organizing recipes by source.
- Ingest recipes through a reusable cached adapter from multiple recipe sites
  and suitable GitHub repositories.

## Grocery workflow

- Produce one combined, deduplicated grocery list for the two weekly recipes
  and all seven breakfasts.
- Group ingredients by grocery aisle.
- Persist checked items and allow the list to be copied or cleared.
- Assume salt, sugar, flour, bread flour, water, mayonnaise, black pepper, and
  cooking oils are already available.

## Product standards

- Keep the interface concise, aligned, responsive, and free of promotional
  filler.
- Use Tailwind CSS for the structural UI, with minimal custom styling.
- Make browsing 300 recipes fast through search, filters, and progressive
  disclosure.
- Do not expose recipe download buttons.
- Use Cooklang as the data backbone; do not use Nyum or Pandoc.

## Publishing

- Publish the static site through GitHub Pages from
  `eliziff/recipe-hopper`.
- Never deploy this project to Alberta Law Review infrastructure.
