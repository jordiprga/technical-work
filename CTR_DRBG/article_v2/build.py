"""Compile the saved manuscript with an installed Tectonic compiler."""
from pathlib import Path
import argparse
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument("--compiler", default="tectonic")
args = parser.parse_args()
subprocess.run([args.compiler, "main.tex", "--keep-logs", "--keep-intermediates", "--reruns", "2"], cwd=Path(__file__).resolve().parent, check=True)
