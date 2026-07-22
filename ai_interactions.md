# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Agentic Workflow (SF8)

> Document your experience using an AI agent (e.g., Cursor Agent, Claude, Copilot) to make multi-step changes autonomously.

**What task did you give the agent?**

<!-- Describe the goal you asked the agent to accomplish -->

**Prompts used:**

<!-- Paste the key prompts you gave the agent -->

**What did the agent generate or change?**

<!-- List the files edited, code generated, or commands run -->

**What did you verify or fix manually?**

<!-- Describe anything the agent got wrong or that required human review -->

---

## Design Pattern (SF10)

> Document how AI helped you choose or implement a design pattern.

**Which design pattern did you use?**

The **Strategy pattern**. Ranking behavior is encapsulated in interchangeable
"strategy" functions that all share one contract —
`(user_prefs, song) -> (score, reasons)` — and the recommender picks one at
runtime without knowing how it works internally. Three modes are provided:
`mood-first`, `genre-first`, and `energy-similarity`.

**How did AI help you brainstorm or implement it?**

I started with a single hard-coded `prioritize` flag ("mood" vs "genre") baked
into the scoring function. I asked the AI how to support several distinct ranking
approaches (including one that ignores genre/mood and ranks purely by energy)
without turning `recommend_songs` into a tangle of `if mode == ...` branches.

- It identified that swappable algorithms behind a common interface is exactly
  the **Strategy pattern**, and that Python doesn't need formal classes for it —
  plain functions with a shared signature plus a name→function **registry
  (dict)** are idiomatic and lighter-weight.
- We discussed keeping the pattern **backward compatible**: `strategy=None`
  falls back to the original `score_song` behavior, so existing tests and callers
  are untouched.
- It suggested making the two existing behaviors (mood/genre priority) into
  strategies too, so the old `prioritize` toggle became just two of the modes,
  and the menu in `main.py` is generated directly from the registry — adding a
  mode never requires editing the menu code.

I reviewed and kept the design, then verified each mode produces a genuinely
different ranking and added tests for all three.

**How does the pattern appear in your final code?**

In [`src/recommender.py`](src/recommender.py):

- The strategy functions `mood_first_strategy`, `genre_first_strategy`, and
  `energy_similarity_strategy` (all sharing the `score_song` contract).
- The `RANKING_STRATEGIES` registry (name → function) and `resolve_strategy()`,
  which normalizes a name / callable / `None` into a scoring function.
- `recommend_songs(user_prefs, songs, k, strategy=...)` calls the resolved
  strategy and is otherwise mode-agnostic.

In [`src/main.py`](src/main.py), `ask_strategy()` builds its menu from
`RANKING_STRATEGIES` and passes the chosen name straight through to
`recommend_songs`, so the UI is decoupled from the set of modes.
