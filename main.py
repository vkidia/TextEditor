# -*- coding: utf-8 -*-
# main.py — Точка входа в приложение. Запускать именно этот файл.

import tkinter as tk
from config import WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT
from editor import TextEditor


def main():
    """Создать главное окно и запустить цикл событий tkinter."""
    root = tk.Tk()

    # ── Настройка окна ────────────────────────────────────────────────────────
    root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
    root.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
    root.resizable(True, True)

    # Подавить ошибку иконки на системах без файла .ico
    try:
        root.iconbitmap(default="")
    except Exception:
        pass

    # ── Создать редактор ──────────────────────────────────────────────────────
    app = TextEditor(root)

    # Обработчик закрытия окна через крестик — предлагает сохранить файл
    root.protocol("WM_DELETE_WINDOW", app.quit_app)

    # ── Запустить главный цикл обработки событий ──────────────────────────────
    root.mainloop()


if __name__ == "__main__":
    main()
