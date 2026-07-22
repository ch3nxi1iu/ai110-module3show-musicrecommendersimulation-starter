import csv
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        # TODO: Implement recommendation logic
        return self.songs[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        # TODO: Implement explanation logic
        return "Explanation placeholder"

NUMERIC_FIELDS = ("energy", "tempo_bpm", "valence", "danceability", "acousticness")

# Graded mood relationships. Each key maps neighboring moods to a similarity
# in (0, 1]. Only one direction of a pair needs an entry -- mood_similarity()
# reads it symmetrically. Anything not listed (and not an exact match) is 0.0.
# This lets a requested mood cluster onto neighbors (e.g. sad -> melancholy)
# instead of the old all-or-nothing string equality.
MOOD_SIMILARITY: Dict[str, Dict[str, float]] = {
    # low-valence / dark
    "sad":        {"melancholy": 0.9, "moody": 0.7, "nostalgic": 0.4, "angry": 0.3},
    "melancholy": {"moody": 0.7, "nostalgic": 0.5, "angry": 0.3},
    "moody":      {"intense": 0.4, "angry": 0.4},
    # high-arousal / hard
    "angry":      {"aggressive": 0.9, "intense": 0.6},
    "aggressive": {"intense": 0.7},
    "intense":    {"euphoric": 0.3, "energetic": 0.7},
    # calm / soft
    "chill":      {"relaxed": 0.9, "laid-back": 0.85, "peaceful": 0.8, "calm": 0.9, "focused": 0.5},
    "relaxed":    {"laid-back": 0.85, "peaceful": 0.8, "calm": 0.9},
    "laid-back":  {"peaceful": 0.7, "calm": 0.8},
    "peaceful":   {"calm": 0.85},
    "focused":    {"relaxed": 0.4},
    "nostalgic":  {"peaceful": 0.4, "romantic": 0.3},
    # high-valence / bright
    "happy":      {"upbeat": 0.9, "euphoric": 0.8, "uplifting": 0.8, "joyful": 0.9},
    "upbeat":     {"euphoric": 0.8, "uplifting": 0.7},
    "euphoric":   {"uplifting": 0.8},
    "energetic":  {"upbeat": 0.6, "euphoric": 0.6},
    "romantic":   {"peaceful": 0.3},
}


def mood_similarity(want: str, have: str) -> float:
    """
    Graded similarity between two mood labels, in [0.0, 1.0].

    1.0 is an exact match; related moods draw partial credit from
    MOOD_SIMILARITY (read symmetrically); everything else is 0.0.

    Case-insensitive: "Chill", "chill", and "CHILL" all match "chill".
    """
    want = want.lower()
    have = have.lower()
    if want == have:
        return 1.0
    forward = MOOD_SIMILARITY.get(want, {}).get(have, 0.0)
    backward = MOOD_SIMILARITY.get(have, {}).get(want, 0.0)
    return max(forward, backward)


def load_songs(csv_path: str) -> List[Dict]:
    """
    Loads songs from a CSV file.
    Required by src/main.py

    Numeric columns are cast to float; `id` is cast to int.
    """
    songs: List[Dict] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["id"] = int(row["id"])
            for field in NUMERIC_FIELDS:
                row[field] = float(row[field])
            songs.append(row)
    return songs

def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """
    Scores a single song against user preferences.
    Required by recommend_songs() and src/main.py

    Weighting recipe:
      2.5 * mood match          (required)
      1.5 * genre match         (required)
      1.0 * energy similarity   (required)
      1.0 * valence similarity      (optional -- scored only if provided)
      0.5 * danceability similarity (optional -- scored only if provided)

    Only mood, genre, and energy are required. Valence and danceability are
    optional refinements: a user who doesn't care about them can leave them
    out, and those terms simply don't contribute to the score.

    Returns (score, reasons).

    Accepts either the descriptive profile keys (favorite_genre,
    favorite_mood, target_energy, target_valence, target_danceability)
    or the short keys (genre, mood, energy, valence, danceability).
    """
    def pref(*keys):
        """Return the first of the given required keys present in user_prefs."""
        for key in keys:
            if key in user_prefs:
                return user_prefs[key]
        raise KeyError(f"user_prefs is missing one of: {keys}")

    def pref_optional(*keys):
        """Return the first present key, or None if the user omitted all of them."""
        for key in keys:
            if key in user_prefs:
                return user_prefs[key]
        return None

    want_mood = pref("favorite_mood", "mood")
    want_genre = pref("favorite_genre", "genre")
    want_energy = pref("target_energy", "energy")
    want_valence = pref_optional("target_valence", "valence")
    want_dance = pref_optional("target_danceability", "danceability")

    # The two categorical weights (2.5 and 1.5) go to whichever the user
    # prioritizes. Default: mood over genre. Set profile["prioritize"] to
    # "genre" to swap them.
    prioritize = user_prefs.get("prioritize", "mood")
    if prioritize == "genre":
        genre_weight, mood_weight = 2.5, 1.5
    else:
        mood_weight, genre_weight = 2.5, 1.5

    mood_sim = mood_similarity(want_mood, song["mood"])
    genre_match = song["genre"].lower() == str(want_genre).lower()
    energy_sim = 1 - abs(song["energy"] - want_energy)

    # Exact mood matches read as "happy mood match"; graded neighbors read
    # as "sad~melancholy mood match" so the explanation shows the clustering.
    if mood_sim >= 1.0:
        mood_label = f"{want_mood} mood match"
    else:
        mood_label = f"{want_mood}~{song['mood']} mood match"

    # Each entry is (label, points contributed to the score). The required
    # three always contribute; the optional two are appended only when the
    # user supplied a target, so an omitted preference never sways the score.
    contributions = [
        (mood_label, mood_weight * mood_sim),
        (f"{want_genre} genre match", genre_weight * genre_match),
        ("energy similarity", 1.0 * energy_sim),
    ]
    if want_valence is not None:
        contributions.append(("valence similarity", 1.0 * (1 - abs(song["valence"] - want_valence))))
    if want_dance is not None:
        contributions.append(("danceability similarity", 0.5 * (1 - abs(song["danceability"] - want_dance))))

    score = sum(points for _, points in contributions)

    # Only surface components that actually added points, biggest first,
    # each annotated with how much it contributed.
    reasons: List[str] = [
        f"{label} (+{points:.2f})"
        for label, points in sorted(contributions, key=lambda c: c[1], reverse=True)
        if points > 0
    ]

    return score, reasons

# --- Ranking strategies (Strategy pattern) --------------------------------
# A ranking strategy is any callable with the same contract as score_song:
#   (user_prefs, song) -> (score, reasons)
# Modes are registered by name in RANKING_STRATEGIES, so a new ranking mode
# can be added without changing recommend_songs() or main.py -- both resolve
# strategies by name and stay agnostic about how any mode computes its score.

def mood_first_strategy(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """Weighted score with mood prioritized over genre (mood gets 2.5)."""
    return score_song({**user_prefs, "prioritize": "mood"}, song)


def genre_first_strategy(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """Weighted score with genre prioritized over mood (genre gets 2.5)."""
    return score_song({**user_prefs, "prioritize": "genre"}, song)


def energy_similarity_strategy(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """Rank purely by how close a song's energy is to the target, ignoring
    genre and mood entirely -- useful for "find me songs at this intensity"."""
    want = user_prefs.get("target_energy", user_prefs.get("energy"))
    if want is None:
        raise KeyError("energy-similarity mode needs 'target_energy' (or 'energy')")
    sim = 1 - abs(song["energy"] - want)
    reasons = [f"energy similarity (+{sim:.2f})"] if sim > 0 else []
    return sim, reasons


# Registry: name -> strategy callable. Order is the menu order in main.py.
RANKING_STRATEGIES = {
    "mood-first": mood_first_strategy,
    "genre-first": genre_first_strategy,
    "energy-similarity": energy_similarity_strategy,
}


def resolve_strategy(strategy):
    """
    Normalize a strategy argument into a scoring callable.

    - None            -> score_song (default; respects prefs['prioritize'])
    - a callable       -> used as-is (bring your own strategy)
    - a registered name -> looked up in RANKING_STRATEGIES
    """
    if strategy is None:
        return score_song
    if callable(strategy):
        return strategy
    try:
        return RANKING_STRATEGIES[strategy]
    except KeyError:
        raise ValueError(
            f"Unknown ranking strategy {strategy!r}; "
            f"choose from {sorted(RANKING_STRATEGIES)}"
        )


def recommend_songs(
    user_prefs: Dict,
    songs: List[Dict],
    k: int = 5,
    strategy=None,
) -> List[Tuple[Dict, float, str]]:
    """
    Functional implementation of the recommendation logic.
    Required by src/main.py

    `strategy` selects the ranking mode (Strategy pattern): a name from
    RANKING_STRATEGIES, a custom (user_prefs, song) -> (score, reasons)
    callable, or None for the default score_song behavior.
    """
    score_fn = resolve_strategy(strategy)
    scored: List[Tuple[Dict, float, str]] = []
    for song in songs:
        score, reasons = score_fn(user_prefs, song)
        explanation = "; ".join(reasons) if reasons else "a general match for your taste"
        scored.append((song, score, explanation))

    scored.sort(key=lambda item: item[1], reverse=True)
    return scored[:k]


def recommend(df, prefs: Dict, n: int = 5) -> List[Tuple[str, str, float]]:
    """
    v1 ranking rule (pandas): score every row and return the top-n
    as (title, artist, score) tuples, ranked by score descending.
    """
    scores = []
    for _, song in df.iterrows():
        s, _reasons = score_song(prefs, song)
        scores.append((song["title"], song["artist"], s))

    ranked = sorted(scores, key=lambda x: x[2], reverse=True)
    return ranked[:n]
