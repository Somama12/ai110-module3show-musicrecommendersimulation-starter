"""Run a reproducible behavior evaluation: python -m src.evaluate."""
from .main import CATALOG
from .profiles import PROFILES
from .recommender import load_songs, recommend_songs
from .reliability import reliable_recommend


def main():
    """Evaluate profiles, diversity, abstention, validation and strategy changes."""
    songs = load_songs(CATALOG)
    results = []
    for name, prefs in PROFILES.items():
        report = reliable_recommend(prefs, songs, k=3)
        rows = report['recommendations']
        good = len(rows) == 3 and rows[0][0]['genre'] == prefs['genre']
        results.append((f'{name}: top genre and three reliable results', good))
    unsupported = {'genre': 'opera', 'mood': 'dramatic', 'energy': .5}
    results.append(('unsupported genre: abstain', reliable_recommend(unsupported, songs)['status'] == 'abstained'))
    results.append(('strict threshold: abstain', reliable_recommend(PROFILES['pop'], songs, min_match=1)['status'] == 'abstained'))
    results.append(('partial result: no weak padding', reliable_recommend(PROFILES['pop'], songs, k=20)['status'] == 'partial'))
    try:
        reliable_recommend({**PROFILES['pop'], 'energy': 1.4}, songs)
        invalid_rejected = False
    except ValueError:
        invalid_rejected = True
    results.append(('invalid energy: rejected', invalid_rejected))
    base = recommend_songs(PROFILES['edm'], songs, 2, artist_penalty=0)
    diverse = recommend_songs(PROFILES['edm'], songs, 2, artist_penalty=.6)
    results.append(('artist diversity: increases top-two unique artists',
                    len({s['artist'] for s, _, _ in diverse}) > len({s['artist'] for s, _, _ in base})))
    genre = recommend_songs(PROFILES['pop'], songs, 3, 'genre-first')
    mood = recommend_songs(PROFILES['pop'], songs, 3, 'mood-first')
    results.append(('mode switch: changes top-three selection', [r[0]['id'] for r in genre] != [r[0]['id'] for r in mood]))
    for name, passed in results:
        print(f'{"PASS" if passed else "FAIL"} | {name}')
    passed = sum(ok for _, ok in results)
    print(f'\nEvaluation: {passed}/{len(results)} passed')
    return 0 if passed == len(results) else 1


if __name__ == '__main__':
    raise SystemExit(main())
