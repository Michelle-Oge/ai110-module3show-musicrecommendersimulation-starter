"""
Run:  pip install flask flask-cors
Run:  python app.py
Open: http://localhost:5000
"""

import os, csv, json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder=".")
CORS(app)


# ── Load catalog ───────────────────────────────────────────────────────────────

def load_songs(path="data/songs.csv"):
    songs = []
    with open(path, newline="", encoding="utf-8") as f:
        for i, row in enumerate(csv.DictReader(f)):
            songs.append({
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
            })
    return songs

SONGS = load_songs()


# ── Local keyword-based profile extractor (no API key needed) ──────────────────

def extract_profile_locally(text):
    t = text.lower()

    # Genre
    if any(w in t for w in ["rock","guitar","metal","grunge","punk","riff"]):
        genre = "rock"
    elif any(w in t for w in ["lofi","lo-fi","lo fi","chill hop","chillhop"]):
        genre = "lofi"
    elif any(w in t for w in ["hip hop","hiphop","hip-hop","rap","trap","beats"]):
        genre = "hiphop"
    elif any(w in t for w in ["electronic","edm","house","techno","synth","rave","dance music"]):
        genre = "electronic"
    elif any(w in t for w in ["classical","orchestra","piano","beethoven","mozart","baroque"]):
        genre = "classical"
    else:
        genre = "pop"

    # Mood
    if any(w in t for w in ["intense","aggressive","heavy","angry","rage","powerful","hard"]):
        mood = "intense"
    elif any(w in t for w in ["sad","melancholy","melancholic","cry","heartbreak","lonely","blue","somber","gloomy"]):
        mood = "sad"
    elif any(w in t for w in ["calm","relax","chill","focus","study","peaceful","quiet","soft","gentle","serene"]):
        mood = "calm"
    else:
        mood = "happy"

    # Energy
    if any(w in t for w in ["high energy","workout","gym","intense","aggressive","fast","loud","pumped","hype"]):
        energy = 0.9
    elif any(w in t for w in ["calm","chill","study","relax","slow","quiet","peaceful","focus","soft"]):
        energy = 0.2
    elif any(w in t for w in ["mid","moderate","medium","drive","walk","background"]):
        energy = 0.55
    else:
        energy = 0.65

    # Acoustic
    likes_acoustic = any(w in t for w in [
        "acoustic","unplugged","folk","classical","guitar only",
        "piano","instrumental","organic","natural sound"
    ])

    # Confidence: rough heuristic based on how many signals matched
    matched = sum([
        genre != "pop",
        mood != "happy",
        energy != 0.65,
        likes_acoustic,
    ])
    confidence = round(0.45 + (matched * 0.13), 2)

    return {
        "favorite_genre": genre,
        "favorite_mood":  mood,
        "target_energy":  energy,
        "likes_acoustic": likes_acoustic,
        "reasoning": (
            f"Detected genre signals pointing to '{genre}', "
            f"mood signals suggesting '{mood}', "
            f"and energy level around {energy} based on your description. "
            f"Acoustic preference set to {'yes' if likes_acoustic else 'no'}. "
            f"Using local keyword extraction — add an Anthropic API key for richer AI reasoning."
        ),
        "confidence": confidence,
        "flags": [] if matched >= 2 else [
            "Low signal strength — description was ambiguous. Try adding genre, mood, or energy keywords."
        ],
    }


# ── Content-based scorer ───────────────────────────────────────────────────────

