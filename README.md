# 🎵 Music Recommender Simulation

## Project Summary

In this project you will build and explain a small music recommender system.

Your goal is to:

- Represent songs and a user "taste profile" as data
- Design a scoring rule that turns that data into recommendations
- Evaluate what your system gets right and wrong
- Reflect on how this mirrors real world AI recommenders

This version, **VibeMatch 1.0**, is a content-based recommender over a 28-song
catalog. A user states a taste profile — a target genre, mood, and energy level
(valence and danceability optional) — and the system scores every song, ranks
them, and returns the top picks with a plain-text explanation of each. It adds
graded mood matching (so "sad" still finds melancholy songs), case-insensitive
matching, and optional preferences on top of the starter's exact-match logic.
See [`model_card.md`](model_card.md) for the full write-up.

---

## How The System Works

### Real-world context
Real-world music platforms (Spotify, Apple Music, etc.) combine several techniques:
collaborative filtering (recommending what similar users liked), content-based
filtering (comparing the actual audio/metadata of songs), NLP on reviews and
playlist titles, and deep-learning embeddings that place songs and users in a
shared similarity space. They also factor in contextual signals like skips,
replays, and time of day.

This project implements a simplified version of **content-based filtering**
only — it doesn't use other users' listening data, just the attributes of
the songs themselves compared against what the current user is looking for.

### What features each `Song` uses in this system
Each song is represented by:
- `genre` — categorical, matched **case-insensitively** against the user's genre
- `mood` — categorical, matched **case-insensitively and *graded*** against the
  user's mood: an exact match earns full credit, and a *related* mood (e.g.
  `sad`↔`melancholy`) earns partial credit
- `energy` — numerical (0-1), how intense/active the track feels
- `valence` — numerical (0-1), how positive/upbeat vs. sad the track feels
- `danceability` — numerical (0-1), how suited the track is to dancing

`tempo_bpm` and `acousticness` are collected but not yet used in scoring —
left for a future version, since they need separate normalization before
they can be combined fairly with the other features.

### What information `UserProfile` stores
`UserProfile` (called `prefs` in the code) stores what the user wants right now
rather than an actual track. **Only `genre`, `mood`, and `energy` are required**;
`valence` and `danceability` are optional and are simply left out of the score
when the user doesn't provide them. This can come from explicit input (a mood
picker), from a seed song the user selects ("more like this"), or in a future
version, from averaging a user's recent listening history.

### How does your `Recommender` compute a score for each song

Each song is scored against the user's preferences with a weighted formula:

```python
score = 2.5 * mood_similarity(prefs.mood, song.mood)   # graded 0.0–1.0
      + 1.5 * (song.genre == prefs.genre)              # case-insensitive
      + 1.0 * (1 - abs(song.energy - prefs.energy))
      + 1.0 * (1 - abs(song.valence - prefs.valence))       # only if provided
      + 0.5 * (1 - abs(song.danceability - prefs.danceability))  # only if provided
```

**Mood is weighted higher than genre by default** (2.5 vs. 1.5) because mood
reflects what a listener is actually chasing emotionally, while genre is more
of a loose proxy — people frequently want the same mood across different
genres, but rarely want a specific genre in the wrong mood.

**Mood matching is graded, not all-or-nothing.** `mood_similarity` returns 1.0
for an exact match and a partial value for related moods (e.g. `sad`→`melancholy`
scores 0.9, `sad`→`moody` scores 0.7). This means a request for a mood the
catalog doesn't literally contain still clusters onto its closest neighbors
instead of scoring zero. Genre and mood matching are both case-insensitive.

Numerical features use `1 - abs(difference)` so closer values score higher. The
maximum score is **6.5** when all five preferences are given, or **5.0** for a
minimal profile (mood + genre + energy only), since the two optional terms are
dropped rather than defaulted when omitted.

These weights are hand-picked for this version — a future improvement would
be learning them from real user feedback (likes/skips) instead of guessing.

### Ranking modes (Strategy pattern)

The recommender supports multiple **ranking strategies**, and the user picks one
at runtime. Each strategy is a plain function with the same contract as
`score_song` — `(user_prefs, song) -> (score, reasons)` — registered by name in
`RANKING_STRATEGIES` in [`src/recommender.py`](src/recommender.py):

| Mode | What it does |
|------|--------------|
| `mood-first` | Weighted score with **mood** prioritized (2.5 vs. 1.5). The default. |
| `genre-first` | Same weighted score but **genre** prioritized (2.5 vs. 1.5). |
| `energy-similarity` | Ranks **purely by energy closeness**, ignoring genre and mood entirely. |

