from __future__ import annotations

import argparse
from pathlib import Path

from .ingest import build_demo_catalog, download_sources


def _cmd_download(args: argparse.Namespace) -> int:
    paths = download_sources(out_dir=args.out, obf_max_lines=args.obf_max_lines)
    print(f"DOWNLOADED {len(paths)} files to {args.out}")
    for p in paths:
        print(f"- {p}")
    return 0


def _cmd_build_demo(args: argparse.Namespace) -> int:
    stats = build_demo_catalog(
        raw_dir=args.raw_dir,
        out_path=args.out,
        max_products=args.max_products,
        seed=args.seed,
    )
    print(
        "BUILD_OK",
        f"bdpm_rows={stats.bdpm_rows}",
        f"obf_rows={stats.obf_rows}",
        f"merged_rows={stats.merged_rows}",
        f"out={args.out}",
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pharmassist-catalog-fr")
    sub = parser.add_subparsers(dest="cmd", required=True)

    dl = sub.add_parser("download-sources", help="Download BDPM + OBF source files.")
    dl.add_argument("--out", type=Path, required=True, help="Output directory for raw files.")
    dl.add_argument(
        "--obf-max-lines",
        type=int,
        default=200000,
        help="Max OBF CSV lines to keep locally (header included).",
    )
    dl.set_defaults(func=_cmd_download)

    build = sub.add_parser("build-demo", help="Build deterministic demo catalog JSON.")
    build.add_argument(
        "--raw-dir",
        type=Path,
        required=True,
        help="Directory containing source files.",
    )
    build.add_argument("--out", type=Path, required=True, help="Output products.demo.json path.")
    build.add_argument("--max-products", type=int, default=500, help="Max products to include.")
    build.add_argument("--seed", type=int, default=42, help="Deterministic seed.")
    build.set_defaults(func=_cmd_build_demo)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
