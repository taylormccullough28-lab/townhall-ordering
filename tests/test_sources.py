"""The sales source seam: file upload works, the API stub refuses honestly."""

from __future__ import annotations

from datetime import date

import pytest

from thbev.sources import (
    FileUploadSource,
    SalesSource,
    ToastApiConfig,
    ToastApiSource,
    build_source,
)


def test_file_upload_reads_both_shapes(fixtures_dir):
    source = FileUploadSource(
        [fixtures_dir / "item_selection_details.csv", fixtures_dir / "pmix_full.xlsx"],
        location="Townhall - Short North",
    )
    result = source.fetch_sales(date(2026, 8, 24), date(2026, 8, 30))
    kinds = {entry["format"] for entry in source.describe()["files"]}
    assert kinds == {"item_selection_details", "pmix"}
    assert result.rows
    # PMIX rows have no date and are kept; the CSV's out-of-range 04:05 sale is not.
    assert result.counters["rows_outside_range"] >= 1


def test_file_upload_needs_files():
    with pytest.raises(ValueError):
        FileUploadSource([])


def test_unreadable_file_is_reported_not_ignored(tmp_path, fixtures_dir):
    junk = tmp_path / "notes.txt"
    junk.write_text("not a toast export", encoding="utf-8")
    source = FileUploadSource([junk])
    result = source.fetch_sales(date(2026, 8, 24), date(2026, 8, 30))
    assert {i.code for i in result.issues} & {"unrecognized_file"}


def test_toast_api_source_refuses_with_an_explanation():
    source = ToastApiSource()
    assert isinstance(source, SalesSource)
    with pytest.raises(NotImplementedError) as excinfo:
        source.fetch_sales(date(2026, 8, 24), date(2026, 8, 30))
    message = str(excinfo.value)
    # It must say what is unknown rather than pretend to be nearly done.
    assert "no Toast API integration yet" in message
    assert "restaurant GUID" in message
    assert "FileUploadSource" in message


def test_toast_api_describe_lists_every_blocker():
    described = ToastApiSource(ToastApiConfig(host="example")).describe()
    assert described["implemented"] is False
    assert len(described["open_questions"]) >= 8
    assert "client_id" in described["config_missing"]


def test_source_is_a_config_choice(fixtures_dir):
    source = build_source(
        {"type": "file_upload", "paths": [str(fixtures_dir / "item_selection_details.csv")]}
    )
    assert isinstance(source, FileUploadSource)
    assert isinstance(build_source({"type": "toast_api"}), ToastApiSource)
    with pytest.raises(ValueError):
        build_source({"type": "carrier_pigeon"})
    with pytest.raises(ValueError):
        build_source({})
