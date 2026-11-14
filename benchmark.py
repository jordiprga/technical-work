#!/usr/bin/env python3
"""Reproducible chronological adversarial prediction benchmark."""
import argparse
import json
from pathlib import Path
from entropy_oracle.experiment import run_experiment, save_result
from entropy_oracle.sources import SOURCE_NAMES


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',default='nonlinear',choices=SOURCE_NAMES)
    parser.add_argument('--models',default='all',help='all or comma-separated model names')
    parser.add_argument('--n',type=int,default=12000)
    parser.add_argument('--seed',type=int,default=11)
    parser.add_argument('--seeds',help='Comma-separated independent seeds; overrides --seed')
    parser.add_argument('--window',type=int,default=32)
    parser.add_argument('--epochs',type=int,default=15)
    parser.add_argument('--params',default='{}',help='JSON source parameters')
    parser.add_argument('--bootstrap',type=int,default=300)
    parser.add_argument('--learning-sizes',help='Comma-separated training prefix sizes; same validation/test, exploratory')
    parser.add_argument('--output',default='results',help='Output directory')
    args=parser.parse_args()
    seeds=[int(v) for v in args.seeds.split(',')] if args.seeds else [args.seed]
    sizes=[int(v) for v in args.learning_sizes.split(',')] if args.learning_sizes else [None]
    for seed in seeds:
        for size in sizes:
            result=run_experiment(source=args.source,n=args.n,seed=seed,models=args.models,
                window=args.window,epochs=args.epochs,source_params=json.loads(args.params),
                bootstrap=args.bootstrap,train_size=size,progress=lambda text:print(text,flush=True))
            suffix=f'_train{size}' if size else ''
            path=Path(args.output)/f'{args.source}_seed{seed}_n{args.n}{suffix}.json'
            save_result(result,path)
            print('\nModel              Accuracy  Log-loss(bits)  Fit(s)')
            for row in result['metrics']:
                print(f'{row["model"]:18s} {row["accuracy"]:8.4f} {row["log_loss_bits"]:15.4f} {row["fit_seconds"]:7.2f}')
            print(f'Selected on validation: {result["selection"]["selected_model"]}; saved {path}',flush=True)

if __name__=='__main__':
    main()
