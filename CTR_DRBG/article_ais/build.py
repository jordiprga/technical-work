"""Build the manuscript with Tectonic; no sources are downloaded by this script."""
from pathlib import Path
import argparse
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('--compiler', default='tectonic')
parser.add_argument('--review-jordi', action='store_true',
                    help='Build the temporary edition with Jordi review notes')
args = parser.parse_args()
subprocess.run([args.compiler, 'review-jordi.tex' if args.review_jordi else 'main.tex', '--keep-logs', '--keep-intermediates',
                '--reruns', '2'], cwd=Path(__file__).resolve().parent, check=True)
