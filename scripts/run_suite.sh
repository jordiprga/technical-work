#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python benchmark.py --source nonlinear --models all --n 12000 --seeds 211,229,247 --epochs 15 --output results/v2/main
python benchmark.py --source bernoulli --models all --n 1600 --seeds 211,229,247 --params '{"p":0.8}' --output results/v2/iid
python benchmark.py --source ar1 --models all --n 12000 --seeds 211,229,247 --epochs 15 --output results/v2/ar1
python benchmark.py --source nonlinear --models marginal,markov5,gb,mlp,gru,transformer,flow --n 12000 --seed 201 --epochs 15 --learning-sizes 500,1500,4000,7000 --output results/v2/learning
python scripts/summarize.py
python scripts/verify_results.py results/v2 --require-audit
