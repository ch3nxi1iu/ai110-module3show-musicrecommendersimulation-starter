"""
Reusable user-preference profiles for the music recommender.

Single source of truth shared by src/main.py (demo mode) and
tests/test_profiles.py. Each profile is a dict accepted directly by
recommender.score_song / recommend_songs.

BASELINE_PROFILES    -- well-formed "happy path" tastes.
ADVERSARIAL_PROFILES -- edge cases that probe the scoring logic. The
                        `note` on each documents the failure mode it exposes.
"""

# --- baseline: clean, intended-to-work profiles ---------------------------
BASELINE_PROFILES = {
    "High-Energy Pop": dict(
        favorite_genre="pop", favorite_mood="happy",
        target_energy=0.90, target_valence=0.85, target_danceability=0.85,
    ),
    "Chill Lofi": dict(
        favorite_genre="lofi", favorite_mood="chill",
        target_energy=0.40, target_valence=0.55, target_danceability=0.60,
    ),
    "Deep Intense Rock": dict(
        favorite_genre="rock", favorite_mood="intense",
        target_energy=0.90, target_valence=0.45, target_danceability=0.60,
    ),
}

# --- adversarial: designed to trick or surprise the scoring logic ---------
# Each value is (profile_dict, note-describing-what-it-exposes).
ADVERSARIAL_PROFILES = {
    "Ghost mood": (
        dict(favorite_genre="soul", favorite_mood="sad",
             target_energy=0.40, target_valence=0.20, target_danceability=0.50),
        "mood 'sad' is not a catalog label; graded mood_similarity now clusters "
        "it onto its melancholy/moody neighbors for partial credit instead of "
        "scoring a silent zero.",
    ),
    "Split brain": (
        dict(favorite_genre="folk", favorite_mood="peaceful",
             target_energy=0.95, target_valence=0.90, target_danceability=0.95),
        "genre+mood (max 4.0) swamp the numeric terms (max 2.5): a calm folk "
        "song wins despite the requested energy/danceability being its opposite.",
    ),
    "Out of range": (
        dict(favorite_genre="pop", favorite_mood="happy",
             target_energy=2.0, target_valence=0.85, target_danceability=0.85),
        "target_energy=2.0 is never clamped, so energy similarity goes negative "
        "and silently deflates every score.",
    ),
    "Case mismatch": (
        dict(favorite_genre="lofi", favorite_mood="Chill",
             target_energy=0.40, target_valence=0.55, target_danceability=0.60),
        "mixed-case mood 'Chill' is normalized -- mood matching is now "
        "case-insensitive, so it matches 'chill' as expected.",
    ),
    "Bad priority key": (
        dict(favorite_genre="pop", favorite_mood="happy",
             target_energy=0.90, target_valence=0.85, target_danceability=0.85,
             prioritize="valence"),
        "only the exact string 'genre' changes weighting; any other value is "
        "silently swallowed and defaults to mood priority.",
    ),
    "Null profile": (
        dict(favorite_genre="kpop", favorite_mood="",
             target_energy=0.0, target_valence=0.0, target_danceability=0.0),
        "unknown genre + empty mood + all-zero targets still returns confident "
        "results; the system never says it doesn't understand the profile.",
    ),
}
