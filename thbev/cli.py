"""Command-line entry point.

Small on purpose: the value is in the library, and the eventual surface is five
screens, not a terminal. These commands exist so the math can be exercised
against a real export the day one arrives.

    thbev ingest   --file export.csv --location "Townhall - Short North"
    thbev deplete  --file export.csv
    thbev windows  --at 2026-08-30T16:00
    thbev suggest  --file export.csv --vendor superior --counts counts.yaml
    thbev sources
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Sequence

import yaml

from .catalog import load_catalog
from .catalog.loader import Catalog
from .depletion import DepletionEngine
from .ordering import (
    DayContext,
    OrderEngine,
    Weather,
    render_order,
    upcoming_cutoffs,
)
from .ordering.forecast import Buyout
from .sources import FileUploadSource, ToastApiSource


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI. Returns a process exit code."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        return 1
    try:
        return args.handler(args)
    except (ValueError, KeyError, NotImplementedError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="thbev", description=__doc__)
    parser.add_argument("--catalog", help="Directory of catalog YAML to use instead of the packaged seed.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    sub = parser.add_subparsers(dest="command")

    ingest = sub.add_parser("ingest", help="Parse Toast exports and report what was read.")
    _add_file_args(ingest)
    ingest.set_defaults(handler=_cmd_ingest)

    deplete = sub.add_parser("deplete", help="Convert sales to product depletion.")
    _add_file_args(deplete)
    deplete.set_defaults(handler=_cmd_deplete)

    windows = sub.add_parser("windows", help="Show upcoming vendor order cutoffs.")
    windows.add_argument("--at", help="ISO datetime to evaluate from. Defaults to now.")
    windows.add_argument("--days", type=int, default=7)
    windows.set_defaults(handler=_cmd_windows)

    suggest = sub.add_parser("suggest", help="Build a per-vendor order suggestion.")
    _add_file_args(suggest)
    suggest.add_argument("--vendor", help="Vendor key. Omit for every vendor.")
    suggest.add_argument("--at", help="ISO datetime of the ordering moment. Defaults to now.")
    suggest.add_argument("--counts", help="YAML/JSON file of counted on-hand units per product key.")
    suggest.add_argument("--on-order", help="YAML/JSON file of units already on order.")
    suggest.add_argument("--calendar", help="YAML/JSON file of events and weather by date.")
    suggest.add_argument("--counted-at", help="ISO datetime the count was taken.")
    suggest.add_argument("--include-optional-windows", action="store_true")
    suggest.add_argument("--arena-out-of-stock", action="store_true",
                         help="Unlock the OYO direct contact.")
    suggest.set_defaults(handler=_cmd_suggest)

    sources = sub.add_parser("sources", help="Describe the configured sales sources.")
    sources.set_defaults(handler=_cmd_sources)
    return parser


def _add_file_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--file", action="append", required=True,
                        help="Toast export file. Repeatable.")
    parser.add_argument("--location", help="Toast location name to filter to.")
    parser.add_argument("--start", help="First business date (YYYY-MM-DD).")
    parser.add_argument("--end", help="Last business date (YYYY-MM-DD).")


def _catalog(args: argparse.Namespace) -> Catalog:
    return load_catalog(args.catalog)


def _range(args: argparse.Namespace, catalog: Catalog) -> tuple[date, date]:
    if args.start and args.end:
        return date.fromisoformat(args.start), date.fromisoformat(args.end)
    today = date.today()
    monday = today - timedelta(days=today.weekday() + 7)
    return monday, monday + timedelta(days=6)


def _ingest(args: argparse.Namespace, catalog: Catalog):
    source = FileUploadSource(
        args.file,
        location=args.location or catalog.config.location,
        cutoff_hour=catalog.config.business_day_cutoff_hour,
    )
    start, end = _range(args, catalog)
    return source.fetch_sales(start, end)


def _emit(args: argparse.Namespace, payload: dict[str, Any], lines: Sequence[str]) -> int:
    if args.json:
        print(json.dumps(payload, indent=2, default=str))
    else:
        for line in lines:
            print(line)
    return 0


def _cmd_ingest(args: argparse.Namespace) -> int:
    catalog = _catalog(args)
    result = _ingest(args, catalog)
    summary = result.summary()
    lines = [
        f"Files: {', '.join(summary['source_files'])}",
        f"Rows: {summary['rows']}  Total qty: {summary['total_qty']:g}",
        f"Unmapped rows: {summary['unmapped_rows']} ({summary['unmapped_qty']:g} units)",
        f"Voided rows excluded: {summary['voided_rows']}",
        f"Sheets used: {', '.join(summary['sheets_used']) or '(none)'}",
        f"Time dimension: {'yes' if summary['has_time_dimension'] else 'no (PMIX only)'}",
        "",
        "Counters:",
        *[f"  {name}: {value}" for name, value in sorted(summary["counters"].items())],
        "",
        "Issues:",
        *[f"  [{i['severity']}] {i['message']}" for i in summary["issues"]],
    ]
    return _emit(args, summary, lines)


def _cmd_deplete(args: argparse.Namespace) -> int:
    catalog = _catalog(args)
    result = _ingest(args, catalog)
    depletion = DepletionEngine(catalog).deplete(result.rows)
    summary = depletion.summary()
    lines = ["Depleted units by product:"]
    for product_key, units in sorted(summary["units_by_product"].items()):
        product = catalog.product(product_key)
        lines.append(f"  {product.name}: {units:.2f} {product.unit_label}s")
    lines += [
        "",
        f"Unmapped rows: {summary['unmapped_rows']} ({summary['unmapped_qty']:g} units) "
        "-- these need mapping or the order under-counts.",
    ]
    for row in depletion.unmapped[:20]:
        lines.append(f"  {row.key} qty={row.qty} ({row.reason})")
    return _emit(args, summary, lines)


def _cmd_windows(args: argparse.Namespace) -> int:
    catalog = _catalog(args)
    at = datetime.fromisoformat(args.at) if args.at else datetime.now()
    upcoming = upcoming_cutoffs(catalog, at, horizon_days=args.days)
    payload = [
        {
            "cutoff": cutoff.isoformat(),
            "vendor": vendor_key,
            "vendor_name": catalog.vendor(vendor_key).name,
            "window": window.key,
            "optional": window.optional,
            "hours_remaining": round((cutoff - at).total_seconds() / 3600, 1),
        }
        for cutoff, vendor_key, window in upcoming
    ]
    lines = [
        f"{entry['cutoff']}  {entry['vendor_name']:<28} "
        f"{entry['hours_remaining']:>6.1f}h" + ("  (optional)" if entry["optional"] else "")
        for entry in payload
    ]
    return _emit(args, {"cutoffs": payload}, lines)


def _load_mapping_file(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    text = Path(path).read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a mapping at the top level.")
    return data


def _load_calendar(path: str | None) -> dict[date, DayContext]:
    """Read a calendar file into day contexts.

    Expected shape::

        2026-09-05:
          events: [osu_home_football]
          weather: {high_f: 88, sunny: true}
          buyout: {headcount: 120}
          promos: {nutrl: 1.2}
    """
    raw = _load_mapping_file(path)
    calendar: dict[date, DayContext] = {}
    for key, value in raw.items():
        day = key if isinstance(key, date) else date.fromisoformat(str(key))
        value = value or {}
        weather_doc = value.get("weather")
        buyout_doc = value.get("buyout")
        calendar[day] = DayContext(
            day=day,
            events=list(value.get("events", []) or []),
            weather=Weather(**weather_doc) if weather_doc else None,
            buyout=Buyout(**buyout_doc) if buyout_doc else None,
            promos={str(k): float(v) for k, v in (value.get("promos") or {}).items()},
        )
    return calendar


def _cmd_suggest(args: argparse.Namespace) -> int:
    catalog = _catalog(args)
    result = _ingest(args, catalog)
    depletion = DepletionEngine(catalog).deplete(result.rows)
    engine = OrderEngine(catalog, depletion)
    at = datetime.fromisoformat(args.at) if args.at else datetime.now()
    counted_at = datetime.fromisoformat(args.counted_at) if args.counted_at else None
    kwargs = dict(
        at=at,
        on_hand={str(k): float(v) for k, v in _load_mapping_file(args.counts).items()},
        on_order={str(k): float(v) for k, v in _load_mapping_file(args.on_order).items()},
        calendar=_load_calendar(args.calendar),
        include_optional_windows=args.include_optional_windows,
        counted_at=counted_at,
    )
    if args.vendor:
        orders = [engine.suggest_vendor(args.vendor, **kwargs)]
    else:
        orders = engine.suggest_all(**kwargs)

    payload: dict[str, Any] = {"orders": [], "unmapped_rows": len(depletion.unmapped)}
    lines: list[str] = []
    for order in orders:
        output = render_order(order, arena_out_of_stock=args.arena_out_of_stock)
        payload["orders"].append({**order.to_dict(), "output": output.to_dict()})
        lines.append("=" * 72)
        lines.append(f"{order.vendor.name} - cutoff {order.plan.cutoff}, "
                     f"delivers {order.plan.delivery}, {order.plan.days_of_cover} days of cover")
        for warning in order.warnings:
            lines.append(f"  ! {warning}")
        for line in order.lines:
            lines.append(f"  {line.reasoning.one_liner()}")
            for warning in line.warnings:
                lines.append(f"    ! {warning}")
        for recommendation in order.style_recommendations:
            lines.append(f"  {recommendation.text()}")
        if order.follow_up_offer and order.follow_up_offer.get("offered"):
            lines.append(f"  follow-up: {order.follow_up_offer['flag']}")
        lines.append("")
        lines.append(output.body)
        lines.append("")
    return _emit(args, payload, lines)


def _cmd_sources(args: argparse.Namespace) -> int:
    stub = ToastApiSource()
    payload = {"available": ["file_upload"], "stubbed": stub.describe()}
    lines = [
        "file_upload: working. Parses Toast PMIX XLSX and ItemSelectionDetails CSV.",
        "",
        "toast_api: NOT implemented. Blocking questions:",
        *[f"  {index}. {q['question']}" for index, q in enumerate(payload["stubbed"]["open_questions"], 1)],
    ]
    return _emit(args, payload, lines)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
