# 🎵 Music Recommender Simulation

## Project Summary

In this project you will build and explain a small music recommender system.

Your goal is to:

- Represent songs and a user "taste profile" as data
- Design a scoring rule that turns that data into recommendations
- Evaluate what your system gets right and wrong
- Reflect on how this mirrors real world AI recommenders

Replace this paragraph with your own summary of what your version does.

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
- `genre` — categorical, matched exactly against the user's preferred genre
- `mood` — categorical, matched exactly against the user's preferred mood
- `energy` — numerical (0-1), how intense/active the track feels
- `valence` — numerical (0-1), how positive/upbeat vs. sad the track feels
- `danceability` — numerical (0-1), how suited the track is to dancing

`tempo_bpm` and `acousticness` are collected but not yet used in scoring —
left for a future version, since they need separate normalization before
they can be combined fairly with the other features.

### What information `UserProfile` stores
`UserProfile` (called `prefs` in the code) stores the same shape of data as
a `Song`, but representing what the user wants right now rather than an
actual track: a target `genre`, `mood`, `energy`, `valence`, and
`danceability`. This can come from explicit input (a mood picker), from a
seed song the user selects ("more like this"), or in a future version, from
averaging a user's recent listening history.

### How does your `Recommender` compute a score for each song

Each song is scored against the user's preferences with a weighted formula:

```python
score = 2.5 * (song.mood == prefs.mood)
      + 1.5 * (song.genre == prefs.genre)
      + 1.0 * (1 - abs(song.energy - prefs.energy))
      + 1.0 * (1 - abs(song.valence - prefs.valence))
      + 0.5 * (1 - abs(song.danceability - prefs.danceability))
```

**Mood is weighted higher than genre by default** (2.5 vs. 1.5) because mood
reflects what a listener is actually chasing emotionally, while genre is more
of a loose proxy — people frequently want the same mood across different
genres, but rarely want a specific genre in the wrong mood. Numerical features
use `1 - abs(difference)` so closer values score higher, capped between 0 and
1. The maximum possible score is 6.5.

**The user can swap the mood/genre priority at runtime.** When you run the app
it asks whether you prefer genre over mood or mood over genre, and assigns the
heavier weight (2.5) to whichever you choose (the other gets 1.5):

```
Do you prefer (g)enre over mood, or (m)ood over genre? [g/m]:
```

This is stored as `prefs["prioritize"]` (`"mood"` or `"genre"`) and read inside
`score_song`. For example, prioritizing genre pushes a same-genre/different-mood
track like *Gym Hero* up the list (3.77 → 4.77), while a same-mood/different-genre
track like *Rooftop Lights* drops (4.92 → 3.92). The key is optional — profiles
that omit it default to mood priority.

These weights are hand-picked for this version — a future improvement would
be learning them from real user feedback (likes/skips) instead of guessing.

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
`genre=pop, mood=happy, energy=0.8, valence=0.8, danceability=0.75`, with mood
prioritized. Each recommendation shows its score and a breakdown of reasons,
where every reason is annotated with the exact points it contributed (the
points sum to the score):

```
Do you prefer (g)enre over mood, or (m)ood over genre? [g/m]: m
Prioritizing mood (weight 2.5) over the other (weight 1.5).

Top 3 recommendations:

Sunrise City - Score: 6.42
Because: happy mood match (+2.50); pop genre match (+1.50); energy similarity (+0.98); valence similarity (+0.96); danceability similarity (+0.48)

Rooftop Lights - Score: 4.92
Because: happy mood match (+2.50); valence similarity (+0.99); energy similarity (+0.96); danceability similarity (+0.47)

Gym Hero - Score: 3.77
Because: pop genre match (+1.50); valence similarity (+0.97); energy similarity (+0.87); danceability similarity (+0.43)
```

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or demo video link here -->

---

## Experiments You Tried

Use this section to document the experiments you ran. For example:

- What happened when you changed the weight on genre from 2.0 to 0.5
- What happened when you added tempo or valence to the score
- How did your system behave for different types of users

---

## Limitations and Risks

Summarize some limitations of your recommender.

Examples:

- It only works on a tiny catalog
- It does not understand lyrics or language
- It might over favor one genre or mood

You will go deeper on this in your model card.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Write 1 to 2 paragraphs here about what you learned:

- about how recommenders turn data into predictions
- about where bias or unfairness could show up in systems like this



