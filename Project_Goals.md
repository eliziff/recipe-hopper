# Recipe Hopper: Project Goals

## Objective

Build a simple, attractive Cooklang-based meal-planning site that turns a
large recipe collection into one practical weekly cooking routine.

## Weekly routine

- Show one explicitly selectable week at a time in a 32-week curriculum.
- Open on week 1 by default; do not derive the selected week from the calendar.
- Sunday is the only grocery and meal-prep day.
- Sunday lunch and dinner are takeout.
- Cook two recipes on Sunday: one five-portion lunch and one five-portion
  dinner.
- Eat those meals Monday through Friday; Saturday remains open.
- Let every weekday meal open its exact recipe at one adult portion while
  preserving a five-portion Sunday batch view.
- Prefer meals that hold well after cooking; refrigerate Monday and Tuesday
  portions and freeze Wednesday through Friday portions on Sunday.
- Alternate exactly two breakfasts across the seven days and make
  each one fresh that morning.
- Pair one Easy smoothie-and-toast breakfast with one Hard cooked breakfast;
  alternate them across the week.
- Include chickpea-and-olive shakshuka and revisit its egg-poaching technique
  on expanding cross-week intervals.
- Pair one easy recipe with the curriculum dinner. Revisit only explicitly
  tagged complex recipes and techniques; use one-off variety elsewhere.
- Generate the 32-week schedule, review stages, lunch pairing, and breakfast
  defaults programmatically.

## Recipe library

- Maintain the current 306 complete lunch or dinner dishes in a flat Cooklang
  collection.
- Keep the catalogue focused on lunch and dinner; manage breakfast
  through a small curated planner rotation.
- Exclude tofu, desserts, standalone sauces, sides, condiments, incomplete
  recipes, and specialty or impractically expensive dishes.
- Prefer ingredients available at ordinary Edmonton supermarkets and favour
  lower-cost staples.
- Require a traceable numeric source yield and quantity-consistent directions
  before a recipe can enter the planner; keep the rest available for browsing.
- Scale every planned recipe to five portions with CookCLI.
- Preserve the original source, author, and applicable licence metadata
  without organizing recipes by source.
- Ingest recipes through a reusable cached adapter from multiple recipe sites
  and suitable GitHub repositories.

## Grocery workflow

- Produce one combined, deduplicated grocery list for the two weekly recipes
  and all seven breakfasts.
- Show a measured quantity for every grocery item, summed from five lunches,
  five dinners, and seven one-person breakfasts.
- Choose lunch and dinner pairs programmatically to favour useful ingredient
  overlap while preserving scheduled technique reviews.
- Carry durable bulk ingredients into later weeks and pre-check them when the
  plan assumes stock remains.
- Group ingredients by grocery aisle.
- Persist checked items and allow the list to be copied or cleared.
- Assume salt, sugar, flour, bread flour, water, mayonnaise, black pepper, and
  cooking oils are already available.

## Product standards

- Keep the interface concise, aligned, responsive, and free of promotional
  filler.
- Use Tailwind CSS for the structural UI, with minimal custom styling.
- Make browsing 306 recipes fast through search, filters, and progressive
  disclosure.
- Do not expose recipe download buttons.
- Use Cooklang as the data backbone; do not use Nyum or Pandoc.

## Publishing

- Publish the static site through GitHub Pages from
  `eliziff/recipe-hopper`.
- Build and deploy on every push to `main` with a GitHub Actions workflow that
  downloads the latest official CookCLI Linux release.
- Never deploy this project to Alberta Law Review infrastructure.
