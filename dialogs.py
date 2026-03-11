# -*- coding: utf-8 -*-
# dialogs.py — Все диалоговые окна: список, таблица, ссылка, график, поиск/замена

import tkinter as tk
from tkinter import messagebox
from config import COLORS


# ══════════════════════════════════════════════════════════════════════════════
#  БАЗОВЫЙ КЛАСС — единый стиль для всех диалогов
# ══════════════════════════════════════════════════════════════════════════════
class BaseDialog(tk.Toplevel):
    """
    Базовый класс модального диалогового окна.
    Все дочерние диалоги наследуют единую тёмную тему и вспомогательные методы.
    """

    def __init__(self, parent, title, width=400, height=300):
        super().__init__(parent)
        self.result = None   # Результат, который заберёт вызывающий код

        self.title(title)
        self.geometry(f"{width}x{height}")
        self.resizable(False, False)
        self.configure(bg=COLORS["bg_main"])
        self.transient(parent)   # Привязать к родительскому окну
        self.grab_set()          # Сделать модальным (блокирует родительское окно)

        self._build_ui()
        self.wait_window(self)   # Ждать закрытия диалога

    def _build_ui(self):
        """Переопределить в подклассах для создания содержимого диалога."""
        pass

    # ─── Вспомогательные фабричные методы для виджетов ────────────────────────
    def _label(self, parent, text, **kwargs):
        """Создать Label в едином стиле темы."""
        return tk.Label(parent,
            text=text,
            bg=COLORS["bg_main"],
            fg=COLORS["text_ui"],
            font=("Segoe UI", 10),
            **kwargs,
        )

    def _entry(self, parent, **kwargs):
        """Создать Entry (поле ввода) в едином стиле темы."""
        return tk.Entry(parent,
            bg=COLORS["btn_normal"],
            fg=COLORS["text_ui"],
            insertbackground=COLORS["accent"],
            relief="flat",
            font=("Segoe UI", 10),
            **kwargs,
        )

    def _button(self, parent, text, cmd, primary=False):
        """Создать Button в едином стиле. primary=True — акцентная кнопка."""
        bg = COLORS["accent"]    if primary else COLORS["btn_normal"]
        fg = "#1E1E2E"           if primary else COLORS["text_ui"]
        w  = tk.Button(parent,
            text=text, command=cmd,
            bg=bg, fg=fg,
            font=("Segoe UI", 10, "bold" if primary else "normal"),
            relief="flat",
            padx=14, pady=6,
            cursor="hand2",
        )
        # Эффект наведения
        w.bind("<Enter>", lambda e: w.config(bg=COLORS["btn_hover"] if not primary else COLORS["accent2"]))
        w.bind("<Leave>", lambda e: w.config(bg=bg))
        return w


# ══════════════════════════════════════════════════════════════════════════════
#  ДИАЛОГ СОЗДАНИЯ СПИСКА
# ══════════════════════════════════════════════════════════════════════════════
class ListDialog(BaseDialog):
    """
    Диалог ввода пунктов для маркированного или нумерованного списка.
    Каждый пункт вводится с новой строки.
    """

    def __init__(self, parent, list_type):
        self.list_type = list_type
        super().__init__(parent, list_type, width=400, height=320)

    def _build_ui(self):
        self._label(self,
            f"Введите пункты для {self.list_type}а\n(каждый с новой строки):"
        ).pack(pady=(20, 6), padx=20, anchor="w")

        # Многострочное поле ввода
        self.txt = tk.Text(self,
            bg=COLORS["btn_normal"],
            fg=COLORS["text_ui"],
            insertbackground=COLORS["accent"],
            relief="flat",
            font=("Segoe UI", 10),
            height=8, padx=8, pady=6,
        )
        self.txt.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        self.txt.insert("1.0", "Пункт 1\nПункт 2\nПункт 3")  # Пример заполнения

        btn_frame = tk.Frame(self, bg=COLORS["bg_main"])
        btn_frame.pack(pady=(0, 16))
        self._button(btn_frame, "Вставить", self._ok, primary=True).pack(side="left", padx=6)
        self._button(btn_frame, "Отмена",   self.destroy).pack(side="left", padx=6)

    def _ok(self):
        """Собрать непустые строки как пункты списка и сохранить в result."""
        items = [
            line.strip()
            for line in self.txt.get("1.0", "end").split("\n")
            if line.strip()
        ]
        self.result = items
        self.destroy()


