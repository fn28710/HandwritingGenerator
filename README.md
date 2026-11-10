# 个人手写字生成器（HandwritingGenerator）

输入任意文字，生成像真人的手写体 A4 图像。基于**深度学习风格迁移**：收集少量你的手写样本，训练一个轻量 U-Net，即可把任意字符（包括你没写过的字）渲染成你的笔迹风格。

## 特性

- 🖊️ **风格迁移**：任意汉字（含 GB2312 全 6763 字 + 冷门扩展字）都能生成手写体
- 🧠 **深度学习**：轻量条件 U-Net（~7.7M 参数），4GB 显存即可训练，CPU 也能跑
- 📄 **A4 打印**：默认 40mm 大字、300dpi、纯黑笔画、透明背景、无方格
- 🖱️ **极简界面**：Tkinter 三要素——打印预览 + 输入框 + 生成按钮
- 🎨 **多风格模型**：可训练多个风格（如霞鹜文楷、华文行楷），下拉切换

## 界面

```
┌─────────────────────────────────────────┐
│  [生成] 页           [训练] 页            │
│  A4 打印预览     │  1. 生成采集模板       │
│  输入框          │  2. 导入扫描件切格     │
│  [生成] 按钮     │  3. 训练手写风格模型   │
│  风格模型下拉    │  4. 训练AI风格模型     │
└─────────────────────────────────────────┘
```

## 快速开始（零成本体验）

```bash
# Windows（需要 Python 3.10+，Tkinter 自带）
pip install Pillow numpy torch torchvision
python main.py
```

生成页选择「demo_lxgw」或「demo_hand」风格模型，输入文字，点生成即可看到效果。

> 注意：`models/` 下的预训练权重默认不在仓库中（用户自己训练）。要快速体验，运行：
> ```bash
> python -m handwriting_generator.training.fake_data
> python -m handwriting_generator.ml.train_unet training_images/demo_hand/processed models/demo_hand/unet.pt
> ```

## 完整流程：训练你自己的字

### 第 1 步：生成采集模板
训练页 → 「1. 生成采集模板」→ 打印 `templates/<数据集名>/xxx.pdf`（100 常用字 + 标点 + ASCII，每字 2 遍，22mm 大格）。

### 第 2 步：手写 + 扫描
照着模板抄写，扫描/拍照，把图放进 `training_images/<数据集名>/raw/`。

### 第 3 步：切格
训练页 → 「2. 导入扫描件切格」→ 自动按格子坐标切出单字，命名 `U+码点.png`。

### 第 4 步：训练 AI 风格模型
训练页 → 「4. 训练AI风格模型」→ 输出 `models/<数据集名>/unet.pt`（40 epoch，GPU 约 50 分钟，CPU 约 37 分钟）。

### 第 5 步：生成
生成页 → 选你的模型 → 输入任意文字 → 生成 A4 手写体。

## 目录结构

```
HandwritingGenerator/
├── main.py                    # 程序入口
├── run.bat                    # Windows 双击启动
├── handwriting_generator/
│   ├── app.py                 # 主窗口（生成/训练两个分页）
│   ├── config.py              # 路径常量、A4 尺寸、约定
│   ├── ui/                    # 界面（预览/生成页/训练页）
│   ├── pipeline/              # 排版、渲染、变体库、风格参数
│   ├── training/              # 采集模板、切格、数据集、训练编排
│   └── ml/                    # 深度学习（U-Net、数据集、训练、推理）
├── assets/fonts/              # 霞鹜文楷字体（开源，开源可商用）
├── training_images/           # 训练集图片文件夹
├── models/                    # 风格模型输出文件夹
├── output/                    # 生成结果输出
└── templates/                 # 采集模板输出
```

## 技术架构

- **模型**：轻量条件 U-Net（base=32，~7.7M 参数），输入印刷体字符图 → 输出手写体图
- **训练**：PyTorch + CUDA（或 CPU），AMP 混合精度，batch=8，224×224 分辨率
- **数据**：印刷体↔手写体配对（自动用 PIL 渲染印刷体），完整 GB2312 数据集 7835 张
- **渲染链**：风格模型 → 几何扰动 → 墨色微调 → 二值化 → 去噪 → A4 合成

## 风格迁移原理

模型学习「印刷体结构 → 笔迹风格」的映射：
- **结构**由输入的印刷体字符图保证（所以任意字都对）
- **风格**由你的手写样本学出（所以像你的字）
- 未录入的字也能生成，无需穷举所有字符

## 许可

- 代码：MIT License
- 字体 `assets/fonts/LXGWWenKai-Regular.ttf`：霞鹜文楷（LXGW WenKai），SIL Open Font License 1.1