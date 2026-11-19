"""Load the project's CSV datasets without modifying source data."""

from pathlib import Path
from typing import Union

import pandas as pd

from src.utils.config import DATASET_DIR


PathLike = Union[str, Path]

CSV_FILES = {
    "blood_banks": "blood_banks.csv",
    "hospitals": "hospitals.csv",
    "inventory": "inventory.csv",
    "requests": "requests.csv",
    "transport": "transport.csv",
}


def _resolve_dataset_dir(dataset_dir: PathLike | None = None) -> Path:
    """Resolve an optional dataset directory to an absolute path."""
    if dataset_dir is None:
        return DATASET_DIR
    path = Path(dataset_dir)
    if not path.is_absolute():
        path = Path.cwd() / path
    return path.resolve()


def load_csv(filename: PathLike, dataset_dir: PathLike | None = None) -> pd.DataFrame:
    """Load one CSV file and report missing or malformed files clearly."""
    dataset_path = _resolve_dataset_dir(dataset_dir)
    path = Path(filename)
    if not path.is_absolute():
        path = dataset_path / path

    if not path.exists():
        raise FileNotFoundError(f"Required dataset file is missing: {path}")
    if not path.is_file():
        raise FileNotFoundError(f"Dataset path is not a file: {path}")

    try:
        return pd.read_csv(path)
    except pd.errors.ParserError as exc:
        raise ValueError(f"Malformed CSV file: {path}") from exc
    except pd.errors.EmptyDataError as exc:
        raise ValueError(f"CSV file is empty: {path}") from exc
    except OSError as exc:
        raise OSError(f"Could not read dataset file: {path}") from exc


def load_dataset(name: str, dataset_dir: PathLike | None = None) -> pd.DataFrame:
    """Load a named project dataset."""
    if name not in CSV_FILES:
        raise KeyError(f"Unknown dataset name '{name}'. Expected one of: {', '.join(CSV_FILES)}")
    return load_csv(CSV_FILES[name], dataset_dir)


def load_all_datasets(dataset_dir: PathLike | None = None) -> dict[str, pd.DataFrame]:
    """Load all required project CSV datasets."""
    return {name: load_dataset(name, dataset_dir) for name in CSV_FILES}


def load_blood_banks(dataset_dir: PathLike | None = None) -> pd.DataFrame:
    return load_dataset("blood_banks", dataset_dir)


def load_hospitals(dataset_dir: PathLike | None = None) -> pd.DataFrame:
    return load_dataset("hospitals", dataset_dir)


def load_inventory(dataset_dir: PathLike | None = None) -> pd.DataFrame:
    return load_dataset("inventory", dataset_dir)


def load_requests(dataset_dir: PathLike | None = None) -> pd.DataFrame:
    return load_dataset("requests", dataset_dir)


def load_transport(dataset_dir: PathLike | None = None) -> pd.DataFrame:
    return load_dataset("transport", dataset_dir)
