#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python benchmark.py --source nonlinear --models all --n 12000 --seeds 11,29,47 --epochs 15 --output results/main
python benchmark.py --source bernoulli --models all --n 1600 --seeds 11,29,47 --params '{"p":0.8}' --output results/iid
python benchmark.py --source ar1 --models all --n 12000 --seeds 11,29,47 --epochs 15 --output results/ar1
python benchmark.py --source nonlinear --models marginal,markov5,gb,mlp,gru,transformer,flow --n 12000 --seed 101 --epochs 15 --learning-sizes 500,1500,4000,7000 --output results/learning
python scripts/summarize.py
