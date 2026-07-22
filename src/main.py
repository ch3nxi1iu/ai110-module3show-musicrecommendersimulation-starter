"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

import os
import sys

# Works whether launched as `python -m src.main` (from the project root) or
# as `python src/main.py` (IDE Run button): put the project root -- the
# parent of this file's src/ folder -- on the import path.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.recommender import load_songs, recommend_songs, RANKING_STRATEGIES
from src.profiles import BASELINE_PROFILES, ADVERSARIAL_PROFILES

# Absolute path so the CSV is found regardless of the current directory.
SONGS_CSV = os.path.join(PROJECT_ROOT, "data", "songs.csv")


def print_recommendations(prefs: dict, songs: list, k: int = 3) -> None:
    """Score `songs` against `prefs` and print the top-k with explanations."""
    for song, score, explanation in recommend_songs(prefs, songs, k=k):
        print(f"  {score:5.2f}  {song['title']} ({song['genre']}, {song['mood']})")
        print(f"         because: {explanation}")


def run_demo() -> None:
    """
    Non-interactive walkthrough of the baseline and adversarial profiles.
    Run with: python -m src.main --demo
    """
    songs = load_songs(SONGS_CSV)

    print("=== Baseline profiles ===\n")
    for name, prefs in BASELINE_PROFILES.items():
        print(name)
        print_recommendations(prefs, songs)
        print()

    print("=== Adversarial / edge-case profiles ===\n")
    for name, (prefs, note) in ADVERSARIAL_PROFILES.items():
        print(f"{name} -- {note}")
        print_recommendations(prefs, songs)
        print()


def ask_strategy() -> str:
    """
    Ask which ranking mode to use and return a key from RANKING_STRATEGIES.
    Defaults to the first mode (mood-first) on blank/invalid input.
    """
    modes = list(RANKING_STRATEGIES)  # registry order = menu order
    print("Ranking modes:")
    for i, name in enumerate(modes, 1):
        print(f"  {i}. {name}")

    answer = input(f"Choose a mode [1-{len(modes)}, default 1]: ").strip()
    if answer.isdigit() and 1 <= int(answer) <= len(modes):
        return modes[int(answer) - 1]

    print(f"Unrecognized choice — defaulting to {modes[0]}.")
    return modes[0]


def _read_float(prompt: str, default=None, optional: bool = False):
    """Read a number in [0.0, 1.0]. Blank returns `default` (or None if
    optional); anything invalid re-prompts."""
    if default is not None:
        hint = f" [default {default}]"
    elif optional:
        hint = " [blank to skip]"
    else:
        hint = ""
    while True:
        raw = input(f"{prompt}{hint}: ").strip()
        if raw == "":
            return default
        try:
            value = float(raw)
        except ValueError:
            print("  Please enter a number like 0.7.")
            continue
        if not 0.0 <= value <= 1.0:
            print("  Please enter a value between 0.0 and 1.0.")
            continue
        return value


def ask_profile(strategy: str) -> dict:
    """
    Collect the taste profile the chosen mode needs.

    The weighted modes (mood-first / genre-first) ask for genre, mood, and
    energy, with valence and danceability optional. The energy-similarity mode
    ignores genre and mood, so it only asks for a target energy.
    """
    prefs: dict = {}
    if strategy != "energy-similarity":
        prefs["favorite_genre"] = input("Favorite genre (e.g. pop, lofi, rock) [pop]: ").strip() or "pop"
        prefs["favorite_mood"] = input("Desired mood (e.g. happy, chill, intense) [happy]: ").strip() or "happy"

    prefs["target_energy"] = _read_float("Target energy 0.0-1.0", default=0.8)

    if strategy != "energy-similarity":
        valence = _read_float("Target valence 0.0-1.0", optional=True)
        if valence is not None:
            prefs["target_valence"] = valence
        danceability = _read_float("Target danceability 0.0-1.0", optional=True)
        if danceability is not None:
            prefs["target_danceability"] = danceability

    return prefs


def main() -> None:
    songs = load_songs(SONGS_CSV)

    # Let the user pick a ranking mode, then enter the taste profile it needs.
    strategy = ask_strategy()
    print(f"Ranking mode: {strategy}\n")

    user_prefs = ask_profile(strategy)

    recommendations = recommend_songs(user_prefs, songs, k=5, strategy=strategy)

    print("\nTop 5 recommendations:\n")
    for rec in recommendations:
        # You decide the structure of each returned item.
        # A common pattern is: (song, score, explanation)
        song, score, explanation = rec
        print(f"{song['title']} - Score: {score:.2f}")
        print(f"Because: {explanation}")
        print()


if __name__ == "__main__":
    if "--demo" in sys.argv[1:]:
        run_demo()
    else:
        main()
