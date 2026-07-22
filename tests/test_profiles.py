"""
Characterization tests for the baseline and adversarial profiles.

These lock in the *current* behavior of the functional scoring path
(recommender.score_song / recommend_songs). The adversarial tests document
known failure modes -- if the scoring logic is later hardened (input
validation, case-folding, clamping), these are the tests to revisit.
"""

import os

import pytest

from src.recommender import (
    load_songs,
    recommend_songs,
    score_song,
    mood_similarity,
    RANKING_STRATEGIES,
    resolve_strategy,
)
from src.profiles import BASELINE_PROFILES, ADVERSARIAL_PROFILES

CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "songs.csv")


@pytest.fixture(scope="module")
def songs():
    return load_songs(CSV_PATH)


def top(prefs, songs, k=3):
    return recommend_songs(prefs, songs, k=k)


# --- baseline: happy path returns the intended genre + mood ---------------
@pytest.mark.parametrize(
    "name, genre, mood",
    [
        ("High-Energy Pop", "pop", "happy"),
        ("Chill Lofi", "lofi", "chill"),
        ("Deep Intense Rock", "rock", "intense"),
    ],
)
def test_baseline_top_pick_matches_profile(songs, name, genre, mood):
    best_song, _score, _why = top(BASELINE_PROFILES[name], songs)[0]
    assert best_song["genre"] == genre
    assert best_song["mood"] == mood


# --- adversarial characterization: current (surprising) behavior ----------
def test_ghost_mood_has_no_literal_sad_song(songs):
    """No song carries the 'sad' label -- clustering, not equality, does the work."""
    prefs, _note = ADVERSARIAL_PROFILES["Ghost mood"]
    results = top(prefs, songs)
    assert all(song["mood"] != "sad" for song, _s, _w in results)


# --- graded mood clustering (option 1) ------------------------------------
def test_mood_similarity_is_graded_and_symmetric():
    assert mood_similarity("sad", "sad") == 1.0                       # exact
    assert mood_similarity("sad", "melancholy") == 0.9               # neighbor
    assert mood_similarity("melancholy", "sad") == 0.9              # symmetric
    assert mood_similarity("sad", "happy") == 0.0                    # unrelated
    # closer neighbor beats farther neighbor
    assert mood_similarity("sad", "melancholy") > mood_similarity("sad", "moody")


def test_sad_profile_clusters_onto_melancholy(songs):
    """A 'sad' request now surfaces a melancholy song via partial mood credit."""
    prefs, _note = ADVERSARIAL_PROFILES["Ghost mood"]  # favorite_mood="sad"
    best_song, _score, why = top(prefs, songs)[0]
    assert best_song["mood"] == "melancholy"
    assert "sad~melancholy mood match" in why  # explanation shows the clustering


def test_mood_similarity_is_case_insensitive():
    """'Chill'/'CHILL' match 'chill'; neighbor credit ignores case too."""
    assert mood_similarity("Chill", "chill") == 1.0
    assert mood_similarity("CHILL", "chill") == 1.0
    assert mood_similarity("SAD", "Melancholy") == 0.9


def test_only_mood_genre_energy_are_required(songs):
    """A 3-key profile (no valence/danceability) scores without error."""
    prefs = dict(favorite_genre="pop", favorite_mood="happy", target_energy=0.9)
    results = top(prefs, songs)
    assert len(results) == 3
    # Neither optional term should appear in the explanation.
    _song, _score, why = results[0]
    assert "valence" not in why and "danceability" not in why


def test_missing_required_key_still_raises(songs):
    """Dropping a required key (energy) is still a hard error."""
    prefs = dict(favorite_genre="pop", favorite_mood="happy")
    with pytest.raises(KeyError):
        recommend_songs(prefs, songs)


def test_optional_valence_changes_score_when_provided(songs):
    """Adding a valence target contributes points a bare profile doesn't have."""
    bare = dict(favorite_genre="pop", favorite_mood="happy", target_energy=0.9)
    withval = dict(bare, target_valence=0.85)
    best_bare = score_song(bare, [s for s in songs if s["title"] == "Sunrise City"][0])[0]
    best_val = score_song(withval, [s for s in songs if s["title"] == "Sunrise City"][0])[0]
    assert best_val > best_bare  # the extra valence-similarity term adds points


def test_genre_match_is_case_insensitive(songs):
    """'LoFi'/'LOFI' earn the same genre credit as 'lofi'."""
    base = dict(favorite_genre="lofi", favorite_mood="chill",
                target_energy=0.40, target_valence=0.55, target_danceability=0.60)
    ranked = lambda g: [(s["id"], round(score, 6))
                        for s, score, _w in top(dict(base, favorite_genre=g), songs)]
    assert ranked("LoFi") == ranked("lofi")
    assert ranked("LOFI") == ranked("lofi")


