# Audit Stage 3.15 - Dataset stats BTC/ETH lock

- `run_id`: `stage3_15_dataset_stats_btc_eth_lock_v002`
- Mục tiêu: khóa số dataset BTC/ETH để Section 3 không còn phải dùng placeholder cần kiểm chứng cho ETH.
- Phạm vi: chỉ tổng hợp audit tables đã có, không chạy lại raw data audit, không train/inference, không dùng GPU.
- Quyết định: `PASS`

## Artifact đã sinh

- `CryptoRegimeShift/outputs/tables/table_dataset_stats_stage3_by_asset.csv`
- `CryptoRegimeShift/outputs/paper_assets/table_1_dataset_stats.csv`
- `CryptoRegimeShift/outputs/paper_assets/table_1b_eth_dataset_stats.csv`

## Nguồn dữ liệu

- BTC source: `CryptoRegimeShift/outputs/tables/table_data_audit_stage_3_full_scale.csv`
- ETH source: `CryptoRegimeShift/outputs/tables/table_data_audit_stage3_eth_usdt.csv`

Hai nguồn này là audit tables theo ngày đã có sẵn. Stage 3.15 không đọc raw parquet lớn và không thay đổi pipeline thí nghiệm.

## Số khóa cho paper

| Symbol | Exchange | Snapshots audit | Days | Median interval ms | Mean spread | Mean depth top-10 |
|---|---|---:|---:|---:|---:|---:|
| `BTC-USDT` | `BINANCE` | `167,753,156` | `366` | `100.000256` | `0.0282724554` | `9.9064246` |
| `ETH-USDT` | `BINANCE` | `114,416,283` | `366` | `200.0` | `0.0107778793` | `105.1572273` |

Ghi chú ETH:

- ETH conversion raw parquet có `114,416,570` rows.
- ETH stage audit dùng `114,416,283` snapshots trong phạm vi `stage_3_full_scale`.
- ETH feature/label/regime rows là `114,414,433` sau horizon/drop.

## Tác động tới paper

- Section 3 `Data and Benchmark Construction` không cần để placeholder cần kiểm chứng cho ETH dataset stats.
- Nên dùng `table_1_dataset_stats.csv` nếu muốn bảng chung BTC/ETH.
- Nên dùng `table_1b_eth_dataset_stats.csv` nếu chỉ cần copy nhanh dòng ETH vào draft.
- Claim không đổi: paper vẫn là benchmark/failure-analysis + robust selective execution có điều kiện, không claim trading profitability.

## Principal ML Scientist view

- Số ETH hiện đã được khóa từ audit table, cùng cơ chế với BTC.
- Chênh lệch ETH conversion rows, audit snapshots và feature/label rows được ghi rõ, tránh reviewer hiểu nhầm là inconsistency.
- Không có lý do chạy lại raw audit vì nguồn audit hiện đủ để tạo dataset stats reviewer-facing.

## Reviewer ICDM view

- Bảng dataset bây giờ có cả BTC và ETH, hỗ trợ claim cross-asset evaluation tốt hơn.
- Việc ghi source audit artifact trong CSV giúp truy vết số liệu.
- Boundary snapshot-level L2 vẫn phải giữ rõ trong paper.

## Bước tiếp theo

- Thay toàn bộ placeholder cần kiểm chứng liên quan ETH dataset stats trong draft paper bằng số ở bảng Stage 3.15.
- Nếu draft paper thêm số mới ngoài bảng này, chạy lại number consistency hoặc tạo thêm check tương ứng.
