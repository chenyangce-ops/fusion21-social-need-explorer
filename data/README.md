# Fusion21 data directory

本文件夹是网站程序使用的唯一数据目录。数据按 ETL 生命周期分层，不能把
中间计算结果重新放回 `raw`。

## `raw/` - 原始输入

- `raw/imd/`
  - `File_7_...csv`：管道实际使用的 IMD 2019 LSOA 数据，包括 IMD Score、
    Rank、Decile 和人口分母。
  - `File_1_...xlsx`：保留用于人工核对，不参与当前自动计算。
- `raw/geography/`
  - 2019 LAD 和 Region 地图边界。
  - `lad19_to_rgn19_lookup.csv`：LAD19 到 RGN19 的官方地区对照表。
- `raw/labour_market/`
  - 从 Nomis API 下载的最新 ONS 地区失业率。
- `raw/fusion21_synthetic/`
  - 合同、社会价值活动和 Foundation 支付三张模拟输入表。

`raw` 文件应当保持原样。重新下载数据时运行：

```powershell
..\.venv\Scripts\python.exe pipeline.py --data-only --force
```

## `interim/` - 中间计算结果

- `imd_lad2019_weighted.csv`：LSOA 按人口加权后汇总到 LAD19。
- `imd_rgn2019_weighted.csv`：LAD19 再按人口加权后汇总到九个 Region。

这些文件可以由管道重新生成，不是原始数据。

## `processed/` - 网站直接读取

- `metrics_latest.csv`：网站公共指标统一表，3 个指标 x 9 个地区。
- `metrics_timeseries.csv`：统一的时期字段，为时间序列扩展预留接口。
- `imd_lad2019.csv`、`imd_rgn2019.csv`：清洗后的 IMD 输出。
- `unemployment_rgn_latest.csv`：清洗后的地区失业率。
- `social_need_composite_latest.csv`：原始社会需求综合指数。
- `fusion21_*_synthetic.csv`：模拟 Fusion21 项目、地区汇总和地图指标。

网站不应直接读取 `raw` 或 `interim`；它只读取 `processed` 和地图边界。

## `archive/legacy_unused/` - 旧文件

这里保存当前管道不使用的历史导出，避免和正式输入混淆。删除这些文件不会
影响当前管道，但暂时保留以便追溯之前的分析。
