# -*- coding: utf-8 -*-
"""Train page: pick one dataset, set model output, generate template, train.

Three-step workflow:
  1. generate collection template (grid sheets to print & copy)
  2. ingest scanned sheets -> processed/U+XXXX.png glyphs
  3. train style model (variant library and/or deep U-Net)
"""
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from handwriting_generator import config
from handwriting_generator.training import datasets, trainer, template_gen, ingest


class TrainPage(ttk.Frame):
    def __init__(self, master, **kw):
        super().__init__(master, padding=12, **kw)
        self._training = False

        # dataset picker
        drow = ttk.Frame(self)
        drow.pack(fill="x", pady=4)
        ttk.Label(drow, text="训练数据集：").pack(side="left")
        self.dataset_var = tk.StringVar()
        self.dataset_combo = ttk.Combobox(
            drow, textvariable=self.dataset_var, state="readonly", width=26,
        )
        self.dataset_combo.pack(side="left", padx=(4, 0))
        self.dataset_combo.bind("<<ComboboxSelected>>", self._on_dataset_selected)
        self.dataset_hint = ttk.Label(drow, text="", foreground="#888888")
        self.dataset_hint.pack(side="left", padx=8)
        self._refresh_datasets()

        # model output folder
        frow = ttk.Frame(self)
        frow.pack(fill="x", pady=4)
        ttk.Label(frow, text="风格模型输出文件夹：").pack(side="left")
        self.model_var = tk.StringVar(value=str(config.MODELS_DIR / config.DEFAULT_MODEL_NAME))
        ttk.Entry(frow, textvariable=self.model_var, width=40).pack(side="left", fill="x", expand=True)
        ttk.Button(frow, text="浏览…", command=self.on_browse).pack(side="left", padx=4)

        # tool buttons
        toolrow = ttk.Frame(self)
        toolrow.pack(fill="x", pady=(6, 0))
        ttk.Button(toolrow, text="1. 生成采集模板", command=self.on_make_template).pack(side="left", padx=2)
        ttk.Button(toolrow, text="2. 导入扫描件切格", command=self.on_ingest).pack(side="left", padx=2)
        ttk.Button(toolrow, text="3. 训练手写风格模型", command=self.on_start).pack(side="left", padx=2)
        ttk.Button(toolrow, text="4. 训练AI风格模型(深度学习)", command=self.on_train_ai).pack(side="left", padx=2)

        hint = ttk.Label(toolrow,
            text="模板输出到 templates/<数据集名>/，AI模型产出 unet.pt 到 models/<模型名>/",
            foreground="#888888")
        hint.pack(side="left", padx=8)

        # progress
        self._sync_model_path()

        self.progress = ttk.Progressbar(self, maximum=1.0, value=0.0)
        self.progress.pack(fill="x", pady=(16, 4))
        self.progress_label = ttk.Label(self, text="进度：0%")
        self.progress_label.pack(anchor="w")

        self.log = tk.Text(self, height=12, wrap="word", state="disabled",
                           font=("Consolas", 9))
        self.log.pack(fill="both", expand=True, pady=(8, 6))

    # ---- dataset helpers ----
    def _refresh_datasets(self):
        sets = datasets.list_datasets()
        entries = [name for name, _d in sets]
        self._dataset_dirs = {name: d for name, d in sets}
        self.dataset_combo["values"] = entries
        if entries:
            self.dataset_combo.current(0)
            self._update_hint()
        else:
            self.dataset_var.set("")
            self.dataset_hint.config(text="training_images/ 下暂无数据集目录")

    def _on_dataset_selected(self, event=None):
        self._update_hint()
        self._sync_model_path()

    def _sync_model_path(self):
        name = self.dataset_var.get()
        if name:
            self.model_var.set(str(config.MODELS_DIR / name))

    def _update_hint(self):
        name = self.dataset_var.get()
        d = self._dataset_dirs.get(name)
        if d:
            stats = datasets.dataset_stats(d)
            self.dataset_hint.config(
                text=f"raw={stats['raw_count']} processed={stats['processed_count']} manifest={'有' if stats['has_manifest'] else '无'}",
            )
        else:
            self.dataset_hint.config(text="")

    def _log(self, msg):
        self.log.config(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.config(state="disabled")

    def _model_name(self):
        path = self.model_var.get().strip()
        return path.rstrip("\\/").split("\\")[-1].split("/")[-1] or config.DEFAULT_MODEL_NAME

    def _model_dir(self):
        path = self.model_var.get().strip()
        return path or str(config.MODELS_DIR / self._model_name())

    # ---- actions ----
    def on_browse(self):
        path = filedialog.askdirectory(initialdir=str(config.MODELS_DIR), title="选择风格模型输出文件夹")
        if path:
            self.model_var.set(path.replace("/", "\\"))

    def on_make_template(self):
        name = self.dataset_var.get() or config.DEFAULT_DATASET
        if not name:
            messagebox.showwarning("模板", "请先指定数据集名字")
            return
        datasets.resolve_dataset(name)
        try:
            r = template_gen.generate_templates(dataset_name=name, copies=2, dpi=config.DPI_EXPORT)
            self._log(f"模板已生成：{r['pdf']}")
            self._log(f"  共 {len(r['pngs'])} 页 / {len(r['chars'])} 字符（每字 2 遍），请打印 PDF 抄写")
            self._log(f"  扫描后把 sheet_001.png 等放入 training_images/{name}/raw/")
            messagebox.showinfo("模板", f"采集模板已生成，请打印：\n{r['pdf']}")
        except Exception as e:
            messagebox.showerror("模板生成失败", str(e))

    def on_ingest(self):
        name = self.dataset_var.get()
        if not name:
            messagebox.showwarning("导入", "请先在 training_images/ 下创建数据集目录")
            return
        d = self._dataset_dirs.get(name)
        if not d:
            return
        coords = d / "template_coords.json"
        if not coords.exists():
            coords = config.TEMPLATES_DIR / name / "template_coords.json"
        if not coords.exists():
            messagebox.showwarning("导入", "未找到坐标文件，请先点「生成采集模板」")
            return
        try:
            n = ingest.ingest_all(d / "raw", coords, d / "processed")
            self._log(f"切格完成：写入 {n} 张单字图到 processed/")
            self._update_hint()
            messagebox.showinfo("导入", f"切格完成，共 {n} 张单字图")
        except Exception as e:
            messagebox.showerror("导入失败", str(e))

    def on_start(self):
        """Train variant library (rule-based) from processed glyphs."""
        if self._training:
            return
        name = self.dataset_var.get()
        if not name:
            messagebox.showwarning("训练", "请先在 training_images/ 下创建数据集目录")
            return
        model_name = self._model_name()
        self._begin_train(f"训练风格模型：数据集 {name} -> {model_name}")
        threading.Thread(
            target=self._run_variant_train, args=(name, model_name), daemon=True,
        ).start()

    def on_train_ai(self):
        """Train deep U-Net style-transfer model from processed glyphs."""
        if self._training:
            return
        name = self.dataset_var.get()
        if not name:
            messagebox.showwarning("AI训练", "请先在 training_images/ 下创建数据集目录")
            return
        d = self._dataset_dirs.get(name)
        if not d or not (d / "processed").exists() or not list((d / "processed").glob("*.png")):
            messagebox.showwarning("AI训练", "请先完成切格（processed/ 下有单字图）")
            return
        model_name = self._model_name()
        self._begin_train(f"AI训练：数据集 {name} -> {model_name}/unet.pt")
        threading.Thread(
            target=self._run_ai_train, args=(name, model_name), daemon=True,
        ).start()

    def _begin_train(self, msg):
        self._training = True
        self.progress.config(value=0.0)
        self.progress_label.config(text="进度：0%")
        self._log(f"=== {msg} ===")
        self.update_idletasks()

    def _run_variant_train(self, dataset_name, model_name):
        def cb(stage, percent, message):
            self.after(0, self._on_progress, stage, percent, message)
        try:
            model_dir = trainer.start_training(dataset_name, model_name, progress_cb=cb)
            self.after(0, self._on_done, f"变体风格模型：{model_dir}")
        except Exception as e:
            self.after(0, self._on_error, str(e))

    def _run_ai_train(self, dataset_name, model_name):
        def cb(epoch, step, loss, n_total):
            pct = min(0.99, epoch / 40.0)
            self.after(0, self._on_progress, "ai", pct,
                       f"epoch {epoch} step {step} loss={loss:.4f} ({n_total} 对)")
        try:
            from handwriting_generator.ml import train_unet
            dataset_dir = self._dataset_dirs[dataset_name]
            glyph_dir = dataset_dir / "processed"
            out_pt = config.MODELS_DIR / model_name / config.ML_CHECKPOINT_NAME
            train_unet.train(str(glyph_dir), str(out_pt), epochs=40, batch=1,
                             lr=1e-3, report_cb=cb)
            self.after(0, self._on_done, f"AI风格模型：{out_pt}")
        except Exception as e:
            self.after(0, self._on_error, str(e))

    def _on_progress(self, stage, percent, message):
        self.progress.config(value=percent)
        self.progress_label.config(text=f"进度：{int(percent*100)}%  [{stage}]")
        self._log(message)

    def _on_done(self, what):
        self._log(f"训练完成：{what}")
        self._training = False
        messagebox.showinfo("训练完成", what)

    def _on_error(self, err):
        self._log(f"训练失败：{err}")
        self._training = False
        messagebox.showerror("训练失败", err)