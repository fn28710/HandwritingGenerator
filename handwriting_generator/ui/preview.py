# -*- coding: utf-8 -*-
"""A4 print preview widget: scales pages, supports prev/next page."""
import tkinter as tk
from PIL import Image, ImageTk
from handwriting_generator import config


class A4Preview(tk.Frame):
    def __init__(self, master, **kw):
        super().__init__(master, **kw)
        self.pages = []          # list of PIL.Image (RGB)
        self.page = 0            # current page index (0-based)
        self._photo = None
        self._canvas = tk.Canvas(self, bg="#f0f0f0", highlightthickness=0)
        self._canvas.pack(fill="both", expand=True)
        self._canvas.bind("<Configure>", self._on_resize)
        self.bind("<MouseWheel>", self._on_wheel)
        self._label = None

    def show(self, images):
        """Replace displayed pages with new rendered images."""
        if not images:
            self._canvas.delete("all")
            self.pages = []
            self.page = 0
            self._canvas.create_text(
                200, 200, text="输入文字后点击生成",
                fill="#999999", font=("Microsoft YaHei", 14),
            )
            return
        self.pages = list(images)
        self.page = min(self.page, len(self.pages) - 1)
        self._redraw()

    def _on_wheel(self, event):
        if not self.pages:
            return
        delta = -1 if event.delta > 0 else 1
        self.page = (self.page + delta) % len(self.pages)
        self._redraw()

    def _on_resize(self, event):
        self._redraw()

    def page_up(self):
        if self.pages:
            self.page = (self.page - 1) % len(self.pages)
            self._redraw()

    def page_down(self):
        if self.pages:
            self.page = (self.page + 1) % len(self.pages)
            self._redraw()

    def _redraw(self):
        self._canvas.delete("all")
        if not self.pages:
            self._canvas.create_text(
                200, 200, text="输入文字后点击生成",
                fill="#999999", font=("Microsoft YaHei", 14),
            )
            return
        img = self.pages[self.page]
        cw = max(self._canvas.winfo_width(), 200)
        chh = max(self._canvas.winfo_height(), 200)
        scale = min(cw / img.width, chh / img.height) * 0.96
        w = int(img.width * scale)
        h = int(img.height * scale)
        resized = img.resize((w, h), Image.LANCZOS)
        self._photo = ImageTk.PhotoImage(resized)
        x = (cw - w) // 2
        y = (chh - h) // 2
        self._canvas.create_image(x, y, anchor="nw", image=self._photo)
        self._canvas.create_text(
            cw - 8, chh - 12,
            text=f"第 {self.page + 1}/{len(self.pages)} 页（A4 预览）",
            anchor="se", fill="#555555", font=("Microsoft YaHei", 9),
        )