def score_song(prefs, song):
    score = 0.0
    reasons = []

    if song["genre"] == prefs.get("favorite_genre"):
        score += 2.0
        reasons.append({"type": "genre", "text": f"genre match: {song['genre']} (+2.0)"})

    if song["mood"] == prefs.get("favorite_mood"):
        score += 1.0
        reasons.append({"type": "mood", "text": f"mood match: {song['mood']} (+1.0)"})

    tgt = prefs.get("target_energy", 0.5)
    e_pts = round(1.0 - abs(tgt - song["energy"]), 2)
    score += e_pts
    label = "close" if e_pts > 0.8 else "near" if e_pts > 0.5 else "far"
    reasons.append({"type": "energy", "text": f"energy {label}: {song['energy']} (+{e_pts})"})

    if prefs.get("likes_acoustic"):
        a_pts = round(0.5 * song["acousticness"], 2)
        score += a_pts
        if a_pts > 0.2:
            reasons.append({"type": "other", "text": f"acoustic fit (+{a_pts})"})
    else:
        a_pts = round(0.5 * (1.0 - song["acousticness"]), 2)
        score += a_pts
        if a_pts > 0.3:
            reasons.append({"type": "other", "text": f"electronic feel (+{a_pts})"})

    d_pts = round(0.5 * (1.0 - abs(0.65 - song["danceability"])), 2)
    score += d_pts

    return round(score, 2), reasons


def recommend(prefs, k=5):
    results = []
    for s in SONGS:
        score, reasons = score_song(prefs, s)
        results.append({"song": s, "score": score, "reasons": reasons})
    return sorted(results, key=lambda x: x["score"], reverse=True)[:k]


# ── Guardrails ─────────────────────────────────────────────────────────────────

def run_guardrails(user_input, prefs, results):
    checks = []

    if len(user_input.strip()) < 4:
        checks.append({"status": "fail", "title": "Input too short",
                        "detail": "Please describe your vibe in a few words."})
    else:
        snippet = user_input[:60] + ("…" if len(user_input) > 60 else "")
        checks.append({"status": "pass", "title": "Input valid",
                        "detail": f'"{snippet}" — enough context for keyword extraction.'})

    genre_count = sum(1 for s in SONGS if s["genre"] == prefs.get("favorite_genre"))
    if genre_count == 0:
        checks.append({"status": "warn", "title": "Genre not in catalog",
                        "detail": f'"{prefs.get("favorite_genre")}" has 0 songs. Rankings rely on mood + energy only.'})
    else:
        checks.append({"status": "pass", "title": f"Catalog: {genre_count} songs match",
                        "detail": f'{genre_count} "{prefs.get("favorite_genre")}" songs found — sufficient for ranking.'})

    top_score = results[0]["score"] if results else 0
    conf = top_score / 4.5
    if conf < 0.38:
        checks.append({"status": "warn", "title": f"Low confidence ({round(conf*100)}%)",
                        "detail": f"Best score {top_score}/4.5. Preferences may conflict or catalog coverage is thin."})
    else:
        checks.append({"status": "pass", "title": f"Confidence {round(conf*100)}%",
                        "detail": f"Top result scored {top_score}/4.5 — recommendations are well-supported."})

    top_genres = list(dict.fromkeys(r["song"]["genre"] for r in results[:3]))
    if len(top_genres) == 1:
        checks.append({"status": "warn", "title": "Genre filter bubble",
                        "detail": f'All top-3 results are "{top_genres[0]}". Genre weight may suppress variety.'})
    else:
        checks.append({"status": "pass", "title": "Genre diversity OK",
                        "detail": f"Top results span {len(top_genres)} genres — no filter bubble detected."})

    return checks


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/recommend", methods=["POST"])
def recommend_route():
    body = request.get_json()
    user_input = body.get("vibe", "").strip()

    if not user_input:
        return jsonify({"error": "No vibe provided"}), 400

    profile = extract_profile_locally(user_input)
    results = recommend(profile, k=5)
    checks  = run_guardrails(user_input, profile, results)

    return jsonify({
        "profile":    profile,
        "results":    results,
        "guardrails": checks,
    })


@app.route("/songs")
def songs_route():
    return jsonify(SONGS)


if __name__ == "__main__":
    print("\n  Tunes4You 2.0 running at http://localhost:5000")
    print("  No API key required — using local keyword extraction\n")
    app.run(debug=True, port=5000)