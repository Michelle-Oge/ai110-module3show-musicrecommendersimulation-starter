import csv
from typing import List, Dict, Tuple
from dataclasses import dataclass

 
@dataclass
class Song:
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
    
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool
 
 
class Recommender:
   
 
    def __init__(self, songs: List[Song]):
        self.songs = songs
 
    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        
        scored = []
        for song in self.songs:
            score = self._score(user, song)
            scored.append((song, score))
 
        scored.sort(key=lambda x: x[1], reverse=True)
        return [song for song, _ in scored[:k]]
 
    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        
        reasons = []
 
        if song.genre == user.favorite_genre:
            reasons.append(f"genre matches your favorite ({song.genre})")
 
        if song.mood == user.favorite_mood:
            reasons.append(f"mood matches your preference ({song.mood})")
 
        energy_gap = abs(user.target_energy - song.energy)
        if energy_gap <= 0.15:
            reasons.append(f"energy level ({song.energy}) is close to your target ({user.target_energy})")
        elif energy_gap >= 0.5:
            reasons.append(f"energy level ({song.energy}) is far from your target ({user.target_energy})")
 
        if user.likes_acoustic and song.acousticness >= 0.6:
            reasons.append(f"acoustic score ({song.acousticness}) suits your preference for acoustic music")
        elif not user.likes_acoustic and song.acousticness <= 0.2:
            reasons.append(f"low acousticness ({song.acousticness}) fits your non-acoustic preference")
 
        if not reasons:
            return f"'{song.title}' partially matches your profile but has no strong individual signals."
 
        return f"'{song.title}' was recommended because: " + "; ".join(reasons) + "."
 
    def _score(self, user: UserProfile, song: Song) -> float:
        
        score = 0.0
 
        if song.genre == user.favorite_genre:
            score += 2.0
        if song.mood == user.favorite_mood:
            score += 1.0
 
        # Energy proximity: closer to target = higher score (max +1.0)
        score += round(1.0 - abs(user.target_energy - song.energy), 3)
 
        # Acoustic bonus/penalty (max +0.5)
        if user.likes_acoustic:
            score += round(0.5 * song.acousticness, 3)
        else:
            score += round(0.5 * (1.0 - song.acousticness), 3)
 
        # Danceability proximity (max +0.5) — default target 0.65
        score += round(0.5 * (1.0 - abs(0.65 - song.danceability)), 3)
 
        return round(score, 3)
 
 
def load_songs(csv_path: str) -> List[Dict]:
   
    print(f"Loading songs from {csv_path}...")
    songs = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            song = {
                "id":           i,
                "title":        row["title"],
                "artist":       row["artist"],
                "genre":        row["genre"],
                "mood":         row["mood"],
                "energy":       float(row["energy"]),
                "valence":      float(row["valence"]),
                "tempo_bpm":    int(row["tempo_bpm"]),
                "danceability": float(row["danceability"]),
                "acousticness": float(row["acousticness"]),
            }
            songs.append(song)
    return songs
 
def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """
    Score a single song against user preferences using the Algorithm Recipe.
 
    Accepts both short keys  {"genre", "mood", "energy"}
    and long keys {"favorite_genre", "favorite_mood", "target_energy"}.
 
    Recipe:
      +2.0    genre match
      +1.0    mood match
      +0-1.0  energy proximity  (1 - |target - song|)
      +0-0.5  acoustic fit      (scaled by acousticness or its inverse)
      +0-0.5  danceability proximity
 
    Returns:
        (total_score, reasons)  where reasons is a list of plain-English strings.
    """
    # Normalise keys: starter main.py uses short keys; our extended profiles use long keys.
    fav_genre  = user_prefs.get("favorite_genre") or user_prefs.get("genre")
    fav_mood   = user_prefs.get("favorite_mood")  or user_prefs.get("mood")
    tgt_energy = user_prefs.get("target_energy")  if user_prefs.get("target_energy") is not None \
                 else user_prefs.get("energy", 0.5)
    likes_acoustic = user_prefs.get("likes_acoustic", False)
 
    score = 0.0
    reasons = []
 
    # Genre match (+2.0)
    if song["genre"] == fav_genre:
        score += 2.0
        reasons.append(f"genre match: {song['genre']} (+2.0)")
 
    # Mood match (+1.0)
    if song["mood"] == fav_mood:
        score += 1.0
        reasons.append(f"mood match: {song['mood']} (+1.0)")
 
    # Energy proximity (max +1.0)
    energy_pts = round(1.0 - abs(tgt_energy - song["energy"]), 3)
    score += energy_pts
    reasons.append(f"energy proximity: {song['energy']} vs target {tgt_energy} (+{energy_pts})")
 
    # Acoustic fit (max +0.5)
    if likes_acoustic:
        acoustic_pts = round(0.5 * song["acousticness"], 3)
        reasons.append(f"acoustic fit: acousticness {song['acousticness']} (+{acoustic_pts})")
    else:
        acoustic_pts = round(0.5 * (1.0 - song["acousticness"]), 3)
        reasons.append(f"non-acoustic fit: acousticness {song['acousticness']} (+{acoustic_pts})")
    score += acoustic_pts
 
    # Danceability proximity — default target 0.65 (max +0.5)
    dance_pts = round(0.5 * (1.0 - abs(0.65 - song["danceability"])), 3)
    score += dance_pts
    reasons.append(f"danceability proximity: {song['danceability']} (+{dance_pts})")
 
    return round(score, 3), reasons
 
 
def recommend_songs(
    user_prefs: Dict, songs: List[Dict], k: int = 5
) -> List[Tuple[Dict, float, str]]:
    """
    Score every song, sort highest-to-lowest, and return the top-k.
 
    Returns:
        List of (song_dict, score, explanation_string) tuples.
    """
    scored = []
    for song in songs:
        score, reasons = score_song(user_prefs, song)
        explanation = " | ".join(reasons)
        scored.append((song, score, explanation))
 
    return sorted(scored, key=lambda x: x[1], reverse=True)[:k]