# ══════════════════════════════════════════════════════════════════════════════
#  ДИАЛОГ СОЗДАНИЯ ТАБЛИЦЫ
# ══════════════════════════════════════════════════════════════════════════════
class TableDialog(BaseDialog):
    """
    Диалог настройки таблицы: количество строк, столбцов и заголовки.
    Результат: (rows, cols, headers) — tuple.
    """

    def __init__(self, parent):
        super().__init__(parent, "Вставить таблицу", width=380, height=290)

    def _build_ui(self):
        f = tk.Frame(self, bg=COLORS["bg_main"])
        f.pack(fill="both", padx=24, pady=20)

        # ── Количество строк ──
        self._label(f, "Строк:").grid(row=0, column=0, sticky="w", pady=8)
        self.rows_var = tk.IntVar(value=3)
        tk.Spinbox(f,
            from_=1, to=50, textvariable=self.rows_var, width=8,
            bg=COLORS["btn_normal"], fg=COLORS["text_ui"],
            relief="flat", font=("Segoe UI", 10),
            buttonbackground=COLORS["btn_normal"],
        ).grid(row=0, column=1, padx=10, pady=8, sticky="w")

        # ── Количество столбцов ──
        self._label(f, "Столбцов:").grid(row=1, column=0, sticky="w", pady=8)
        self.cols_var = tk.IntVar(value=3)
        tk.Spinbox(f,
            from_=1, to=20, textvariable=self.cols_var, width=8,
            bg=COLORS["btn_normal"], fg=COLORS["text_ui"],
            relief="flat", font=("Segoe UI", 10),
            buttonbackground=COLORS["btn_normal"],
        ).grid(row=1, column=1, padx=10, pady=8, sticky="w")

        # ── Заголовки столбцов ──
        self._label(f, "Заголовки (через запятую):").grid(
            row=2, column=0, sticky="w", pady=8
        )
        self.headers_entry = self._entry(f, width=22)
        self.headers_entry.grid(row=2, column=1, padx=10, pady=8, sticky="w")
        self.headers_entry.insert(0, "Столбец 1, Столбец 2, Столбец 3")

        btn_frame = tk.Frame(self, bg=COLORS["bg_main"])
        btn_frame.pack(pady=(6, 16))
        self._button(btn_frame, "Вставить", self._ok, primary=True).pack(side="left", padx=6)
        self._button(btn_frame, "Отмена",   self.destroy).pack(side="left", padx=6)

    def _ok(self):
        rows    = self.rows_var.get()
        cols    = self.cols_var.get()
        headers = [h.strip() for h in self.headers_entry.get().split(",") if h.strip()]
        self.result = (rows, cols, headers)
        self.destroy()


# ══════════════════════════════════════════════════════════════════════════════
#  ДИАЛОГ ВСТАВКИ ССЫЛКИ
# ══════════════════════════════════════════════════════════════════════════════
class LinkDialog(BaseDialog):
    """
    Диалог для вставки гиперссылки: URL и отображаемый текст.
    Результат: (url, display_text) — tuple.
    """

    def __init__(self, parent):
        super().__init__(parent, "Вставить ссылку", width=420, height=220)

    def _build_ui(self):
        f = tk.Frame(self, bg=COLORS["bg_main"])
        f.pack(fill="both", padx=24, pady=24)

        # ── Поле URL ──
        self._label(f, "URL адрес:").grid(row=0, column=0, sticky="w", pady=8)
        self.url_entry = self._entry(f, width=30)
        self.url_entry.grid(row=0, column=1, padx=10, pady=8)
        self.url_entry.insert(0, "https://")

        # ── Поле текста ссылки ──
        self._label(f, "Текст ссылки:").grid(row=1, column=0, sticky="w", pady=8)
        self.text_entry = self._entry(f, width=30)
        self.text_entry.grid(row=1, column=1, padx=10, pady=8)
        self.text_entry.insert(0, "Нажмите здесь")

        btn_frame = tk.Frame(self, bg=COLORS["bg_main"])
        btn_frame.pack(pady=6)
        self._button(btn_frame, "Вставить", self._ok, primary=True).pack(side="left", padx=6)
        self._button(btn_frame, "Отмена",   self.destroy).pack(side="left", padx=6)

    def _ok(self):
        url     = self.url_entry.get().strip()
        display = self.text_entry.get().strip()
        if url:
            self.result = (url, display)
        self.destroy()


