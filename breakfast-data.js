(() => {
  const easy = (meal, ingredients) => ({
    difficulty: "Easy",
    meal,
    ingredients: [
      ...ingredients,
      ["whey protein powder", 1, "scoop"],
      ["milk", 1, "cup"],
      ["whole-grain bread", 2, "slices"]
    ]
  });
  const hard = (meal, ingredients) => ({difficulty: "Hard", meal, ingredients});

  const plans = [
    {
      id: "berry-cocoa", name: "Berry smoothie + scrambled eggs",
      first: easy("Berry-vanilla Whey smoothie + toast", [["frozen mixed berries", 1, "cup"]]),
      second: hard("Scrambled eggs & whole-grain toast", [["Eggs", 3], ["whole-grain bread", 2, "slices"]])
    },
    {
      id: "mango-mocha", name: "Mango smoothie + apple oatmeal",
      first: easy("Mango-ginger Whey smoothie + toast", [["frozen mango", 1, "cup"], ["fresh ginger", 1, "tsp"]]),
      second: hard("Apple-cinnamon oatmeal", [["rolled oats", .5, "cup"], ["milk", 1, "cup"], ["Apples", 1], ["cinnamon", .5, "tsp"]])
    },
    {
      id: "strawberry-peanut", name: "Strawberry smoothie + breakfast wrap",
      first: easy("Strawberry-oat Whey smoothie + toast", [["frozen strawberries", 1, "cup"], ["rolled oats", .25, "cup"]]),
      second: hard("Egg & cheese breakfast wrap", [["Eggs", 2], ["shredded cheddar", .25, "cup"], ["flour tortillas", 1]])
    },
    {
      id: "blueberry-peach", name: "Blueberry smoothie + spinach omelette",
      first: easy("Blueberry-cinnamon Whey smoothie + toast", [["frozen blueberries", 1, "cup"], ["cinnamon", .5, "tsp"]]),
      second: hard("Spinach-cheddar omelette + toast", [["Eggs", 3], ["Spinach", 1, "cup"], ["shredded cheddar", .25, "cup"], ["whole-grain bread", 2, "slices"]])
    },
    {
      id: "raspberry-banana", name: "Raspberry smoothie + peanut oatmeal",
      first: easy("Raspberry-cocoa Whey smoothie + toast", [["frozen raspberries", 1, "cup"], ["cocoa powder", 1, "tbsp"]]),
      second: hard("Peanut-butter banana oatmeal", [["rolled oats", .5, "cup"], ["milk", 1, "cup"], ["Bananas", 1], ["peanut butter", 2, "tbsp"]])
    },
    {
      id: "pineapple-cherry", name: "Pineapple smoothie + breakfast quesadilla",
      first: easy("Pineapple-vanilla Whey smoothie + toast", [["frozen pineapple", 1, "cup"]]),
      second: hard("Egg & cheese breakfast quesadilla", [["Eggs", 2], ["shredded cheddar", .25, "cup"], ["flour tortillas", 1], ["salsa", 2, "tbsp"]])
    },
    {
      id: "mixed-berry-coffee", name: "Mixed-berry smoothie + French toast",
      first: easy("Mixed-berry oat Whey smoothie + toast", [["frozen mixed berries", 1, "cup"], ["rolled oats", .25, "cup"]]),
      second: hard("Banana-cinnamon French toast", [["Eggs", 2], ["milk", .25, "cup"], ["whole-grain bread", 2, "slices"], ["Bananas", 1], ["cinnamon", .25, "tsp"]])
    },
    {
      id: "apple-strawberry", name: "Apple smoothie + mushroom eggs",
      first: easy("Apple-cinnamon Whey smoothie + toast", [["Apples", 1], ["cinnamon", .5, "tsp"]]),
      second: hard("Mushroom-cheddar scrambled eggs + toast", [["Eggs", 3], ["mixed mushrooms", 1, "cup"], ["shredded cheddar", .25, "cup"], ["whole-grain bread", 2, "slices"]])
    }
  ];

  const forPlan = plan => Array.from(
    {length: 7},
    (_, index) => index % 2 ? plan.second : plan.first
  );

  const method = breakfast => {
    if (breakfast.meal.includes("smoothie")) return "Blend the smoothie ingredients until smooth. Toast the bread and serve.";
    if (breakfast.meal.includes("oatmeal")) return "Simmer the oats and milk for 5 minutes. Stir in or top with the remaining ingredients.";
    if (breakfast.meal.includes("omelette")) return "Wilt the spinach in a lightly oiled pan. Add beaten eggs, scatter over the cheese, fold when nearly set, and serve with toast.";
    if (breakfast.meal.includes("quesadilla")) return "Soft-scramble the eggs. Fill the tortilla with eggs and cheese, fold, and toast both sides in the pan. Serve with salsa.";
    if (breakfast.meal.includes("French toast")) return "Whisk the eggs, milk, and cinnamon. Dip the bread, cook both sides in a lightly oiled pan, and serve with sliced banana.";
    if (breakfast.meal.includes("Mushroom")) return "Brown the mushrooms in a lightly oiled pan. Add the eggs, scramble gently, finish with cheese, and serve with toast.";
    if (breakfast.meal.includes("Scrambled")) return "Scramble the eggs over medium-low heat and serve with toast.";
    if (breakfast.meal.includes("wrap")) return "Scramble the eggs, add cheese, then roll everything in a warm tortilla.";
    return "Add everything to a bowl and serve.";
  };

  window.RECIPE_HOPPER_BREAKFASTS = Object.freeze({plans, forPlan, method});
})();
