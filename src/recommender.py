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
      2.5 * mood match
      1.5 * genre match
      1.0 * energy similarity
      1.0 * valence similarity
      0.5 * danceability similarity

    Returns (score, reasons).

    Accepts either the descriptive profile keys (favorite_genre,
    favorite_mood, target_energy, target_valence, target_danceability)
    or the short keys (genre, mood, energy, valence, danceability).
    """
    def pref(*keys):
        """Return the first of the given keys present in user_prefs."""
        for key in keys:
            if key in user_prefs:
                return user_prefs[key]
        raise KeyError(f"user_prefs is missing one of: {keys}")

    want_mood = pref("favorite_mood", "mood")
    want_genre = pref("favorite_genre", "genre")
    want_energy = pref("target_energy", "energy")
    want_valence = pref("target_valence", "valence")
    want_dance = pref("target_danceability", "danceability")

    # The two categorical weights (2.5 and 1.5) go to whichever the user
    # prioritizes. Default: mood over genre. Set profile["prioritize"] to
    # "genre" to swap them.
    prioritize = user_prefs.get("prioritize", "mood")
    if prioritize == "genre":
        genre_weight, mood_weight = 2.5, 1.5
    else:
        mood_weight, genre_weight = 2.5, 1.5

    mood_match = song["mood"] == want_mood
    genre_match = song["genre"] == want_genre
    energy_sim = 1 - abs(song["energy"] - want_energy)
    valence_sim = 1 - abs(song["valence"] - want_valence)
    dance_sim = 1 - abs(song["danceability"] - want_dance)

    # Each entry is (label, points contributed to the score).
    contributions = [
        (f"{want_mood} mood match", mood_weight * mood_match),
        (f"{want_genre} genre match", genre_weight * genre_match),
        ("energy similarity", 1.0 * energy_sim),
        ("valence similarity", 1.0 * valence_sim),
        ("danceability similarity", 0.5 * dance_sim),
    ]

    score = sum(points for _, points in contributions)

    # Only surface components that actually added points, biggest first,
    # each annotated with how much it contributed.
    reasons: List[str] = [
        f"{label} (+{points:.2f})"
        for label, points in sorted(contributions, key=lambda c: c[1], reverse=True)
        if points > 0
    ]

    return score, reasons

def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """
    Functional implementation of the recommendation logic.
    Required by src/main.py
    """
    scored: List[Tuple[Dict, float, str]] = []
    for song in songs:
        score, reasons = score_song(user_prefs, song)
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