# ══════════════════════════════════════════════════════════════════════════════
#  ДИАЛОГ СОЗДАНИЯ ГРАФИКА
# ══════════════════════════════════════════════════════════════════════════════
class ChartDialog(BaseDialog):
    """
    Диалог для ввода данных ASCII-графика.
    Формат ввода: «Метка=Число» по одному на строку.
    Результат: (title, [(label, value), ...]) — tuple.
    """

    def __init__(self, parent):
        super().__init__(parent, "Вставить график", width=420, height=360)

    def _build_ui(self):
        # ── Название графика ──
        self._label(self, "Название графика:").pack(
            anchor="w", padx=24, pady=(20, 4)
        )
        self.title_entry = self._entry(self, width=40)
        self.title_entry.pack(padx=24, fill="x")
        self.title_entry.insert(0, "Мой график")

        # ── Данные ──
        self._label(self,
            "Данные — формат «Метка=Число», по одному на строку:"
        ).pack(anchor="w", padx=24, pady=(14, 4))

        self.data_text = tk.Text(self,
            bg=COLORS["btn_normal"],
            fg=COLORS["text_ui"],
            insertbackground=COLORS["accent"],
            relief="flat",
            font=("Courier New", 10),
            height=6, padx=8, pady=6,
        )
        self.data_text.pack(fill="both", padx=24, pady=(0, 10), expand=True)
        # Пример данных по умолчанию
        self.data_text.insert("1.0", "Янв=42\nФев=68\nМар=55\nАпр=89\nМай=73")

        btn_frame = tk.Frame(self, bg=COLORS["bg_main"])
        btn_frame.pack(pady=(0, 16))
        self._button(btn_frame, "Вставить", self._ok, primary=True).pack(side="left", padx=6)
        self._button(btn_frame, "Отмена",   self.destroy).pack(side="left", padx=6)

    def _ok(self):
        title  = self.title_entry.get().strip() or "График"
        lines  = self.data_text.get("1.0", "end").strip().split("\n")
        values = []
        for line in lines:
            if "=" in line:
                lbl, _, val_str = line.partition("=")
                try:
                    values.append((lbl.strip(), float(val_str.strip())))
                except ValueError:
                    pass  # Пропустить строки с неверным форматом
        if values:
            self.result = (title, values)
        self.destroy()


