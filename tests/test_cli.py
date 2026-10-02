"""CLI smoke tests. The library carries the logic; these check it is reachable."""

from __future__ import annotations

import json

from thbev.cli import main

LOCATION = "Townhall - Short North"


def test_ingest_command_reports_what_it_read(fixtures_dir, capsys):
    code = main([
        "--json", "ingest",
        "--file", str(fixtures_dir / "item_selection_details.csv"),
        "--location", LOCATION,
        "--start", "2026-08-24", "--end", "2026-08-30",
    ])
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["rows"] > 0
    assert payload["voided_rows"] == 1
    assert payload["has_time_dimension"] is True


def test_deplete_command_lists_unmapped_rows(fixtures_dir, capsys):
    code = main([
        "--catalog", str(fixtures_dir / "catalog"), "--json", "deplete",
        "--file", str(fixtures_dir / "item_selection_details.csv"),
        "--location", LOCATION, "--start", "2026-08-24", "--end", "2026-08-30",
    ])
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["unmapped_qty"] == 8  # the Mystery Shot line, quantity intact


def test_suggest_command_produces_a_vendor_order(fixtures_dir, tmp_path, capsys):
    counts = tmp_path / "counts.yaml"
    counts.write_text("bud_light: 40\nnutrl: 12\n", encoding="utf-8")
    code = main([
        "--catalog", str(fixtures_dir / "catalog"), "--json", "suggest",
        "--file", str(fixtures_dir / "item_selection_history.csv"),
        "--location", LOCATION, "--start", "2026-07-27", "--end", "2026-08-30",
        "--vendor", "superior", "--at", "2026-08-30T16:00", "--counts", str(counts),
    ])
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    order = payload["orders"][0]
    assert order["vendor"] == "superior"
    assert order["delivery_plan"]["days_of_cover"] == 7
    assert order["lines"][0]["reasoning_line"]


def test_windows_command(capsys):
    assert main(["windows", "--at", "2026-08-30T16:00"]) == 0
    out = capsys.readouterr().out
    assert "Arena Liquor" in out


def test_sources_command_is_honest_about_the_api(capsys):
    assert main(["sources"]) == 0
    out = capsys.readouterr().out
    assert "toast_api: NOT implemented" in out


def test_bad_input_exits_nonzero(tmp_path, capsys):
    code = main(["ingest", "--file", str(tmp_path / "missing.csv")])
    assert code == 2


def test_no_command_prints_help(capsys):
    assert main([]) == 1
