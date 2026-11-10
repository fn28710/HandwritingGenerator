# -*- coding: utf-8 -*-
"""全局配置：路径常量、A4 尺寸、数据集/模型约定。

约定（固定一对一）：
  数据集目录 = training_images/<数据集名>/
  风格模型   = models/<模型名>/
  一个风格模型固定由且仅由一个数据集训练而来，模型 info.json 中记录 dataset 字段。
"""
from pathlib import Path

# 项目根目录（HandwritingGenerator/）
ROOT = Path(__file__).resolve().parent.parent

# 三大必需目录
TRAINING_IMAGES_DIR = ROOT / "training_images"   # 训练集图片文件夹（每个子目录=一个数据集）
MODELS_DIR = ROOT / "models"                     # 风格模型输出文件夹（每个子目录=一个风格模型）
OUTPUT_DIR = ROOT / "output"                     # 生成结果输出文件夹

# 采集模板目录（预留）
TEMPLATES_DIR = ROOT / "templates"

# 默认值
DEFAULT_DATASET = "default_set"
DEFAULT_MODEL_NAME = "my_style"

# A4 纸张尺寸（毫米）
A4_MM_WIDTH = 210.0
A4_MM_HEIGHT = 297.0

# 渲染 DPI 档位
DPI_PREVIEW = 96    # 预览用，位图像素
DPI_EXPORT = 300    # 导出/打印用

# 默认页边距（毫米）
MARGIN_TOP_MM = 25.0
MARGIN_BOTTOM_MM = 25.0
MARGIN_LEFT_MM = 20.0
MARGIN_RIGHT_MM = 20.0


def a4_size_px(dpi: int) -> tuple[int, int]:
    """返回 A4 画布在指定 dpi 下的像素尺寸 (宽, 高)。"""
    w = round(A4_MM_WIDTH / 25.4 * dpi)
    h = round(A4_MM_HEIGHT / 25.4 * dpi)
    return w, h


def ensure_dirs() -> None:
    """确保三大必需目录与模板目录存在。"""
    for d in (TRAINING_IMAGES_DIR, MODELS_DIR, OUTPUT_DIR, TEMPLATES_DIR):
        d.mkdir(parents=True, exist_ok=True)

# ---- 深度学习风格迁移（ml/） ----
# 模型权重文件相对每个 models/<模型名>/ 目录
ML_CHECKPOINT_NAME = "unet.pt"
# 训练字图尺寸
ML_GLYPH_SIZE = 224