# ══════════════════════════════════════════════════════════════════════════════
#  ДИАЛОГ ПОИСКА И ЗАМЕНЫ
# ══════════════════════════════════════════════════════════════════════════════
class FindReplaceDialog(tk.Toplevel):
    """
    Немодальный диалог поиска и замены текста.
    Позволяет: найти следующее вхождение, заменить одно, заменить все.
    """

    def __init__(self, parent, text_widget):
        super().__init__(parent)
        self.text_widget = text_widget   # Ссылка на текстовое поле редактора

        self.title("Найти и Заменить")
        self.geometry("480x250")
        self.resizable(False, False)
        self.configure(bg=COLORS["bg_main"])
        self.transient(parent)   # Следует за родительским окном

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        f = tk.Frame(self, bg=COLORS["bg_main"])
        f.pack(fill="both", padx=24, pady=20)

        # ── Поле «Найти» ──
        tk.Label(f, text="Найти:",
            bg=COLORS["bg_main"], fg=COLORS["text_ui"],
            font=("Segoe UI", 10),
        ).grid(row=0, column=0, sticky="e", pady=8)

        self.find_var = tk.StringVar()
        tk.Entry(f, textvariable=self.find_var, width=30,
            bg=COLORS["btn_normal"], fg=COLORS["text_ui"],
            insertbackground=COLORS["accent"],
            relief="flat", font=("Segoe UI", 10),
        ).grid(row=0, column=1, padx=12, pady=8)

        # ── Поле «Заменить на» ──
        tk.Label(f, text="Заменить на:",
            bg=COLORS["bg_main"], fg=COLORS["text_ui"],
            font=("Segoe UI", 10),
        ).grid(row=1, column=0, sticky="e", pady=8)

        self.replace_var = tk.StringVar()
        tk.Entry(f, textvariable=self.replace_var, width=30,
            bg=COLORS["btn_normal"], fg=COLORS["text_ui"],
            insertbackground=COLORS["accent"],
            relief="flat", font=("Segoe UI", 10),
        ).grid(row=1, column=1, padx=12, pady=8)

        # ── Флажок учёта регистра ──
        self.case_var = tk.BooleanVar(value=False)
        tk.Checkbutton(f,
            text="Учитывать регистр",
            variable=self.case_var,
            bg=COLORS["bg_main"], fg=COLORS["text_ui"],
            selectcolor=COLORS["btn_normal"],
            activebackground=COLORS["bg_main"],
            font=("Segoe UI", 9),
        ).grid(row=2, column=1, sticky="w", pady=4)

        # ── Кнопки действий ──
        btn_f = tk.Frame(self, bg=COLORS["bg_main"])
        btn_f.pack(pady=12)

        def sbtn(text, cmd, primary=False):
            """Вспомогательная функция кнопки диалога."""
            bg = COLORS["accent"]    if primary else COLORS["btn_normal"]
            fg = "#1E1E2E"           if primary else COLORS["text_ui"]
            b  = tk.Button(btn_f, text=text, command=cmd,
                bg=bg, fg=fg, relief="flat",
                font=("Segoe UI", 9, "bold" if primary else "normal"),
                padx=12, pady=6, cursor="hand2",
            )
            b.pack(side="left", padx=4)
            return b

        sbtn("Найти далее",  self.find_next,    primary=True)
        sbtn("Заменить",     self.replace_one)
        sbtn("Заменить все", self.replace_all)
        sbtn("Закрыть",      self._on_close)

    def find_next(self):
        """Найти следующее вхождение и подсветить его."""
        self.text_widget.tag_remove("found", "1.0", "end")
        query  = self.find_var.get()
        nocase = not self.case_var.get()
        if not query:
            return
        # Искать с позиции курсора вперёд, затем с начала
        start = self.text_widget.search(
            query, "insert+1c", nocase=nocase, stopindex="end"
        )
        if not start:
            start = self.text_widget.search(
                query, "1.0", nocase=nocase, stopindex="end"
            )
        if start:
            end = f"{start}+{len(query)}c"
            self.text_widget.tag_configure("found",
                background=COLORS["accent"],
                foreground="#1E1E2E",
            )
            self.text_widget.tag_add("found", start, end)
            self.text_widget.see(start)
            self.text_widget.mark_set("insert", end)

    def replace_one(self):
        """Заменить текущее найденное вхождение и найти следующее."""
        try:
            if "found" in self.text_widget.tag_names():
                self.text_widget.delete("found.first", "found.last")
                self.text_widget.insert("found.first", self.replace_var.get())
        except tk.TclError:
            pass
        self.find_next()

    def replace_all(self):
        """Заменить все вхождения в документе."""
        query   = self.find_var.get()
        replace = self.replace_var.get()
        nocase  = not self.case_var.get()
        if not query:
            return
        count = 0
        pos   = "1.0"
        while True:
            pos = self.text_widget.search(query, pos, nocase=nocase, stopindex="end")
            if not pos:
                break
            end = f"{pos}+{len(query)}c"
            self.text_widget.delete(pos, end)
            self.text_widget.insert(pos, replace)
            pos   = f"{pos}+{len(replace)}c"
            count += 1
        messagebox.showinfo(
            "Замена завершена",
            f"Заменено вхождений: {count}"
        )

    def _on_close(self):
        """Убрать подсветку найденного и закрыть диалог."""
        self.text_widget.tag_remove("found", "1.0", "end")
        self.destroy()
