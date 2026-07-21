"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from src.recommender import load_songs, recommend_songs


def ask_priority() -> str:
    """
    Ask whether the user prioritizes genre or mood, and return the
    winning key ("genre" or "mood"). Defaults to "mood" on blank/invalid.
    """
    answer = input(
        "Do you prefer (g)enre over mood, or (m)ood over genre? [g/m]: "
    ).strip().lower()

    if answer in ("g", "genre"):
        return "genre"
    if answer in ("m", "mood"):
        return "mood"

    print("Unrecognized choice — defaulting to mood priority.")
    return "mood"


def main() -> None:
    songs = load_songs("data/songs.csv")

    # Starter example profile
    # Taste profile: target values the recommender scores songs against.
    user_prefs = {
        "favorite_genre": "pop",
        "favorite_mood": "happy",
        "target_energy": 0.8,
        "target_valence": 0.8,
        "target_danceability": 0.75,
        "likes_acoustic": False,
    }

    # Let the user decide which categorical feature carries the heavier weight.
    user_prefs["prioritize"] = ask_priority()
    print(f"Prioritizing {user_prefs['prioritize']} (weight 2.5) over the other (weight 1.5).")

    recommendations = recommend_songs(user_prefs, songs, k=3)

    print("\nTop 3 recommendations:\n")
    for rec in recommendations:
        # You decide the structure of each returned item.
        # A common pattern is: (song, score, explanation)
        song, score, explanation = rec
        print(f"{song['title']} - Score: {score:.2f}")
        print(f"Because: {explanation}")
        print()


if __name__ == "__main__":
    main()
