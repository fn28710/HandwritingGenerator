# -*- coding: utf-8 -*-
"""Main window: notebook with two pages (generate / train)."""
import tkinter as tk
from tkinter import ttk
from handwriting_generator import config
from handwriting_generator.ui.generate_page import GeneratePage
from handwriting_generator.ui.train_page import TrainPage


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("个人手写字生成器")
        self.geometry("900x860")
        config.ensure_dirs()

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        self.generate_page = GeneratePage(self.notebook)
        self.train_page = TrainPage(self.notebook)
        self.notebook.add(self.generate_page, text="  生成  ")
        self.notebook.add(self.train_page, text="  训练  ")

        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def _on_tab_changed(self, event):
        # when user returns to generate page, refresh style model dropdown
        if self.notebook.index("current") == 0:
            self.generate_page.refresh_style_list()


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