This is the **Strategy pattern**: `recommend_songs(prefs, songs, strategy=...)`
resolves the mode by name and stays agnostic about how any mode scores, so a new
mode is added by writing one function and registering it — no changes to
`recommend_songs` or `main.py`. When you run the app it prints the menu:

```
Ranking modes:
  1. mood-first
  2. genre-first
  3. energy-similarity
Choose a mode [1-3, default 1]:
```

The mode changes the results meaningfully. For the same `pop / happy` profile:
`genre-first` pushes a same-genre/different-mood track like *Gym Hero* up the
list (3.77 → 4.77) while *Rooftop Lights* drops (4.92 → 3.92); `energy-similarity`
throws out genre and mood entirely and tops out on whichever song is closest to
the target energy (*Groove Machine* at 0.80).

### How do you choose which songs to recommend

All songs are scored against the current `UserProfile`, sorted in descending
order by score, and the top N are returned. If preferences were derived from
a seed song, that song is excluded from its own recommendation list.

```python
ranked = sorted(scored_songs, key=lambda x: x.score, reverse=True)
recommendations = ranked[:n]
```

Ties are broken arbitrarily (by original dataset order) in this version.
---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python -m src.main
```

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.

---

## Sample Recommendation Output

A sample run of `python -m src.main`. The taste profile is
`genre=pop, mood=happy, energy=0.8, valence=0.8, danceability=0.75`, using the
`mood-first` ranking mode. Each recommendation shows its score and a breakdown of
reasons, where every reason is annotated with the exact points it contributed (the
points sum to the score):

```
Ranking modes:
  1. mood-first
  2. genre-first
  3. energy-similarity
Choose a mode [1-3, default 1]: 1
Ranking mode: mood-first

Favorite genre (e.g. pop, lofi, rock) [pop]: pop
Desired mood (e.g. happy, chill, intense) [happy]: happy
Target energy 0.0-1.0 [default 0.8]: 0.8
Target valence 0.0-1.0 [blank to skip]: 0.8
Target danceability 0.0-1.0 [blank to skip]: 0.75

Top 5 recommendations:

Sunrise City - Score: 6.42
Because: happy mood match (+2.50); pop genre match (+1.50); energy similarity (+0.98); valence similarity (+0.96); danceability similarity (+0.48)

Rooftop Lights - Score: 4.92
Because: happy mood match (+2.50); valence similarity (+0.99); energy similarity (+0.96); danceability similarity (+0.47)

Fiesta en la Playa - Score: 4.83
Because: happy mood match (+2.50); energy similarity (+0.98); valence similarity (+0.91); danceability similarity (+0.44)

Lagos Sunrise - Score: 4.82
Because: happy mood match (+2.50); valence similarity (+0.97); energy similarity (+0.92); danceability similarity (+0.43)

Groove Machine - Score: 4.66
Because: happy~upbeat mood match (+2.25); energy similarity (+1.00); valence similarity (+0.98); danceability similarity (+0.42)
```

Note the last pick, *Groove Machine* (mood `upbeat`): it earns partial mood
credit (`happy~upbeat`, +2.25 instead of +2.50) through the graded matching —
a `happy` request still surfaces its emotional neighbors.

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or demo video link here -->

---

## Experiments You Tried

All profiles below are defined in [`src/profiles.py`](src/profiles.py) and can be
reproduced with `python -m src.main --demo`.

### Three distinct user profiles

**1. High-Energy Pop** — `genre=pop, mood=happy, energy=0.90, valence=0.85, danceability=0.85`

```
6.38  Sunrise City (pop, happy)
      happy mood match (+2.50); pop genre match (+1.50); valence (+0.99); energy (+0.92); danceability (+0.47)
4.83  Fiesta en la Playa (latin, happy)
      happy mood match (+2.50); valence (+0.96); energy (+0.88); danceability (+0.49)
4.81  Rooftop Lights (indie pop, happy)
      happy mood match (+2.50); valence (+0.96); energy (+0.86); danceability (+0.48)
```

**2. Chill Lofi** — `genre=lofi, mood=chill, energy=0.40, valence=0.55, danceability=0.60`

```
6.46  Midnight Coding (lofi, chill)
      chill mood match (+2.50); lofi genre match (+1.50); valence (+0.99); energy (+0.98); danceability (+0.49)
6.39  Library Rain (lofi, chill)
      chill mood match (+2.50); lofi genre match (+1.50); valence (+0.95); energy (+0.95); danceability (+0.49)
5.21  Focus Flow (lofi, focused)
      lofi genre match (+1.50); chill~focused mood match (+1.25); energy (+1.00); valence (+0.96); danceability (+0.50)
