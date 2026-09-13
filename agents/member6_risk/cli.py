from __future__ import annotations

import argparse
import json
from pathlib import Path

from .baseline import fit_baselines, save_baselines
from .engine import RiskEngine
from .evaluation import evaluate_temporal_holdout, save_evaluation
from .hydromet import build_hydromet_calibration, read_hydromet_daily, save_hydromet_calibration, write_hydromet_jsonl
from .models import RiskRequest
from .normalizer import iter_dataset_readings, write_jsonl


def command_prepare(args: argparse.Namespace) -> None:
    readings = list(iter_dataset_readings(args.input))
    counts = write_jsonl(readings, args.output)
    print(json.dumps({"readings": len(readings), "by_structure": counts, "output": args.output}, indent=2))


def command_train(args: argparse.Namespace) -> None:
    readings = list(iter_dataset_readings(args.input))
    model = fit_baselines(readings, minimum_samples=args.minimum_samples)
    save_baselines(model, args.output)
    print(json.dumps({key: value for key, value in model.items() if key != "profiles"}, indent=2))


def command_score(args: argparse.Namespace) -> None:
    payload = RiskRequest.model_validate_json(Path(args.request).read_text(encoding="utf-8"))
    response = RiskEngine(args.baseline, hydromet_baseline_path=args.hydromet_baseline).assess(payload)
    print(response.model_dump_json(indent=2))


def command_evaluate(args: argparse.Namespace) -> None:
    report = evaluate_temporal_holdout(iter_dataset_readings(args.input))
    save_evaluation(report, args.output)
    print(json.dumps(report, indent=2))


def command_prepare_hydromet(args: argparse.Namespace) -> None:
    observations = read_hydromet_daily(args.input)
    count = write_hydromet_jsonl(observations, args.output)
    print(json.dumps({"readings": count, "output": args.output}, indent=2))


def command_calibrate_hydromet(args: argparse.Namespace) -> None:
    calibration = build_hydromet_calibration(read_hydromet_daily(args.input))
    save_hydromet_calibration(calibration, args.output)
    print(json.dumps({key: value for key, value in calibration.items() if key != "monthly_profiles"}, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hydrosafe-risk", description="HydroSafe risk calibration and scoring")
    commands = parser.add_subparsers(required=True)
    prepare = commands.add_parser("prepare", help="normalize supported instrument sheets to JSONL")
    prepare.add_argument("--input", required=True)
    prepare.add_argument("--output", required=True)
    prepare.set_defaults(func=command_prepare)
    train = commands.add_parser("train", help="fit robust historical baseline profiles")
    train.add_argument("--input", required=True)
    train.add_argument("--output", required=True)
    train.add_argument("--minimum-samples", type=int, default=12)
    train.set_defaults(func=command_train)
    evaluate = commands.add_parser("evaluate", help="run chronological holdout and synthetic monotonic checks")
    evaluate.add_argument("--input", required=True)
    evaluate.add_argument("--output", required=True)
    evaluate.set_defaults(func=command_evaluate)
    hydromet_prepare = commands.add_parser("prepare-hydromet", help="normalize the reviewed daily legacy XLS table to JSONL")
    hydromet_prepare.add_argument("--input", required=True)
    hydromet_prepare.add_argument("--output", required=True)
    hydromet_prepare.set_defaults(func=command_prepare_hydromet)
    hydromet_calibrate = commands.add_parser("calibrate-hydromet", help="fit monthly context profiles from the daily legacy XLS table")
    hydromet_calibrate.add_argument("--input", required=True)
    hydromet_calibrate.add_argument("--output", required=True)
    hydromet_calibrate.set_defaults(func=command_calibrate_hydromet)
    score = commands.add_parser("score", help="score a JSON request")
    score.add_argument("--baseline", required=True)
    score.add_argument("--hydromet-baseline")
    score.add_argument("--request", required=True)
    score.set_defaults(func=command_score)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
