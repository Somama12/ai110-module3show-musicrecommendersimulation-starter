"""Explainable content-based ranking, with functional and starter OOP interfaces."""
import csv
import math
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

# Fixed scales make feature contributions comparable across songs and profiles.
RANGES = {
    'energy': (0, 1), 'tempo_bpm': (40, 220), 'valence': (0, 1),
    'danceability': (0, 1), 'acousticness': (0, 1),
    'instrumentalness': (0, 1), 'popularity': (0, 100),
    'release_year': (1950, 2030), 'duration_seconds': (60, 600),
    'live_performance': (0, 1),
}
BASE_WEIGHTS = {'genre': 2.0, 'mood': 1.0, 'energy': 1.0, 'tempo_bpm': 0.5,
                **{f: 0.25 for f in RANGES if f not in ('energy', 'tempo_bpm')}}


@dataclass(frozen=True)
class RankingStrategy:
    """A configurable Strategy object supplies feature weights to one scorer."""
    name: str
    weights: dict


STRATEGIES = {
    'genre-first': RankingStrategy('genre-first', BASE_WEIGHTS),
    'mood-first': RankingStrategy('mood-first', {**BASE_WEIGHTS, 'genre': 1.0, 'mood': 2.0}),
    'energy-first': RankingStrategy('energy-first', {**BASE_WEIGHTS, 'genre': 1.0, 'energy': 2.0}),
}


@dataclass
class Song:
    """Represent a catalog song; defaults preserve compatibility with starter tests."""
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
    instrumentalness: float = 0.0
    popularity: float = 50.0
    release_year: float = 2020.0
    duration_seconds: float = 210.0
    live_performance: float = 0.0


@dataclass
class UserProfile:
    """Represent the starter taste profile and optional numeric targets."""
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool

    def preferences(self):
        """Translate the starter object to the shared dictionary interface."""
        return {'genre': self.favorite_genre, 'mood': self.favorite_mood,
                'energy': self.target_energy, 'acousticness': 1.0 if self.likes_acoustic else 0.0}


def _number(value, name, low, high):
    """Reject nonnumeric, nonfinite, boolean and out-of-range numeric inputs."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f'{name} must be a number')
    if not math.isfinite(value) or not low <= value <= high:
        raise ValueError(f'{name} must be between {low} and {high}')


def validate_preferences(prefs):
    """Validate explicit preferences without silently filling in unknown tastes."""
    if not isinstance(prefs, dict):
        raise ValueError('preferences must be a JSON object')
    unknown = set(prefs) - {'genre', 'mood', *RANGES}
    if unknown:
        raise ValueError('unknown preferences: ' + ', '.join(sorted(unknown)))
    if not {'genre', 'mood', 'energy'} <= prefs.keys():
        raise ValueError('preferences require genre, mood, and energy')
    for key in ('genre', 'mood'):
        if not isinstance(prefs[key], str) or not prefs[key].strip():
            raise ValueError(f'{key} must be nonempty text')
    for key in RANGES.keys() & prefs.keys():
        _number(prefs[key], key, *RANGES[key])


def validate_song(song):
    """Validate a complete song schema before scoring or loading it."""
    if not isinstance(song, dict):
        raise ValueError('song must be a dictionary')
    required = {'id', 'title', 'artist', 'genre', 'mood', *RANGES}
    if not required <= song.keys():
        raise ValueError('song is missing required fields')
    if type(song['id']) is not int or song['id'] < 1:
        raise ValueError('song id must be a positive integer')
    for key in ('title', 'artist', 'genre', 'mood'):
        if not isinstance(song[key], str) or not song[key].strip():
            raise ValueError(f'{key} must be nonempty text')
    for key, bounds in RANGES.items():
        _number(song[key], key, *bounds)
    if song['live_performance'] not in (0, 1):
        raise ValueError('live_performance must be 0 or 1')


def load_songs(csv_path):
    """Load validated CSV rows into dictionaries with numeric features converted."""
    songs = []
    with Path(csv_path).open(newline='', encoding='utf-8') as stream:
        reader = csv.DictReader(stream)
        required = {'id', 'title', 'artist', 'genre', 'mood', *RANGES}
        if not required <= set(reader.fieldnames or []):
            raise ValueError('CSV is missing required columns')
        for line, row in enumerate(reader, start=2):
            try:
                if None in row or any(value is None for value in row.values()):
                    raise ValueError('wrong number of CSV fields')
                song = dict(row)
                song['id'] = int(song['id'])
                for field in RANGES:
                    song[field] = float(song[field])
                validate_song(song)
                songs.append(song)
            except (ValueError, TypeError) as exc:
                raise ValueError(f'CSV line {line}: {exc}') from exc
    if not songs:
        raise ValueError('catalog must contain at least one song')
    if len({s['id'] for s in songs}) != len(songs):
        raise ValueError('song IDs must be unique')
    return songs


def get_strategy(mode):
    """Resolve a mode name or reject an unsupported mode."""
    if mode not in STRATEGIES:
        raise ValueError('unknown ranking mode: ' + str(mode))
    return STRATEGIES[mode]


def max_score(prefs, mode='genre-first'):
    """Return the maximum score for only the user's supplied features."""
    return sum(get_strategy(mode).weights[f] for f in prefs)


