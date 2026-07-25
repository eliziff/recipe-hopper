(() => {
  const base = [
    {meal: "Apple-cinnamon oatmeal", ingredients: [["rolled oats", .5, "cup"], ["milk", 1, "cup"], ["Apples", 1], ["cinnamon", .5, "tsp"]]},
    {meal: "Scrambled eggs & whole-grain toast", ingredients: [["Eggs", 3], ["whole-grain bread", 2, "slices"]]},
    null,
    {meal: "Greek yogurt, banana & oats", ingredients: [["Greek yogurt", 1, "cup"], ["Bananas", 1], ["rolled oats", .33, "cup"]]},
    {meal: "Egg & cheese breakfast wrap", ingredients: [["Eggs", 2], ["shredded cheddar", .25, "cup"], ["flour tortillas", 1]]},
    null,
    {meal: "Peanut-butter banana oatmeal", ingredients: [["rolled oats", .5, "cup"], ["milk", 1, "cup"], ["Bananas", 1], ["peanut butter", 2, "tbsp"]]}
  ];

  const plans = [
    {
      id: "berry-cocoa", name: "Berry + chocolate banana",
      first: {meal: "Berry-vanilla Whey smoothie + toast", ingredients: [["frozen mixed berries", 1, "cup"], ["whey protein powder", 1, "scoop"], ["milk", 1, "cup"], ["whole-grain bread", 2, "slices"]]},
      second: {meal: "Chocolate-banana Whey smoothie + toast", ingredients: [["Bananas", 1], ["cocoa powder", 1, "tbsp"], ["whey protein powder", 1, "scoop"], ["milk", 1, "cup"], ["whole-grain bread", 2, "slices"]]}
    },
    {
      id: "mango-mocha", name: "Mango ginger + mocha banana",
      first: {meal: "Mango-ginger Whey smoothie + toast", ingredients: [["frozen mango", 1, "cup"], ["fresh ginger", 1, "tsp"], ["whey protein powder", 1, "scoop"], ["milk", 1, "cup"], ["whole-grain bread", 2, "slices"]]},
      second: {meal: "Mocha-banana Whey smoothie + toast", ingredients: [["Bananas", 1], ["cocoa powder", 1, "tbsp"], ["instant coffee", 1, "tsp"], ["whey protein powder", 1, "scoop"], ["milk", 1, "cup"], ["whole-grain bread", 2, "slices"]]}
    },
    {
      id: "strawberry-peanut", name: "Strawberry oat + chocolate peanut",
      first: {meal: "Strawberry-oat Whey smoothie + toast", ingredients: [["frozen strawberries", 1, "cup"], ["rolled oats", .25, "cup"], ["whey protein powder", 1, "scoop"], ["milk", 1, "cup"], ["whole-grain bread", 2, "slices"]]},
      second: {meal: "Chocolate-peanut Whey smoothie + toast", ingredients: [["cocoa powder", 1, "tbsp"], ["peanut butter", 1, "tbsp"], ["Bananas", 1], ["whey protein powder", 1, "scoop"], ["milk", 1, "cup"], ["whole-grain bread", 2, "slices"]]}
    },
    {
      id: "blueberry-peach", name: "Blueberry cinnamon + peach vanilla",
      first: {meal: "Blueberry-cinnamon Whey smoothie + toast", ingredients: [["frozen blueberries", 1, "cup"], ["cinnamon", .5, "tsp"], ["whey protein powder", 1, "scoop"], ["milk", 1, "cup"], ["whole-grain bread", 2, "slices"]]},
      second: {meal: "Peach-vanilla Whey smoothie + toast", ingredients: [["frozen peaches", 1, "cup"], ["whey protein powder", 1, "scoop"], ["milk", 1, "cup"], ["whole-grain bread", 2, "slices"]]}
    },
    {
      id: "raspberry-banana", name: "Raspberry cocoa + banana cinnamon",
      first: {meal: "Raspberry-cocoa Whey smoothie + toast", ingredients: [["frozen raspberries", 1, "cup"], ["cocoa powder", 1, "tbsp"], ["whey protein powder", 1, "scoop"], ["milk", 1, "cup"], ["whole-grain bread", 2, "slices"]]},
      second: {meal: "Banana-cinnamon Whey smoothie + toast", ingredients: [["Bananas", 1], ["cinnamon", .5, "tsp"], ["whey protein powder", 1, "scoop"], ["milk", 1, "cup"], ["whole-grain bread", 2, "slices"]]}
    },
    {
      id: "pineapple-cherry", name: "Pineapple vanilla + cherry cocoa",
      first: {meal: "Pineapple-vanilla Whey smoothie + toast", ingredients: [["frozen pineapple", 1, "cup"], ["whey protein powder", 1, "scoop"], ["milk", 1, "cup"], ["whole-grain bread", 2, "slices"]]},
      second: {meal: "Cherry-cocoa Whey smoothie + toast", ingredients: [["frozen cherries", 1, "cup"], ["cocoa powder", 1, "tbsp"], ["whey protein powder", 1, "scoop"], ["milk", 1, "cup"], ["whole-grain bread", 2, "slices"]]}
    },
    {
      id: "mixed-berry-coffee", name: "Mixed berry oat + coffee vanilla",
      first: {meal: "Mixed-berry oat Whey smoothie + toast", ingredients: [["frozen mixed berries", 1, "cup"], ["rolled oats", .25, "cup"], ["whey protein powder", 1, "scoop"], ["milk", 1, "cup"], ["whole-grain bread", 2, "slices"]]},
      second: {meal: "Coffee-vanilla Whey smoothie + toast", ingredients: [["instant coffee", 1, "tsp"], ["whey protein powder", 1, "scoop"], ["milk", 1, "cup"], ["whole-grain bread", 2, "slices"]]}
    },
    {
      id: "apple-strawberry", name: "Apple cinnamon + strawberry cocoa",
      first: {meal: "Apple-cinnamon Whey smoothie + toast", ingredients: [["Apples", 1], ["cinnamon", .5, "tsp"], ["whey protein powder", 1, "scoop"], ["milk", 1, "cup"], ["whole-grain bread", 2, "slices"]]},
      second: {meal: "Strawberry-cocoa Whey smoothie + toast", ingredients: [["frozen strawberries", 1, "cup"], ["cocoa powder", 1, "tbsp"], ["whey protein powder", 1, "scoop"], ["milk", 1, "cup"], ["whole-grain bread", 2, "slices"]]}
    }
  ];

  const forPlan = plan => base.map((breakfast, index) =>
    index === 2 ? plan.first : index === 5 ? plan.second : breakfast
  );

  const method = breakfast => {
    if (breakfast.meal.includes("smoothie")) return "Blend the smoothie ingredients until smooth. Toast the bread and serve.";
    if (breakfast.meal.includes("oatmeal")) return "Simmer the oats and milk for 5 minutes. Stir in or top with the remaining ingredients.";
    if (breakfast.meal.includes("Scrambled")) return "Scramble the eggs over medium-low heat and serve with toast.";
    if (breakfast.meal.includes("wrap")) return "Scramble the eggs, add cheese, then roll everything in a warm tortilla.";
    return "Add everything to a bowl and serve.";
  };

  window.RECIPE_HOPPER_BREAKFASTS = Object.freeze({plans, forPlan, method});
})();
