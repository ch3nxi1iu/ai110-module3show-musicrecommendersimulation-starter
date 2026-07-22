# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name

**VibeMatch 1.0** — a content-based music recommender that matches songs to a
listener's stated "taste profile."

---

## 2. Intended Use

VibeMatch generates a ranked list of song recommendations from a small fixed
catalog, based on preferences the user states directly (a target genre, mood,
and energy level, with optional valence and danceability).

- **What it generates:** the top-N songs that best fit the user's profile, each
  with a plain-text explanation of *why* it was picked.
- **Assumptions about the user:** the user can describe what they want right now
  as a small set of preferences. It does **not** assume any listening history,
  account, or knowledge of other users.
- **Who it's for:** classroom exploration of how content-based recommenders turn
  data into ranked predictions. It is **not** built for real users or production.

---

## 3. How the Model Works

Imagine you tell a friend three things: the *genre* you're in the mood for, the
*mood* you want, and how *energetic* you'd like the music. VibeMatch takes that
wish list and looks at every song in its catalog, giving each one a score for
how well it matches.

- **Genre and mood** are matched by name. An exact match earns full points; a
  *related* mood earns partial points (asking for "sad" still surfaces
  "melancholy" and "moody" songs, because the model knows those feelings are
  neighbors). Matching ignores capitalization, so "Chill" and "chill" are the
  same.
- **Energy, valence, and danceability** are numbers from 0 to 1, and the model
  rewards songs whose numbers are *close* to what you asked for.
- **Mood matters most**, then genre, then energy — that's the default priority,
  because people usually chase a feeling more than a label. The user can flip
  mood and genre priority when they run the app.

The model adds these up into one score per song, sorts the catalog from best to
worst, and hands back the top few along with a sentence explaining each pick.

**Changes from the starter logic:**
- Mood matching went from exact-only to **graded** (related moods get partial
  credit) so requests cluster onto close neighbors instead of scoring zero.
- Genre and mood matching are now **case-insensitive**.
- Only **mood, genre, and energy are required**; valence and danceability are
  optional and simply don't count if the user omits them.
- Every recommendation's explanation now shows the **exact points** each factor
  contributed, so the score is fully transparent.

---

## 4. Data

The catalog is a hand-built CSV, [`data/songs.csv`](data/songs.csv).

- **Size:** 28 songs.
- **Genres:** 25 distinct — afrobeat, ambient, bluegrass, blues, classical,
  country, disco, edm, folk, funk, gospel, hip hop, indie pop, jazz, k-pop,
  latin, lofi, metal, pop, punk, r&b, reggae, rock, synthwave, techno.
- **Moods:** 16 distinct — aggressive, angry, chill, euphoric, focused, happy,
  intense, laid-back, melancholy, moody, nostalgic, peaceful, relaxed, romantic,
  upbeat, uplifting.
- **Attributes per song:** `genre`, `mood`, `energy`, `tempo_bpm`, `valence`,
  `danceability`, `acousticness`. Scoring currently uses genre, mood, energy,
  valence, and danceability; `tempo_bpm` and `acousticness` are stored but not
  yet scored.
- **Changes made:** the catalog was expanded from 18 to 28 songs, deliberately
  adding one song each across 10 new genres (funk, gospel, blues, disco, techno,
  latin, punk, k-pop, afrobeat, bluegrass) to widen genre coverage.

**What's missing:** the dataset is tiny and every song is fictional. There is no
notion of popularity, release era, language, or lyrics, and no real listening
behavior. Whole regions of musical taste are represented by a single track.

---

## 5. Strengths

- **Transparent and explainable.** Every recommendation itemizes exactly how
  many points each factor contributed, and the points sum to the score — there
  is no black box.
- **Tolerant input.** Graded mood matching handles near-synonyms and typos
  (e.g. "sad" → melancholy), and case-insensitivity means capitalization never
  silently breaks a match.
- **Flexible profiles.** A user can specify as few as three preferences; omitted
  optional features don't distort the score.
- **Behaves intuitively on clean profiles.** A "High-Energy Pop" profile tops
  out on upbeat pop; "Chill Lofi" surfaces the lofi tracks; "Deep Intense Rock"
  ranks the rock/techno/intense songs first (see the README experiments).

---

## 6. Limitations and Bias

- **Content-only.** No collaborative filtering, listening history, or popularity
  signal — it can't learn "people like you also liked…"
- **Genre imbalance.** The catalog has 3 lofi and 2 pop songs but only **one**
  song for each of the other 23 genres. For those single-genre entries, the
  genre-match bonus almost never differentiates songs, so recommendations lean
  heavily on mood and energy instead.
- **Categorical weights swamp the numbers.** A mood+genre match is worth up to
  4.0 while all numeric closeness combined tops out at 2.5. So a song that
  matches genre and mood wins even when its energy/danceability are the
  *opposite* of what the user asked for (the "split brain" case in the README).
- **No input validation.** Out-of-range targets (e.g. `energy = 2.0`) aren't
  clamped and silently push scores negative; unknown genres and empty moods
  still return confident-looking results with no warning.
- **Hand-picked, static weights.** The 2.5 / 1.5 / 1.0 / 1.0 / 0.5 weights and
  the mood-similarity map are authored by hand, not learned from feedback, and
  encode the author's assumptions about what matters.
- **Unused signals.** `tempo_bpm` and `acousticness` are collected but ignored,
  so an "acoustic lover" preference can't actually be honored yet.

---

## 7. Evaluation

VibeMatch was checked with a mix of designed profiles and automated tests.

- **Profiles tested:** three clean baselines (High-Energy Pop, Chill Lofi, Deep
  Intense Rock) plus six adversarial edge cases (a mood absent from the catalog,
  a self-contradicting "split brain" profile, an out-of-range value, a
  mixed-case input, an invalid priority key, and an all-null profile). All are
  defined in [`src/profiles.py`](src/profiles.py) and runnable via
  `python -m src.main --demo`.
- **What we looked for:** whether each clean profile's top pick matched its
  intended genre+mood, and whether the edge cases failed gracefully.
- **What surprised us:** (1) the "sad" request — a mood no song carries — cleanly
  clustered onto the melancholy tracks once graded matching was added; (2) the
  "split brain" profile exposed that categorical matches structurally outweigh
  any numeric preference.
- **Automated tests:** 19 tests in [`tests/`](tests/) lock in baseline behavior,
  the mood clustering, case-insensitivity, and the optional-preference logic
  (`python -m pytest tests/ -q`).

---

## 8. Future Work

- **Learn the weights** from user feedback (likes/skips) instead of hand-tuning.
- **Validate and clamp inputs** so out-of-range or unknown values are caught.
- **Use `tempo_bpm` and `acousticness`** (after normalization) so preferences
  like "acoustic" or "high-tempo" can actually be honored.
- **Encourage diversity** in the top-N so a couple of lofi tracks can't dominate
  a chill query.
- **Derive mood similarity from data** (e.g. valence/energy vectors) instead of a
  hand-authored map, so it scales to new moods automatically.

---

## 9. Personal Reflection

Building VibeMatch made concrete how much of a recommender's "intelligence" lives
in the scoring rule and its weights, not in anything fancy. The most interesting
discovery was how a small design choice — making mood matching graded instead of
exact — turned a request the system couldn't answer at all ("sad", with no sad
songs) into a sensible one. It also made bias tangible: with 23 genres holding a
single song each, the model's genre signal is nearly useless for most of the
catalog, which is exactly the kind of imbalance that quietly shapes what real
platforms surface.