def score_song(user_prefs, song, mode='genre-first'):
    """Return numeric relevance and exact feature-based reasons for one song."""
    validate_preferences(user_prefs)
    validate_song(song)
    weights = get_strategy(mode).weights
    total, reasons = 0.0, []
    for field, weight in weights.items():
        if field not in user_prefs:
            continue
        if field in ('genre', 'mood'):
            same = song[field].strip().casefold() == user_prefs[field].strip().casefold()
            points = weight if same else 0.0
            detail = f'{field} {"match" if same else "mismatch"} ({song[field]})'
        else:
            low, high = RANGES[field]
            similarity = 1 - abs(song[field] - user_prefs[field]) / (high - low)
            points = weight * similarity
            detail = f'{field} {song[field]:g} vs target {user_prefs[field]:g}'
        total += points
        reasons.append(f'{detail} (+{points:.3f})')
    return total, reasons


def recommend_songs(user_prefs, songs, k=5, mode='genre-first', artist_penalty=0.0):
    """Greedily rank songs by relevance minus a penalty per selected artist repeat."""
    validate_preferences(user_prefs)
    get_strategy(mode)
    if type(k) is not int or k < 1:
        raise ValueError('k must be a positive integer')
    _number(artist_penalty, 'artist_penalty', 0, 10)
    candidates = [(song, *score_song(user_prefs, song, mode)) for song in songs]
    if len({song['id'] for song, _, _ in candidates}) != len(candidates):
        raise ValueError('song IDs must be unique')
    chosen, counts = [], Counter()
    while candidates and len(chosen) < k:
        def adjusted(item):
            return item[1] - artist_penalty * counts[item[0]['artist'].casefold()]
        # sorted() creates a new list; unlike list.sort(), it doesn't mutate the catalog.
        candidates = sorted(candidates, key=lambda item: (-adjusted(item), item[0]['id']))
        song, base, reasons = candidates.pop(0)
        penalty = artist_penalty * counts[song['artist'].casefold()]
        explanation = reasons + [f'artist repeat penalty (-{penalty:.3f}); base {base:.3f}']
        chosen.append((song, base - penalty, '; '.join(explanation)))
        counts[song['artist'].casefold()] += 1
    return chosen


class Recommender:
    """Adapt starter Song/UserProfile objects to the shared scoring implementation."""
    def __init__(self, songs):
        self.songs = songs

    def recommend(self, user, k=5):
        """Return Song objects sorted by the same score used by the CLI."""
        rows = recommend_songs(user.preferences(), [asdict(s) for s in self.songs], k)
        by_id = {s.id: s for s in self.songs}
        return [by_id[row[0]['id']] for row in rows]

    def explain_recommendation(self, user, song):
        """Explain a Song using the shared scorer rather than a separate rule."""
        return '; '.join(score_song(user.preferences(), asdict(song))[1])
