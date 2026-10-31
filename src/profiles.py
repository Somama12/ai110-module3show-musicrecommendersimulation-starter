"""Three contrasting synthetic taste profiles; these are not personal listening data."""
PROFILES = {
    'pop': dict(genre='pop', mood='happy', energy=0.8, tempo_bpm=120,
                valence=0.85, danceability=0.8, acousticness=0.2,
                instrumentalness=0.05, popularity=80, release_year=2022,
                duration_seconds=210, live_performance=0),
    'lofi': dict(genre='lofi', mood='chill', energy=0.35, tempo_bpm=75,
                 valence=0.55, danceability=0.5, acousticness=0.85,
                 instrumentalness=0.9, popularity=30, release_year=2020,
                 duration_seconds=180, live_performance=0),
    'edm': dict(genre='edm', mood='intense', energy=0.95, tempo_bpm=145,
                valence=0.65, danceability=0.95, acousticness=0.05,
                instrumentalness=0.7, popularity=65, release_year=2023,
                duration_seconds=240, live_performance=1),
}
