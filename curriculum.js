(() => {
  const WEEK_COUNT = 32;
  const REVIEW_OFFSETS = Object.freeze([0, 1, 3, 7, 15]);
  const INTRODUCTION_WEEKS = Object.freeze([1, 3, 7, 12, 17]);

  const expandingWeeks = (start, gaps) => {
    let week = start;
    return [week, ...gaps.map(gap => (week += gap))];
  };
  const breakfastReviewWeeks = Object.freeze(expandingWeeks(1, [2, 4, 8, 16]));
  const breakfastPracticeForWeek = value => {
    const index = breakfastReviewWeeks.indexOf(Number(value));
    if (index < 0) return null;
    return {
      stage: index,
      previousWeek: breakfastReviewWeeks[index - 1] || null,
      nextWeek: breakfastReviewWeeks[index + 1] || null
    };
  };

  const buildPracticeSchedule = (repeatable, fillers) => {
    const weeks = Array(WEEK_COUNT).fill(null);
    const lastIntroduction = INTRODUCTION_WEEKS.at(-1);
    const tasks = repeatable.flatMap((recipe, recipeIndex) => {
      const introduced = INTRODUCTION_WEEKS[recipeIndex]
        || lastIntroduction + (recipeIndex - INTRODUCTION_WEEKS.length + 1) * 5;
      return REVIEW_OFFSETS.map((offset, stage) => ({
        due: introduced + offset,
        recipe,
        recipeIndex,
        stage
      }));
    }).sort((a, b) =>
      a.due - b.due || a.stage - b.stage || a.recipeIndex - b.recipeIndex
    );

    tasks.forEach(task => {
      const index = weeks.findIndex((slot, weekIndex) =>
        !slot && weekIndex + 1 >= task.due
      );
      if (index < 0) throw new Error(`No review slot remains for ${task.recipe.title}`);
      weeks[index] = {
        recipe: task.recipe,
        practice: {kind: "review", due: task.due, stage: task.stage}
      };
    });

    const unusedFillers = [...fillers];
    weeks.forEach((slot, index) => {
      if (slot) return;
      const recipe = unusedFillers.shift();
      if (!recipe) throw new Error("The 32-week curriculum needs more one-off dishes");
      weeks[index] = {
        recipe,
        practice: {
          kind: recipe.tags?.includes("stretch") ? "one-off" : "variety"
        }
      };
    });

    repeatable.forEach(recipe => {
      const appearances = weeks
        .map((slot, index) => slot.recipe.path === recipe.path ? index + 1 : 0)
        .filter(Boolean);
      appearances.forEach((week, index) => {
        const practice = weeks[week - 1].practice;
        practice.previousWeek = appearances[index - 1] || null;
        practice.nextWeek = appearances[index + 1] || null;
      });
    });
    return weeks;
  };

  const api = Object.freeze({
    WEEK_COUNT,
    REVIEW_OFFSETS,
    breakfastReviewWeeks,
    breakfastPracticeForWeek,
    buildPracticeSchedule
  });
  if (typeof window !== "undefined") window.RECIPE_HOPPER_CURRICULUM = api;
  if (typeof module !== "undefined") {
    module.exports = api;
    if (require.main === module) {
      const repeatable = Array.from({length: 5}, (_, index) => ({
        path: `review-${index}`,
        title: `Review ${index}`,
        tags: ["stretch", "spaced-review"]
      }));
      const fillers = Array.from({length: 7}, (_, index) => ({
        path: `filler-${index}`,
        title: `Filler ${index}`,
        tags: index < 3 ? ["stretch"] : ["approachable"]
      }));
      const schedule = buildPracticeSchedule(repeatable, fillers);
      const valid = schedule.length === WEEK_COUNT
        && schedule.every(Boolean)
        && repeatable.every(recipe =>
          schedule.filter(slot => slot.recipe.path === recipe.path).length === REVIEW_OFFSETS.length
        )
        && repeatable.every(recipe => {
          const weeks = schedule
            .map((slot, index) => slot.recipe.path === recipe.path ? index + 1 : 0)
            .filter(Boolean);
          const gaps = weeks.slice(1).map((week, index) => week - weeks[index]);
          return gaps.every((gap, index) => !index || gap >= gaps[index - 1]);
        })
        && new Set(schedule.map(slot => slot.recipe.path)).size === 12
        && breakfastPracticeForWeek(15).previousWeek === 7
        && breakfastPracticeForWeek(15).nextWeek === 31
        && breakfastPracticeForWeek(2) === null;
      if (!valid) throw new Error("Curriculum self-check failed");
      console.log("Validated 32 weeks, five spaced-review tracks, and seven one-off dishes.");
    }
  }
})();
