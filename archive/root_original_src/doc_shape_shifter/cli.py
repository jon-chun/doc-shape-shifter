from __future__ import annotations

import argparse
from pathlib import Path

from .core.router import ConversionRouter
from .core.types import ConversionRequest, detect_format, normalize_format
from .engines import detect_tooling


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="doc-shape-shifter")
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor_parser = subparsers.add_parser("doctor", help="Show detected conversion engines")
    doctor_parser.set_defaults(func=run_doctor)

    plan_parser = subparsers.add_parser("plan", help="Show ranked conversion routes")
    add_conversion_arguments(plan_parser)
    plan_parser.set_defaults(func=run_plan)

    convert_parser = subparsers.add_parser("convert", help="Convert a document")
    add_conversion_arguments(convert_parser)
    convert_parser.set_defaults(func=run_convert)

    return parser


def add_conversion_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--from", dest="source_format")
    parser.add_argument("--to", dest="target_format")
    parser.add_argument("--force-ocr", action="store_true", help="Force OCR-oriented PDF extraction")
    parser.add_argument("--prefer-engine", help="Boost a specific engine in ranking")


def build_request(args: argparse.Namespace) -> ConversionRequest:
    source_format = normalize_format(args.source_format) if args.source_format else detect_format(args.input)
    target_format = normalize_format(args.target_format) if args.target_format else detect_format(args.output)
    return ConversionRequest(
        input_path=args.input,
        output_path=args.output,
        source_format=source_format,
        target_format=target_format,
        force_ocr=args.force_ocr,
        prefer_engine=args.prefer_engine.lower() if args.prefer_engine else None,
    )


def run_doctor(_: argparse.Namespace) -> int:
    tooling = detect_tooling()
    for name, status in tooling.items():
        flag = "yes" if status.available else "no"
        version = f" ({status.version})" if status.version else ""
        print(f"{name:12} available={flag:3} {status.detail}{version}")
    return 0


def run_plan(args: argparse.Namespace) -> int:
    request = build_request(args)
    router = ConversionRouter()
    plans = router.rank_plans(request)
    if not plans:
        print("No valid conversion plans found.")
        return 1
    for index, plan in enumerate(plans, start=1):
        print(f"{index}. {plan.route_name} score={plan.score}")
        for step in plan.steps:
            print(f"   - {step.engine}: {step.action} ({step.detail})")
    return 0


def run_convert(args: argparse.Namespace) -> int:
    request = build_request(args)
    router = ConversionRouter()
    plan = router.convert(request)
    print(f"Selected route: {plan.route_name} (score={plan.score})")
    print(f"Wrote: {request.output_path}")
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
