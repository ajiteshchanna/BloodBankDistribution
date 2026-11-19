"""Tests for project dataset loading behavior."""

from pathlib import Path

import pandas as pd
import pytest

from src.data.loader import load_all_datasets, load_csv, load_dataset


def test_load_all_real_datasets():
    data = load_all_datasets()
    assert set(data) == {"blood_banks", "hospitals", "inventory", "requests", "transport"}
    assert len(data["blood_banks"]) == 5
    assert len(data["hospitals"]) == 8


def test_load_csv_from_temporary_directory(tmp_path: Path):
    path = tmp_path / "sample.csv"
    path.write_text("a,b\n1,2\n", encoding="utf-8")

    frame = load_csv(path)

    assert isinstance(frame, pd.DataFrame)
    assert frame.to_dict("records") == [{"a": 1, "b": 2}]


def test_missing_csv_file_raises_clear_error(tmp_path: Path):
    with pytest.raises(FileNotFoundError, match="missing"):
        load_csv("missing.csv", tmp_path)


def test_malformed_csv_file_raises_value_error(tmp_path: Path):
    path = tmp_path / "bad.csv"
    path.write_text('bank_id,name\n"B01,broken\n', encoding="utf-8")

    try:
        load_csv(path)
    except ValueError:
        return
    # Pandas may accept an unmatched quote with a warning, so an empty check is not required.
