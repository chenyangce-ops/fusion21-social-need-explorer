# Fusion21 Social Need Mapping Prototype

本项目通过一个可重复运行的 ETL 管道，把公共社会需求数据和 Fusion21 模拟
记录整理为统一的地区指标，并在 Streamlit 网站中按九个 English Regions 展示。

## 项目结构

```text
01_网站程序_运行代码/
├── app.py                 # Streamlit 展示层
├── pipeline.py            # 唯一的 ETL 主程序
├── Fusion21_Full_Pipeline.ipynb # 主要可执行讲解与交付入口
├── data/
│   ├── raw/               # 原始官方数据和三张模拟输入表
│   ├── interim/           # 人口加权和地区汇总的中间结果
│   ├── processed/         # 网站直接读取的数据
│   ├── archive/           # 当前管道不使用的旧导出
│   └── README.md          # 每个数据文件的用途
├── tests/
│   └── test_pipeline.py   # 地区覆盖、字段和公式检查
├── scripts/
│   └── build_data.py      # 旧命令兼容入口
├── requirements.txt
└── README.md
```

## ETL 管道

所有步骤都在 `pipeline.py` 中，可以从一个文件看完整执行顺序：

```text
Extract -> Transform -> Validate -> Load
```

### 1. Extract

- 读取 IMD 2019 File 7。
- 获取 LAD19 到 RGN19 的官方对照表和地图边界。
- 获取最新 ONS/Nomis 地区失业率。
- 生成可重复的三张 Fusion21 模拟输入表。

### 2. Transform

- 使用 LSOA 人口计算人口加权 IMD Score。
- 将 LSOA 汇总到 LAD19，再将 LAD19 汇总到九个 Region。
- 清洗失业率并转换为统一指标结构。
- 计算原始社会需求指数：

```text
(population-weighted IMD Score + unemployment rate) / 2
```

- 计算模拟社会贡献指标：

```text
Activity Score = Yes / all possible activity responses * 100
Foundation Score = regional Foundation amount converted to a 0-100 scale
Composite Social Contribution Score = (Activity Score + Foundation Score) / 2
```

合同金额只作为 `Procurement footprint` 单独展示，不进入社会贡献综合分。

### 3. Validate

管道在写入结果前检查：

- 三个公共指标是否都覆盖九个 Region；
- 地区编码和必要字段是否完整；
- 模拟贡献汇总是否覆盖九个 Region；
- 合同金额是否错误地进入贡献得分；
- 综合贡献得分是否等于 Activity 与 Foundation 的平均值。

### 4. Load

通过验证的数据写入 `data/processed/`。网站只读取这些经过验证的输出，避免
在展示层重复清洗和计算。

## 运行方法

### 推荐：使用 Notebook 运行和查看完整流程

双击 `启动Notebook.bat`，打开 `Fusion21_Full_Pipeline.ipynb` 后选择
`Run All`。Notebook 会依次执行 Extract、Transform、Validate 和 Load，
并显示人口加权、中间表、九区结果和最终输出。

`pipeline.py` 与 Notebook 使用同一套计算函数，因此网站、自动测试和 Notebook
不会出现不同公式。

### 命令行运行

在本项目目录中运行：

```powershell
..\.venv\Scripts\python.exe pipeline.py --data-only
```

运行完整 ETL 后启动网站：

```powershell
..\.venv\Scripts\python.exe pipeline.py
```

只启动网站：

```powershell
..\.venv\Scripts\python.exe pipeline.py --app-only --port 8501
```

强制重新下载官方数据：

```powershell
..\.venv\Scripts\python.exe pipeline.py --data-only --force
```

运行自动检查：

```powershell
..\.venv\Scripts\python.exe -m unittest discover tests
```

## 网站输出

网站包含三个主要页面：

1. 社会需求地图：人口加权 IMD、地区失业率和原始社会需求指数。
2. 需求与贡献：并列地图、三分位优先筛查和精确地区表格。
3. Fusion21 模拟数据：采购规模、活动、Foundation 和社会贡献综合分。

## 重要限制

- Fusion21 数据是模拟数据，只用于验证流程和界面。
- 当前社会需求指数是探索性指标，不是官方统计或因果模型。
- IMD 与失业率存在概念重叠，网站保留两个原始指标用于检查。
- 当前界面集中展示九个 Region；`interim` 中保留 LAD 层级结果供方法核查。
