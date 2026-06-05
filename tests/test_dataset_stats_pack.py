from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from reports.make_tables import build_dataset_stats  # noqa: E402
from reports.result_pack import assemble_result_pack  # noqa: E402


def _audit_rows(symbol: str, rows: tuple[int, int], *, exchange: str = "BINANCE") -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "trade_date": "2024-01-01",
                "exchange": exchange,
                "symbol": symbol,
                "n_rows": rows[0],
                "first_timestamp": "2024-01-01 00:00:00+00:00",
                "last_timestamp": "2024-01-01 23:59:59+00:00",
                "p50_snapshot_interval_ms": 100.0 if symbol == "BTC-USDT" else 200.0,
                "spread_mean": 0.02 if symbol == "BTC-USDT" else 0.01,
                "depth_top10_mean": 10.0 if symbol == "BTC-USDT" else 100.0,
            },
            {
                "trade_date": "2024-01-02",
                "exchange": exchange,
                "symbol": symbol,
                "n_rows": rows[1],
                "first_timestamp": "2024-01-02 00:00:00+00:00",
                "last_timestamp": "2024-01-02 23:59:59+00:00",
                "p50_snapshot_interval_ms": 120.0 if symbol == "BTC-USDT" else 220.0,
                "spread_mean": 0.04 if symbol == "BTC-USDT" else 0.03,
                "depth_top10_mean": 20.0 if symbol == "BTC-USDT" else 200.0,
            },
        ]
    )


def test_build_dataset_stats_outputs_btc_eth_rows(tmp_path: Path) -> None:
    btc = tmp_path / "btc.csv"
    eth = tmp_path / "eth.csv"
    _audit_rows("BTC-USDT", (10, 20)).to_csv(btc, index=False)
    _audit_rows("ETH-USDT", (30, 40)).to_csv(eth, index=False)

    output = tmp_path / "dataset_stats.csv"
    build_dataset_stats([btc, eth], output)
    stats = pd.read_csv(output)

    assert set(stats["symbol"]) == {"BTC-USDT", "ETH-USDT"}
    btc_row = stats.loc[stats["symbol"].eq("BTC-USDT")].iloc[0]
    eth_row = stats.loc[stats["symbol"].eq("ETH-USDT")].iloc[0]
    assert int(btc_row["rows"]) == 30
    assert int(eth_row["rows"]) == 70
    assert int(eth_row["days"]) == 2
    assert float(eth_row["median_snapshot_interval_ms"]) == 210.0
    assert "stage audit snapshots" in str(eth_row["notes"])


def test_build_dataset_stats_deduplicates_duplicate_eth_sources(tmp_path: Path) -> None:
    eth_primary = tmp_path / "table_data_audit_stage3_eth_usdt.csv"
    eth_duplicate = tmp_path / "table_data_audit_eth_usdt_stage3.csv"
    _audit_rows("ETH-USDT", (30, 40)).to_csv(eth_primary, index=False)
    _audit_rows("ETH-USDT", (999, 999)).to_csv(eth_duplicate, index=False)

    output = tmp_path / "dataset_stats.csv"
    build_dataset_stats([eth_primary, eth_duplicate], output)
    stats = pd.read_csv(output)

    assert len(stats) == 1
    assert str(stats.iloc[0]["symbol"]) == "ETH-USDT"
    assert int(stats.iloc[0]["rows"]) == 70


def test_result_pack_writes_dataset_stats_and_eth_table(tmp_path: Path) -> None:
    tables = tmp_path / "outputs" / "tables"
    tables.mkdir(parents=True)
    _audit_rows("BTC-USDT", (10, 20)).to_csv(tables / "table_data_audit_stage_3_full_scale.csv", index=False)
    _audit_rows("ETH-USDT", (30, 40)).to_csv(tables / "table_data_audit_stage3_eth_usdt.csv", index=False)

    artifacts = assemble_result_pack(tmp_path, stage="stage_3_full_scale")
    dataset = pd.read_csv(artifacts["table_1_dataset_stats"])
    eth = pd.read_csv(artifacts["table_1b_eth_dataset_stats"])
    table_copy = pd.read_csv(tables / "table_dataset_stats_stage3_by_asset.csv")

    assert set(dataset["symbol"]) == {"BTC-USDT", "ETH-USDT"}
    assert set(table_copy["symbol"]) == {"BTC-USDT", "ETH-USDT"}
    assert len(eth) == 1
    assert str(eth.iloc[0]["symbol"]) == "ETH-USDT"
