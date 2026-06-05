from __future__ import annotations

from pathlib import Path
from typing import Sequence

import pandas as pd


DATASET_STATS_COLUMNS = [
    "symbol",
    "exchange",
    "rows",
    "days",
    "median_snapshot_interval_ms",
    "mean_spread",
    "mean_depth_top10",
    "first_timestamp",
    "last_timestamp",
    "source_audit_artifact",
    "notes",
]


def build_dataset_stats(audit_path: Path | Sequence[Path], output_path: Path) -> Path:
    audit = _load_audit_sources(audit_path)
    if audit.empty:
        table = pd.DataFrame(columns=DATASET_STATS_COLUMNS)
    else:
        table = _summarize_dataset_stats(audit)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(output_path, index=False)
    return output_path


def _as_paths(audit_path: Path | Sequence[Path]) -> list[Path]:
    if isinstance(audit_path, (str, Path)):
        return [Path(audit_path)]
    return [Path(path) for path in audit_path]


def _load_audit_sources(audit_path: Path | Sequence[Path]) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for priority, path in enumerate(_as_paths(audit_path)):
        if not path.exists():
            continue
        if path.suffix.lower() == ".parquet":
            frame = pd.read_parquet(path)
        else:
            frame = pd.read_csv(path)
        if frame.empty:
            continue
        frame = frame.copy()
        frame["_source_priority"] = priority
        frame["source_audit_artifact"] = str(path).replace("\\", "/")
        frames.append(frame)
    if not frames:
        return pd.DataFrame()
    audit = pd.concat(frames, ignore_index=True)
    if {"symbol", "trade_date"}.issubset(audit.columns):
        min_priority = audit.groupby(["symbol", "trade_date"], dropna=False)["_source_priority"].transform("min")
        audit = audit.loc[audit["_source_priority"].eq(min_priority)].copy()
    return audit


def _summarize_dataset_stats(audit: pd.DataFrame) -> pd.DataFrame:
    audit = audit.copy()
    if "symbol" not in audit.columns:
        audit["symbol"] = ""
    if "exchange" not in audit.columns:
        audit["exchange"] = ""
    rows: list[dict[str, object]] = []
    for (exchange, symbol), group in audit.groupby(["exchange", "symbol"], dropna=False, sort=True):
        first_ts = _timestamp_series(group, "first_timestamp")
        last_ts = _timestamp_series(group, "last_timestamp")
        rows.append(
            {
                "symbol": symbol,
                "exchange": exchange,
                "rows": int(pd.to_numeric(group["n_rows"], errors="coerce").fillna(0).sum()),
                "days": int(group["trade_date"].nunique()) if "trade_date" in group.columns else int(len(group)),
                "median_snapshot_interval_ms": float(pd.to_numeric(group["p50_snapshot_interval_ms"], errors="coerce").median()),
                "mean_spread": float(pd.to_numeric(group["spread_mean"], errors="coerce").mean()),
                "mean_depth_top10": float(pd.to_numeric(group["depth_top10_mean"], errors="coerce").mean()),
                "first_timestamp": first_ts.min().isoformat() if not first_ts.dropna().empty else "",
                "last_timestamp": last_ts.max().isoformat() if not last_ts.dropna().empty else "",
                "source_audit_artifact": ";".join(sorted(set(group["source_audit_artifact"].astype(str)))),
                "notes": _dataset_notes(str(symbol)),
            }
        )
    return pd.DataFrame(rows, columns=DATASET_STATS_COLUMNS).sort_values(["symbol", "exchange"]).reset_index(drop=True)


def _timestamp_series(group: pd.DataFrame, column: str) -> pd.Series:
    if column not in group.columns:
        return pd.Series(dtype="datetime64[ns, UTC]")
    return pd.to_datetime(group[column], errors="coerce", utc=True)


def _dataset_notes(symbol: str) -> str:
    if symbol == "ETH-USDT":
        return (
            "stage audit snapshots; ETH conversion rows=114416570; "
            "feature/label rows=114414433 after horizon/drop"
        )
    return "stage audit snapshots; feature/label rows may be lower after horizon/drop"


def copy_or_empty_csv(source: Path, target: Path) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.exists():
        try:
            pd.read_csv(source).to_csv(target, index=False)
        except pd.errors.EmptyDataError:
            pd.DataFrame().to_csv(target, index=False)
    else:
        pd.DataFrame().to_csv(target, index=False)
    return target


def copy_symbol_rows(source: Path, target: Path, symbol: str) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.exists():
        try:
            frame = pd.read_csv(source)
        except pd.errors.EmptyDataError:
            frame = pd.DataFrame()
        if "symbol" in frame.columns:
            frame = frame.loc[frame["symbol"].astype(str).eq(symbol)].copy()
        else:
            frame = pd.DataFrame()
        frame.to_csv(target, index=False)
    else:
        pd.DataFrame().to_csv(target, index=False)
    return target
