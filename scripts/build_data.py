"""旧数据构建入口 / Legacy data-build entry point.

中文：真正的总 pipeline 现在在项目根目录的 pipeline.py。
这个文件只是保留旧命令 scripts/build_data.py 还能继续运行。

English: The main pipeline now lives in pipeline.py. This file only keeps the
old scripts/build_data.py command working.
"""

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline import run_data_pipeline


if __name__ == "__main__":
    run_data_pipeline(force=False)
