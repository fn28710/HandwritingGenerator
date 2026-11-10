# -*- coding: utf-8 -*-
"""Generate page: A4 preview + input box + generate button + style model picker."""
import tkinter as tk
from tkinter import ttk, font as tkfont
from handwriting_generator import config
from handwriting_generator.pipeline.render import StyleRenderer
from handwriting_generator.pipeline.fonts import list_style_models
from handwriting_generator.ui.preview import A4Preview


class GeneratePage(ttk.Frame):
    def __init__(self, master, **kw):
        super().__init__(master, padding=8, **kw)
        self.preview = A4Preview(self)
        self.preview.pack(fill="both", expand=True)

        bottom = ttk.Frame(self)
        bottom.pack(fill="x", pady=(8, 0))

        self.style_var = tk.StringVar()
        style_row = ttk.Frame(bottom)
        style_row.pack(fill="x", pady=(0, 4))
        ttk.Label(style_row, text="风格模型（风格迁移）：").pack(side="left")
        self.style_combo = ttk.Combobox(
            style_row, textvariable=self.style_var, state="readonly", width=32,
        )
        self.style_combo.pack(side="left", padx=(4, 0))
        self._refresh_styles()

        self.text = tk.Text(bottom, height=5, wrap="word",
                            font=tkfont.Font(family="Microsoft YaHei", size=11))
        self.text.pack(fill="both", expand=False, pady=(0, 6))
        self.text.insert("1.0", "在这里输入要生成手写体的文字……\n例如：你好，世界。")

        btn_row = ttk.Frame(bottom)
        btn_row.pack(fill="x")
        self.generate_btn = ttk.Button(
            btn_row, text="生 成", command=self.on_generate,
        )
        self.generate_btn.pack(side="right")
        self.status = ttk.Label(bottom, text="就绪", foreground="#666666")
        self.status.pack(side="left")

    def _refresh_styles(self):
        models = list_style_models()
        entries = [display for display, _d in models]
        self._model_dirs = {display: d for display, d in models}
        self.style_combo["values"] = entries
        if entries:
            self.style_combo.current(0)
        else:
            self.style_var.set("")
            self._model_dirs.clear()

    def refresh_style_list(self):
        """Called when switching to this page, so new trained models appear."""
        old = self.style_var.get()
        self._refresh_styles()
        if old in self._model_dirs:
            self.style_var.set(old)
            self.style_combo.set(old)

    def on_generate(self):
        text = self.text.get("1.0", "end-1c").rstrip()
        if not text.strip():
            self.status.config(text="请输入文字")
            return
        style_name = self.style_var.get()
        model_dir = self._model_dirs.get(style_name)
        self.status.config(text=f"生成中（风格：{style_name or '默认系统字体'}）…")
        self.update_idletasks()
        try:
            renderer = StyleRenderer(model_dir=model_dir, dpi=config.DPI_PREVIEW)
            images, doc = renderer.render(text)
        except Exception as e:
            self.status.config(text=f"生成失败：{e}")
            return
        self.preview.show(images)
        self.status.config(text=f"完成，共 {doc.page_count} 页")
