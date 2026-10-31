"""Run the recommender from the repository root: python -m src.main."""
import argparse
import json
import textwrap
from pathlib import Path
from .profiles import PROFILES
from .recommender import STRATEGIES, load_songs, recommend_songs

CATALOG = Path(__file__).resolve().parents[1] / 'data' / 'songs.csv'


def format_table(rows):
    """Format scores and their complete reasons without external dependencies."""
    lines = [f'{"#":<3} {"Song / Artist":<43} {"Score":>7}  Reasons', '-' * 115]
    for rank, (song, score, reason) in enumerate(rows, 1):
        label = f'{song["title"]} / {song["artist"]}'
        labels = textwrap.wrap(label, 43)
        reasons = textwrap.wrap(reason, 58)
        for i in range(max(len(labels), len(reasons))):
            lines.append(f'{str(rank) if i == 0 else "":<3} '
                         f'{labels[i] if i < len(labels) else "":<43} '
                         f'{format(score, ".3f") if i == 0 else "":>7}  '
                         f'{reasons[i] if i < len(reasons) else ""}')
        lines.append('')
    return '\n'.join(lines).rstrip()


def main(argv=None):
    """Choose a profile, strategy and optional Project 4 reliability checks."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', choices=PROFILES, default='pop')
    parser.add_argument('--prefs', type=Path, help='JSON profile; overrides --profile')
    parser.add_argument('--mode', choices=STRATEGIES, default='genre-first')
    parser.add_argument('--k', type=int, default=5)
    parser.add_argument('--artist-penalty', type=float, default=0.6)
    parser.add_argument('--catalog', type=Path, default=CATALOG)
    parser.add_argument('--reliable', action='store_true')
    parser.add_argument('--min-match', type=float, default=0.7)
    parser.add_argument('--trace', type=Path, help='Save Project 4 audit events as JSON')
    args = parser.parse_args(argv)
    try:
        if args.trace and not args.reliable:
            raise ValueError('--trace requires --reliable')
        prefs = json.loads(args.prefs.read_text()) if args.prefs else PROFILES[args.profile]
        songs = load_songs(args.catalog)
        print(f'Loaded songs: {len(songs)}')
        print(f'Profile: {args.prefs.name if args.prefs else args.profile} | mode: {args.mode}')
        if args.reliable:
            from .reliability import reliable_recommend
            report = reliable_recommend(prefs, songs, args.k, args.mode,
                                        args.artist_penalty, args.min_match)
            rows = report['recommendations']
            print(f'Status: {report["status"]} | {report["message"]}')
            if args.trace:
                args.trace.parent.mkdir(parents=True, exist_ok=True)
                args.trace.write_text(json.dumps(report['events'], indent=2) + '\n')
        else:
            rows = recommend_songs(prefs, songs, args.k, args.mode, args.artist_penalty)
        if rows:
            print(format_table(rows))
    except (ValueError, OSError) as exc:
        parser.exit(2, f'Error: {exc}\n')


if __name__ == '__main__':
    main()
