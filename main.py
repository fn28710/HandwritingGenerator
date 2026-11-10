# -*- coding: utf-8 -*-
"""程序本体入口：启动 Tkinter 应用。"""
import sys
from pathlib import Path

# 允许直接双击运行（保证能导入 handwriting_generator 包）
sys.path.insert(0, str(Path(__file__).resolve().parent))

from handwriting_generator.app import main  # noqa: E402

if __name__ == "__main__":
    main()
