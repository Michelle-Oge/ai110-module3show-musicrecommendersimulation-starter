# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name  

Tunes4You

---

## 2. Intended Use  

Tunes4You is designed to suggest songs from a small catalog that match a user's stated musical taste. You tell it your favorite genre, preferred mood, and how energetic you want the music to feel, and it returns five songs ranked by how well they fit.
It assumes the user already knows what they like and can describe it in simple terms. Genre, mood, and energy level. It does not learn from listening history or adapt over time. This is a classroom simulation built to explore how content-based recommendation logic works, not a production tool for real music apps.

---

## 3. How the Model Works  

For every song in the catalog, it awards points in four areas:

Genre: if the song's genre matches your favorite, it gets a big bonus (+2 points). This is the single most important factor.

Mood: if the song's mood (happy, sad, calm, intense) matches yours, it gets another bonus (+1 point).

Energy: songs closer to your target energy level score higher. A perfect energy match gives +1 point; a song on the opposite end of the scale gives close to zero.

Acoustic feel: if you prefer acoustic music, songs with higher acousticness score better. If you prefer produced/electronic sound, low-acousticness songs score better. This is worth up to +0.5 points.

Once every song has a total score (maximum possible: 4.5 points), they are sorted from highest to lowest and the top five are returned with a explanation of what earned each song its points.

---

## 4. Data  

The catalog contains 24 songs spread across six genres: pop, rock, lofi, hip-hop, electronic, and classical. Moods are labeled as happy, sad, calm, or intense. Each song also has numerical scores for energy, acousticness, danceability, valence, and tempo.
The original starter file had 10 songs. An additional 14 were added manually to increase genre and mood diversity, particularly to add lofi, classical, and a wider range of hip-hop and electronic tracks.
Several dimensions of musical taste are missing. There is no representation of country, jazz, R&B, folk, metal (as a separate genre from rock), or Latin music. Tempo is stored but not used in scoring. 

---

## 5. Strengths  

The system works best when a user's preferences are internally consistent and well-represented in the catalog. A few cases where it performed well:

Clear genre + mood combinations. A "Deep Intense Rock" profile correctly surfaced Master of Puppets, Black Dog, and Bohemian Rhapsody in that order. These are intuitive results that match what most people would expect.

Lofi listeners. The Chill Lofi profile returned all three lofi/calm songs as the top three, with a bonus classical track (Classical Gas) sneaking in at #5 on acoustic fit alone, which actually makes sense musically.

Separating styles cleanly. Pop and rock profiles never overlapped in their top 3 results, showing the genre weight is doing its job of keeping results focused.

---

## 6. Limitations and Bias 

Genre dominance. The genre bonus (+2.0) is so large that it is nearly impossible for a song outside the user's preferred genre to appear in the top results, even if it is a near-perfect match on every other dimension. This creates a filter bubble where users only see their own genre reflected back at them.

Conflicting preferences are ignored. When a user asks for "sad mood but very high energy," the system cannot detect that these preferences are in tension. It just picks whichever song scores highest under both constraints independently, which often produces a result that satisfies neither preference well.

No confidence floor. When a user asks for a genre or mood not in the catalog (tested with "jazz / nostalgic"), the system still returns five results with no warning. All scores were below 1.7, but the user has no way to know those results are essentially random noise.

Pop overrepresentation. Five of the 24 songs are pop, giving pop-preferring users more variety and better top-5 diversity than users who prefer classical (only 2 songs) or electronic (4 songs).  

---

## 7. Evaluation  

Six user profiles were tested. three standard and three adversarial.
The standard profiles (High-Energy Pop, Chill Lofi, Deep Intense Rock) all produced results that matched intuition. Top results had both genre and mood matches; lower-ranked results had genre matches but missed on mood; and no cross-genre songs appeared in the top 3 for any profile.

The adversarial profiles revealed three specific weaknesses:

Sad + High-Energy (hiphop): The only hiphop/sad song in the catalog (Pursuit of Happiness) ranked #1 despite having energy=0.55 against a target of 0.95. A 40% miss. The genre+mood bonus made it untouchable.

Jazz + Nostalgic: No song matched either preference. The system returned results based on energy and acousticness alone, with no signal that confidence was low.

Classical + Intense + Acoustic: Classical Gas (slow, quiet) outranked Skrillex (perfect energy and mood match) because the classical genre bonus alone was worth more than Skrillex's numeric advantage.

---

## 8. Future Work  

Add a confidence threshold. If the highest score in a result set falls below a certain value (say 2.0), the system should display a message like "no strong matches found" rather than returning low-quality results silently.

Soften genre dominance. Reduce the genre weight from +2.0 to +1.5 and add a secondary feature.

Add diversity enforcement. After scoring, check whether the top 5 are all from the same artist or sub-genre and swap in a lower-ranked song from a different artist if so. This prevents the same three songs from appearing every time. 

---

## 9. Personal Reflection  

The biggest learning moment was realizing how much a single design decision, giving genre a +2.0 weight shaped every result the system produces. It felt like a reasonable choice at the time, but testing revealed it makes the system almost incapable of recommending anything outside a user's stated genre, even when another song would genuinely fit better. 

The adversarial profiles were the most interesting part. I expected them to break the system in obvious ways, but instead they revealed something subtler. The system does not fail loudly, it fails quietly. It still returns five results with confident-looking scores even when it has essentially no useful information to work with.