def test_split_brain_categorical_beats_contradicting_numeric(songs):
    """Calm folk/peaceful song wins despite max energy/danceability request."""
    prefs, _note = ADVERSARIAL_PROFILES["Split brain"]
    best_song, _score, _why = top(prefs, songs)[0]
    assert best_song["genre"] == "folk" and best_song["mood"] == "peaceful"
    # ...even though its energy is the opposite of what was asked for.
    assert best_song["energy"] < prefs["target_energy"] - 0.5


def test_categorical_weight_ceiling_exceeds_numeric_ceiling():
    """Structural cause of 'split brain': 4.0 categorical vs 2.5 numeric max."""
    perfect = {
        "id": 0, "title": "", "artist": "", "genre": "pop", "mood": "happy",
        "energy": 0.5, "tempo_bpm": 100, "valence": 0.5,
        "danceability": 0.5, "acousticness": 0.5,
    }
    prefs = dict(favorite_genre="pop", favorite_mood="happy",
                 target_energy=0.5, target_valence=0.5, target_danceability=0.5)
    score, _reasons = score_song(prefs, perfect)
    categorical_max = 2.5 + 1.5
    numeric_max = 1.0 + 1.0 + 0.5
    assert categorical_max > numeric_max
    assert score == pytest.approx(categorical_max + numeric_max)


def test_out_of_range_energy_produces_negative_similarity(songs):
    """target_energy=2.0 is never clamped -> energy term goes negative."""
    prefs, _note = ADVERSARIAL_PROFILES["Out of range"]
    inflated, _score, _why = top(prefs, songs)[0]
    # Same song, valid target: scores strictly higher (no negative penalty).
    valid = dict(prefs, target_energy=inflated["energy"])
    assert score_song(prefs, inflated)[0] < score_song(valid, inflated)[0]


def test_case_mismatch_now_matches_mood(songs):
    """Mood matching is case-insensitive: 'Chill' ranks and scores like 'chill'
    (only the explanation label echoes the original casing)."""
    bad, _note = ADVERSARIAL_PROFILES["Case mismatch"]
    good = dict(bad, favorite_mood="chill")
    ranked = lambda prefs: [(s["id"], round(score, 6)) for s, score, _w in top(prefs, songs)]
    assert ranked(bad) == ranked(good)


def test_bad_priority_key_falls_back_to_mood(songs):
    """prioritize='valence' is invalid and silently behaves like the default."""
    bad, _note = ADVERSARIAL_PROFILES["Bad priority key"]
    default = {k: v for k, v in bad.items() if k != "prioritize"}
    assert top(bad, songs) == top(default, songs)


def test_null_profile_still_returns_results(songs):
    """Nonsense profile never errors and always ranks something."""
    prefs, _note = ADVERSARIAL_PROFILES["Null profile"]
    results = top(prefs, songs)
    assert len(results) == 3


# --- ranking strategies / modes (Strategy pattern) ------------------------
POP_HAPPY = dict(favorite_genre="pop", favorite_mood="happy",
                 target_energy=0.8, target_valence=0.8, target_danceability=0.75)


def test_three_ranking_modes_are_registered():
    assert set(RANKING_STRATEGIES) >= {"mood-first", "genre-first", "energy-similarity"}


def test_default_strategy_matches_mood_first(songs):
    """strategy=None keeps score_song's default (mood) priority."""
    default = [(s["id"], round(sc, 6)) for s, sc, _ in recommend_songs(POP_HAPPY, songs)]
    mood = [(s["id"], round(sc, 6))
            for s, sc, _ in recommend_songs(POP_HAPPY, songs, strategy="mood-first")]
    assert default == mood


def test_genre_first_differs_from_mood_first(songs):
    """Swapping the mode changes the ranking for a genre/mood-split catalog."""
    mood = [s["id"] for s, _sc, _w in recommend_songs(POP_HAPPY, songs, strategy="mood-first")]
    genre = [s["id"] for s, _sc, _w in recommend_songs(POP_HAPPY, songs, strategy="genre-first")]
    assert mood != genre


def test_energy_similarity_ignores_genre_and_mood(songs):
    """Energy mode ranks purely by energy closeness; top pick is nearest energy."""
    prefs = dict(target_energy=0.80)  # no genre/mood needed for this mode
    ranked = recommend_songs(prefs, songs, k=5, strategy="energy-similarity")
    best_song, best_score, _why = ranked[0]
    assert abs(best_song["energy"] - 0.80) == min(abs(s["energy"] - 0.80) for s in songs)
    assert best_score <= 1.0  # single-term score, unlike the weighted modes


def test_resolve_strategy_accepts_callable_and_rejects_unknown():
    custom = lambda prefs, song: (0.0, [])
    assert resolve_strategy(custom) is custom
    with pytest.raises(ValueError):
        resolve_strategy("no-such-mode")
