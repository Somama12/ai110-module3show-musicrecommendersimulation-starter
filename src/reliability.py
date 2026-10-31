"""Project 4: validate, gate weak matches, rank, and audit recommendations."""
import math
from .recommender import (validate_preferences, validate_song, score_song,
                          recommend_songs, max_score, get_strategy, _number)


def audit_output(prefs, songs, rows, k, mode, penalty, threshold):
    """Independently check output membership, uniqueness, scores and explanations."""
    catalog = {s['id']: s for s in songs}
    if len(rows) > k or len({s['id'] for s, _, _ in rows}) != len(rows):
        raise ValueError('output audit failed: count or duplicate IDs')
    counts, previous = {}, math.inf
    ceiling = max_score(prefs, mode)
    for song, score, reason in rows:
        if catalog.get(song['id']) != song:
            raise ValueError('output audit failed: song is not in catalog')
        base, parts = score_song(prefs, song, mode)
        artist = song['artist'].casefold()
        deduction = penalty * counts.get(artist, 0)
        expected_reason = '; '.join(parts + [f'artist repeat penalty (-{deduction:.3f}); base {base:.3f}'])
        if not math.isfinite(score) or not math.isclose(score, base - deduction, abs_tol=1e-9):
            raise ValueError('output audit failed: incorrect score')
        if score > previous + 1e-9 or base / ceiling < threshold:
            raise ValueError('output audit failed: order or match threshold')
        if reason != expected_reason:
            raise ValueError('output audit failed: explanation does not match score')
        counts[artist] = counts.get(artist, 0) + 1
        previous = score


def reliable_recommend(prefs, songs, k=5, mode='genre-first', artist_penalty=0.6, min_match=0.7):
    """Apply a deterministic reliability pipeline and return an auditable report."""
    validate_preferences(prefs)
    get_strategy(mode)
    _number(min_match, 'min_match', 0, 1)
    _number(artist_penalty, 'artist_penalty', 0, 10)
    if type(k) is not int or k < 1:
        raise ValueError('k must be a positive integer')
    for song in songs:
        validate_song(song)
    if len({s['id'] for s in songs}) != len(songs):
        raise ValueError('song IDs must be unique')
    events = [{'stage': 'validate', 'result': 'passed', 'catalog_size': len(songs)}]
    # Require a catalog genre match in reliable mode; baseline still allows exploration.
    eligible_genre = [s for s in songs if s['genre'].strip().casefold() == prefs['genre'].strip().casefold()]
    if not eligible_genre:
        events.append({'stage': 'coverage', 'result': 'abstain', 'genre': prefs['genre']})
        return {'status': 'abstained', 'message': 'Requested genre is not represented in the catalog.',
                'recommendations': [], 'events': events}
    ceiling = max_score(prefs, mode)
    # A normalized heuristic match score is NOT a probability of user satisfaction.
    eligible = [s for s in songs if score_song(prefs, s, mode)[0] / ceiling >= min_match]
    events.append({'stage': 'match_gate', 'threshold': min_match, 'eligible': len(eligible),
                   'rejected': len(songs) - len(eligible)})
    rows = recommend_songs(prefs, eligible, k, mode, artist_penalty)
    audit_output(prefs, songs, rows, k, mode, artist_penalty, min_match)
    events.append({'stage': 'rank_and_audit', 'result': 'passed',
                   'selected_ids': [s['id'] for s, _, _ in rows],
                   'scores': [round(score, 6) for _, score, _ in rows]})
    status = 'ok' if len(rows) == k else ('partial' if rows else 'abstained')
    return {'status': status, 'message': f'{len(rows)} of {k} requested songs meet match >= {min_match:.2f}.',
            'recommendations': rows, 'events': events}