```

**3. Deep Intense Rock** — `genre=rock, mood=intense, energy=0.90, valence=0.45, danceability=0.60`

```
6.43  Storm Runner (rock, intense)
      intense mood match (+2.50); rock genre match (+1.50); energy (+0.99); valence (+0.97); danceability (+0.47)
4.85  Warehouse Pulse (techno, intense)
      intense mood match (+2.50); energy (+1.00); valence (+0.97); danceability (+0.39)
4.51  Gym Hero (pop, intense)
      intense mood match (+2.50); energy (+0.97); valence (+0.68); danceability (+0.36)
```

### What the differences show

The three profiles clearly steer the output in different directions, which is the
core thing we wanted to verify:

- **The energy preference actually moves results.** The pop and rock profiles both
  ask for high energy and get high-energy tracks up top; the lofi profile asks for
  low energy (0.40) and returns the two calmest lofi songs (energy 0.42 and 0.35).
- **Genre acts as a tie-breaker within a mood, not a hard filter.** In the pop
  profile, *Sunrise City* wins outright because it matches genre **and** mood
  (+1.50 + 2.50), but the runners-up (*Fiesta en la Playa*, *Rooftop Lights*) are
  latin and indie-pop — they still rank high purely on the `happy` mood match. The
  system prefers the right *feeling* across genres over the right genre in the
  wrong feeling, exactly as the weighting intends.
- **Graded mood matching fills gaps.** In the lofi profile, *Focus Flow* (mood
  `focused`) reaches #3 with partial credit for `chill~focused` (+1.25) — a purely
  exact-match system would have scored its mood at zero.

### A minimal (3-preference) profile

Because valence and danceability are optional, a user can give just three
preferences — `genre=hip hop, mood=aggressive, energy=0.9`:

```
4.98  Concrete Kings (hip hop, aggressive)
      aggressive mood match (+2.50); hip hop genre match (+1.50); energy (+0.98)
3.20  Riot in Room 6 (punk, angry)
      aggressive~angry mood match (+2.25); energy (+0.95)
3.18  Iron Verdict (metal, angry)
      aggressive~angry mood match (+2.25); energy (+0.93)
```

The explanations shorten to only the factors the user cared about, and `angry`
songs surface as graded neighbors of `aggressive`.

### An adversarial profile: "split brain"

Asking for a calm genre/mood but maxed-out energy —
`genre=folk, mood=peaceful, energy=0.95, valence=0.90, danceability=0.95`:

```
5.25  Willow & Wren (folk, peaceful)
      peaceful mood match (+2.50); folk genre match (+1.50); valence (+0.70); energy (+0.35); danceability (+0.20)
```

*Willow & Wren* wins **despite** having energy 0.30 (the opposite of the requested
0.95). This exposed a real property of the design: the categorical weights (max
4.0) structurally outweigh all numeric closeness combined (max 2.5), so a
genre+mood match can never be beaten by numbers alone. Documented as a limitation
below and in the model card.

---

## Limitations and Risks

- **Tiny catalog (28 songs)** — every recommendation is drawn from a handful of
  fictional tracks, so results are illustrative, not useful.
- **Genre imbalance** — 3 lofi and 2 pop songs, but only **one** song for each of
  the other 23 genres. For those single-song genres the genre bonus can't
  differentiate anything, so mood and energy do all the work.
- **Categorical weights swamp the numbers** — a mood+genre match (max 4.0) always
  beats numeric closeness (max 2.5), so a self-contradicting profile is resolved
  in favor of the labels (the "split brain" experiment above).
- **No input validation** — out-of-range targets (e.g. `energy=2.0`) aren't
  clamped and silently push scores down; unknown genres and empty moods still
  return confident-looking results.
- **Content-only** — no listening history, popularity, or collaborative signal,
  and it doesn't understand lyrics or language.
- **Unused features** — `tempo_bpm` and `acousticness` are stored but not scored.

These are explored further in [`model_card.md`](model_card.md).

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Building this made concrete how much of a recommender's behavior lives in the
scoring rule and its weights rather than anything sophisticated. Turning data into
predictions here is just: represent each song and the user as comparable numbers
and labels, score how close they are, and sort. The single most impactful change I
made — grading mood matches instead of requiring exact ones — took a request the
system couldn't answer at all ("sad", when no song is labeled sad) and turned it
into a sensible list of melancholy tracks, which showed how much the *design* of
the similarity function shapes what users can even ask for.

It also made bias tangible. With 23 of 25 genres represented by a single song, the
genre signal is nearly useless for most of the catalog, and the categorical
weights mean a mood+genre match can override every numeric preference. In a real
system those same dynamics — uneven catalog coverage and hand-chosen weights that
quietly favor some signals over others — are exactly where unfairness creeps in,
deciding whose taste gets served well and whose gets flattened into the nearest
popular neighbor.



