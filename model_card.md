# Model Card: VibeFinder

## 1. Model Name

**VibeFinder 1.0 — Explainable Music Recommender**

## 2. Intended Use

This is a classroom simulation for exploring how data and preferences become recommendations. It suggests songs from a fixed catalog to a listener who supplies a genre, mood, and energy target, plus optional numeric targets. It is useful for comparing scoring choices and examining explanations. It is not a trained machine-learning model, a commercial music service, or a validated predictor of individual taste.

## 3. How the Model Works

Each song earns points when its genre or mood matches the listener's preferences. Numeric features earn more points as their values get closer to the requested targets. Features have different weights, and the user can select genre-first, mood-first, or energy-first scoring. The engine repeatedly chooses the best remaining song; when diversity is enabled, previously selected artists receive a penalty. Every recommendation reports all feature contributions and the artist penalty.

The original starter had placeholder loading and scoring functions and returned the first songs rather than a calculated ranking. This version loads real CSV rows, converts numbers, validates them, computes relevance, and sorts candidates. Both the starter class interface and the dictionary interface use the same scorer.

Project 4 adds a reliability pipeline to the working recommender. It rejects malformed inputs, checks genre coverage, filters below a configurable normalized match threshold, and verifies the output against the catalog and scorer. It can return fewer songs or abstain. A 0.70 threshold is a project design choice, not a learned probability threshold. No LLM or external API is required.

## 4. Data

The catalog contains **20 songs**: the 10 original CodePath rows plus 10 synthetic additions. No original values were removed or replaced. Titles and attributes are illustrative and are not verified measurements of real recordings. Added rows cover EDM, folk, acoustic, hip-hop, R&B, classical, pop, and lofi. Existing rows also cover rock, ambient, jazz, synthwave, and indie pop.

Original attributes are ID, title, artist, genre, mood, energy, tempo, valence, danceability, and acousticness. Five new attributes are instrumentalness (0–1), synthetic popularity (0–100), release year (1950–2030 validation range), duration in seconds (60–600), and live performance (0 or 1). Release year and popularity are invented descriptors, not scraped facts. A target of 0.5 for live performance means no preference between studio and live recordings. Other feature scales and weights are listed in the README.

There are 13 genre labels: pop 3, lofi 4, EDM 3, and one each of rock, ambient, jazz, synthwave, indie pop, folk, acoustic, hip-hop, R&B, and classical. Indie pop is counted separately from pop. There is no train/test split because no parameters are learned. The evaluation uses predefined cases against the catalog and separate synthetic test fixtures.

## 5. Strengths

The explanations are tied directly to the scoring rule, making unexpected choices inspectable. Numeric target similarity distinguishes low-energy from high-energy listeners. Optional features are ignored when no target is supplied rather than silently guessing preferences. Three scoring strategies and artist diversity make it easy to see how design decisions change the output. Validation and deterministic tie-breaking make runs reproducible.

## 6. Limitations and Bias

The catalog has only 20 illustrative tracks and overrepresents lofi relative to most other genres. Genre-first ranking favors exact category matches even when a different genre better fits the user's mood. Numeric labels compress subjective musical qualities into simple scales and do not represent lyrics, culture, language, or changing context. Popularity targets can favor already-visible tracks, although low targets can also support novelty. These limitations mean a high score is an explanation of the rule, not evidence of real-world recommendation quality.

The artist penalty improves exposure diversity by preventing near-identical tracks from one artist from automatically occupying the first two slots. In the EDM example, top-two unique artists increase from one to two. This is a modest variety mechanism; it neither measures nor guarantees fairness across demographic groups and does not eliminate genre filter bubbles. The reliable mode may abstain unnecessarily for unfamiliar genre labels, and its threshold needs real feedback for calibration.

## 7. Evaluation

Three full profile outputs with five recommendations each are included as text in the README. The tests cover the original object API, loading, ordering, explanations, input bounds, duplicate IDs, invalid CSV, every added feature, and corrupted output. The evaluation script checks nine named behaviors. The recorded run passed 35 pytest tests and 9/9 evaluation scenarios.

Pairwise profile comparisons:

- **Pop vs. lofi:** Golden Hour Ride leads pop, while Paper Moon Loop leads lofi. The lofi profile prefers lower energy, slower tempo, higher acousticness and instrumentalness, and lower popularity. Their top-five lists have no shared songs.
- **Pop vs. EDM:** The pop list starts with happy songs around 120 BPM. EDM starts with intense, highly danceable tracks around 145 BPM. Gym Hero appears in both top-five lists because its pop genre helps one profile while its intense mood and high energy help the other.
- **Lofi vs. EDM:** Lofi favors Paper Moon Loop, Library Rain, and Midnight Coding; EDM favors Electric Horizon, Bassline Orbit, and Festival Afterglow. Their targets for energy, tempo and acousticness differ substantially. Their top-five lists have no shared songs.

An instructive result is Gym Hero ranking third for happy pop despite an intense mood. With genre weight 2 and mood weight 1, the genre match can outweigh the mismatch. In mood-first mode, Rooftop Lights becomes third. Halving genre's weight and doubling energy's weight also moves Rooftop Lights ahead because its energy is closer to 0.8. These are sensitivity results, not claims of improved listener satisfaction.

The diversity experiment changes EDM's top two from Electric Horizon / Festival Afterglow (both Pulse Arcade) to Electric Horizon / Bassline Orbit (two artists). Festival Afterglow's displayed score drops from 6.442 to 5.842 and it moves third.

Baseline vs. reliability behavior:

| Input | Baseline | Reliable mode |
| --- | --- | --- |
| Opera/dramatic/energy 0.5 | Returns five songs despite missing opera coverage | Zero songs; explicit coverage abstention |
| Pop, threshold 1.0 | Baseline has no quality gate | Zero songs; no perfect match |
| Pop, k=20 | Returns 20 candidates | Partial list of qualifying candidates |
| Energy 1.4 | Validation error | Validation error |

Audit checks reject altered titles, incorrect scores and generic explanations. They share the scorer with ranking, so they catch corruption and consistency problems but cannot independently prove that the scoring formula itself models taste correctly. Tests are behavioral checks on handcrafted examples, not unbiased generalization estimates.

## 8. Future Work

Add more genres and culturally varied recordings with verified metadata. Use listener feedback to choose weights and calibrate the reliability threshold. Support multiple genres, mood tags, language preferences, and context such as studying or exercise. Compare diversity settings using both listener satisfaction and artist exposure metrics. Evaluate on held-out users if a learned model is introduced, and collect listening data only with consent.

## 9. Reflection on Design and AI Collaboration

This project illustrates how a simple weighted rule can produce convincing-looking recommendations while still encoding strong assumptions. Explaining the points makes those assumptions easier to question. The model's flexibility comes from separating data, scoring, ranking, and reliability checks rather than hiding everything in one loop.

AI generated the code, test cases, and documentation in this development session. The user supplied the assignment and corrected the initial standalone-project direction by providing the actual CodePath starter. The agent accepted the shared Strategy configuration design and revised the standalone approach to preserve the supplied dataset, starter interfaces, and tests. The detailed collaboration log records those decisions without claiming unobserved personal listening experiments or manual student verification.
