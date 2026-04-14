"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from src.recommender import load_songs, recommend_songs

PROFILES = {
   
    "High-Energy Pop": {
        "genre": "pop",
        "mood": "happy",
        "energy": 0.85,
        "likes_acoustic": False,
    },
    "Chill Lofi": {
        "genre": "lofi",
        "mood": "calm",
        "energy": 0.2,
        "likes_acoustic": True,
    },
    "Deep Intense Rock": {
        "genre": "rock",
        "mood": "intense",
        "energy": 0.95,
        "likes_acoustic": False,
    },
    
    "Sad but High-Energy (conflict)": {
        "genre": "hiphop",
        "mood": "sad",
        "energy": 0.95,
        "likes_acoustic": False,
    },
    
    "Unknown Genre + Mood (no match)": {
        "genre": "jazz",
        "mood": "nostalgic",
        "energy": 0.5,
        "likes_acoustic": True,
    },
   
    "Acoustic but Intense (contradiction)": {
        "genre": "classical",
        "mood": "intense",
        "energy": 0.9,
        "likes_acoustic": True,
    },
}

DIVIDER = "=" * 62


def print_profile(name, prefs, songs, k=5):
    
    print(f"\n{DIVIDER}")
    print(f"  Profile : {name}")
    print(f"  Prefs   : {prefs}")
    print(DIVIDER)
    results = recommend_songs(prefs, songs, k=k)
    for rank, (song, score, explanation) in enumerate(results, 1):
        print(f"\n  #{rank}  {song['title']} — {song['artist']}")
        print(f"       Genre: {song['genre']} | Mood: {song['mood']} | Energy: {song['energy']}")
        print(f"       Score: {score:.2f}")
        print("       Why:")
        for reason in explanation.split(" | "):
            print(f"         • {reason}")
    print()


def main() -> None:
    songs = load_songs("data/songs.csv")
    print(f"Loaded songs: {len(songs)}")

    for name, prefs in PROFILES.items():
        print_profile(name, prefs, songs)


if __name__ == "__main__":
    main()