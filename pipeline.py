"""Fusion21 总 pipeline / Main project pipeline.

中文：
这个文件是整个项目的总入口。它把两个步骤串起来：
1. 重新生成 processed data。
2. 启动 Streamlit web app。

English:
This file is the main entry point for the project. It connects two steps:
1. Rebuild the processed data.
2. Start the Streamlit web app.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys


# ---------------------------------------------------------------------------
# 1. 项目路径设置 / Project path setup
# ---------------------------------------------------------------------------
# 中文：确保 pipeline.py 能找到 src/fusion21 里面的数据处理函数。
# English: Make sure pipeline.py can find the data functions in src/fusion21.

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from fusion21 import build_all_data


# ---------------------------------------------------------------------------
# 2. 数据 pipeline / Data pipeline
# ---------------------------------------------------------------------------
# 中文：这一部分负责 raw data -> processed data。
# English: This section handles raw data -> processed data.

def run_data_pipeline(force: bool = False) -> None:
    """重新生成网站需要读取的 processed data.

    Rebuild the processed data used by the web app.
    """

    print("Step 1/2: building processed data...")
    outputs = build_all_data(force=force)
    latest = outputs["latest"]
    timeseries = outputs["timeseries"]
    print(f"Built latest indicators: {len(latest):,} rows")
    print(f"Built time series: {len(timeseries):,} rows")
    print("Processed data written to data/processed/")


# ---------------------------------------------------------------------------
# 3. Web app pipeline / Web app pipeline
# ---------------------------------------------------------------------------
# 中文：这一部分负责启动 Streamlit 网站。网站启动后会一直运行，直到你关掉终端。
# English: This section starts the Streamlit app. Once started, the app keeps
# running until the terminal is closed or the process is stopped.

def run_web_app(port: int = 8501) -> None:
    """启动 Streamlit web app / Start the Streamlit web app."""

    print("Step 2/2: starting Streamlit web app...")
    print(f"Local URL: http://localhost:{port}/")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(ROOT / "app.py"),
            "--server.port",
            str(port),
        ],
        check=True,
    )


# ---------------------------------------------------------------------------
# 4. 总入口 / Main entry point
# ---------------------------------------------------------------------------
# 中文：默认运行完整 pipeline；也可以只跑数据或只跑网站。
# English: By default, run the full pipeline; data-only and app-only modes are
# also available.

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Fusion21 project pipeline.")
    parser.add_argument(
        "--data-only",
        action="store_true",
        help="Only rebuild processed data, then stop.",
    )
    parser.add_argument(
        "--app-only",
        action="store_true",
        help="Only start the Streamlit app without rebuilding data.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-download/rebuild cached raw data where supported.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8501,
        help="Port used by the Streamlit app. Default: 8501.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.data_only and args.app_only:
        raise SystemExit("Choose either --data-only or --app-only, not both.")

    if args.app_only:
        run_web_app(port=args.port)
        return

    run_data_pipeline(force=args.force)

    if not args.data_only:
        run_web_app(port=args.port)


if __name__ == "__main__":
    main()
