"""Behavior tests for ranking, validation and the Project 4 reliability layer."""
import csv
import json
import math
import subprocess
import sys
from copy import deepcopy
from dataclasses import asdict
import pytest
from src.main import CATALOG
from src.profiles import PROFILES
from src.recommender import load_songs, score_song, recommend_songs, max_score, RANGES
from src.reliability import reliable_recommend, audit_output


@pytest.fixture
def songs():
    return load_songs(CATALOG)


def test_catalog_preserves_starter_and_expands(songs):
    assert len(songs) == 20
    assert songs[0]['title'] == 'Sunrise City'
    assert songs[9]['title'] == 'Rooftop Lights'
    assert len({s['id'] for s in songs}) == 20
    assert all(isinstance(s[f], float) for s in songs for f in RANGES)


def test_exact_match_gets_maximum(songs):
    song = songs[0]
    prefs = {key: song[key] for key in ('genre', 'mood', *RANGES)}
    score, reasons = score_song(prefs, song)
    assert score == pytest.approx(max_score(prefs))
    assert len(reasons) == len(prefs)


def test_energy_similarity_rewards_closeness(songs):
    prefs = {'genre': 'pop', 'mood': 'happy', 'energy': .8}
    exact = {**songs[0], 'energy': .8}
    high = {**exact, 'energy': 1.0}
    low = {**exact, 'energy': .6}
    assert score_song(prefs, exact)[0] > score_song(prefs, high)[0]
    assert score_song(prefs, high)[0] == pytest.approx(score_song(prefs, low)[0])


@pytest.mark.parametrize('field', ['instrumentalness','popularity','release_year','duration_seconds','live_performance'])
def test_every_added_attribute_changes_score(songs, field):
    prefs = {**PROFILES['pop'], field: RANGES[field][0]}
    close = {**songs[0], field: RANGES[field][0]}
    far = {**close, field: RANGES[field][1]}
    assert score_song(prefs, close)[0] - score_song(prefs, far)[0] == pytest.approx(.25)


@pytest.mark.parametrize('name', PROFILES)
def test_profiles_sorted_explained_and_nonmutating(songs, name):
    original = deepcopy(songs)
    rows = recommend_songs(PROFILES[name], songs, k=5, artist_penalty=.6)
    assert len(rows) == 5
    assert [r[1] for r in rows] == sorted([r[1] for r in rows], reverse=True)
    assert rows[0][0]['genre'] == name
    assert all('target' in r[2] and 'artist repeat penalty' in r[2] for r in rows)
    assert songs == original


def test_diversity_changes_selection(songs):
    plain = recommend_songs(PROFILES['edm'], songs, 2)
    varied = recommend_songs(PROFILES['edm'], songs, 2, artist_penalty=.6)
    assert len({r[0]['artist'] for r in plain}) == 1
    assert len({r[0]['artist'] for r in varied}) == 2


def test_deterministic_ties(songs):
    copies = [{**songs[0], 'id': i} for i in [3, 1, 2]]
    assert [r[0]['id'] for r in recommend_songs(PROFILES['pop'], copies, 3)] == [1, 2, 3]


@pytest.mark.parametrize('energy', [-.1, 1.1, float('nan'), float('inf'), True, 'high'])
def test_invalid_energy_rejected(songs, energy):
    with pytest.raises(ValueError):
        recommend_songs({**PROFILES['pop'], 'energy': energy}, songs)


@pytest.mark.parametrize('k', [0, -1, True, 1.5])
def test_invalid_k(songs, k):
    with pytest.raises(ValueError):
        recommend_songs(PROFILES['pop'], songs, k=k)


def test_empty_and_oversized_requests(songs):
    assert recommend_songs(PROFILES['pop'], []) == []
    assert len(recommend_songs(PROFILES['pop'], songs, 100)) == 20
    assert reliable_recommend(PROFILES['pop'], [])['status'] == 'abstained'


def test_unknown_keys_and_missing_preferences(songs):
    for prefs in ({'genre': 'pop'}, {**PROFILES['pop'], 'enerjy': .2}, []):
        with pytest.raises(ValueError):
            recommend_songs(prefs, songs)


def test_bad_mode_and_duplicate_ids(songs):
    with pytest.raises(ValueError):
        recommend_songs(PROFILES['pop'], songs, mode='bad')
    with pytest.raises(ValueError):
        recommend_songs(PROFILES['pop'], songs + [songs[0]])


def test_csv_validation(tmp_path):
    path = tmp_path / 'bad.csv'
    path.write_text('id,title\n1,A\n')
    with pytest.raises(ValueError, match='columns'):
        load_songs(path)
    text = CATALOG.read_text()
    path.write_text(text.replace('0.82,118', 'nan,118', 1))
    with pytest.raises(ValueError, match='CSV line 2'):
        load_songs(path)
    path.write_text(text + text.splitlines()[1] + '\n')
    with pytest.raises(ValueError, match='unique'):
        load_songs(path)


def test_reliable_abstains_instead_of_fabricating(songs):
    prefs = {'genre': 'opera', 'mood': 'dramatic', 'energy': .5}
    assert len(recommend_songs(prefs, songs)) == 5
    assert reliable_recommend(prefs, songs)['recommendations'] == []
    assert reliable_recommend(PROFILES['pop'], songs, min_match=1)['status'] == 'abstained'


def test_partial_results_and_audit_trace(songs):
    report = reliable_recommend(PROFILES['pop'], songs, k=20)
    assert report['status'] == 'partial'
    assert 0 < len(report['recommendations']) < 20
    assert report['events'][-1]['result'] == 'passed'
    json.dumps(report['events'])


@pytest.mark.parametrize('corruption', ['score', 'reason', 'song'])
def test_output_audit_detects_tampering(songs, corruption):
    rows = reliable_recommend(PROFILES['pop'], songs, k=3)['recommendations']
    song, score, reason = rows[0]
    if corruption == 'score': score += 1
    if corruption == 'reason': reason = 'You will love this!'
    if corruption == 'song': song = {**song, 'title': 'Invented title'}
    rows[0] = (song, score, reason)
    with pytest.raises(ValueError, match='output audit failed'):
        audit_output(PROFILES['pop'], songs, rows, 3, 'genre-first', .6, .7)


def test_cli_invalid_input_exits_cleanly():
    result = subprocess.run([sys.executable, '-m', 'src.main', '--prefs', 'examples/invalid.json'], capture_output=True, text=True)
    assert result.returncode == 2
    assert 'energy must be between 0 and 1' in result.stderr
    assert 'Traceback' not in result.stderr
