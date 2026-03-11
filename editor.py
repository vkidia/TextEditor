# -*- coding: utf-8 -*-
# editor.py — Главный класс редактора с PNG-иконками на кнопках

import tkinter as tk
from tkinter import ttk, colorchooser, messagebox
import tkinter.font as tkfont
import os
import webbrowser
from PIL import Image, ImageTk

from config import COLORS, DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE
from file_manager import FileManager
from dialogs import ListDialog, TableDialog, LinkDialog, ChartDialog, FindReplaceDialog

try:
    PIL_AVAILABLE = True
except:
    PIL_AVAILABLE = False


# ══════════════════════════════════════════════════════════════════════════════
#  ВСПЛЫВАЮЩАЯ ПОДСКАЗКА
# ══════════════════════════════════════════════════════════════════════════════
class Tooltip:
    """Показывает подсказку через 500мс после наведения курсора."""
    def __init__(self, widget, text):
        self.widget  = widget
        self.text    = text
        self.tip_win = None
        self._job    = None
        widget.bind("<Enter>", self._schedule)
        widget.bind("<Leave>", self._hide)

    def _schedule(self, event=None):
        self._cancel()
        self._job = self.widget.after(500, self._show)

    def _cancel(self):
        if self._job:
            self.widget.after_cancel(self._job)
            self._job = None

    def _show(self):
        if self.tip_win:
            return
        x = self.widget.winfo_rootx()
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        self.tip_win = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tw.configure(bg=COLORS["bg_statusbar"])
        tk.Label(tw, text=self.text,
            bg=COLORS["bg_statusbar"], fg=COLORS["text_ui"],
            font=("Segoe UI", 9), padx=8, pady=4,
        ).pack()

    def _hide(self, event=None):
        self._cancel()
        if self.tip_win:
            self.tip_win.destroy()
            self.tip_win = None


# ══════════════════════════════════════════════════════════════════════════════
#  МЕНЕДЖЕР ИКОНОК
# ══════════════════════════════════════════════════════════════════════════════
class IconManager:
    """
    Загружает PNG-иконки из папки icons/ и масштабирует до нужного размера.
    Кэширует загруженные изображения чтобы не перезагружать повторно.
    """
    def __init__(self, icon_dir, size=20):
        self.icon_dir = icon_dir
        self.size     = size
        self._cache   = {}   # Кэш: имя → PhotoImage

    def get(self, name):
        """Вернуть PhotoImage для иконки name. None если файл не найден."""
        if name in self._cache:
            return self._cache[name]
        path = os.path.join(self.icon_dir, f"{name}.png")
        if not os.path.exists(path):
            return None
        try:
            img   = Image.open(path).convert("RGBA")
            img   = img.resize((self.size, self.size), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self._cache[name] = photo
            return photo
        except Exception:
            return None


# ══════════════════════════════════════════════════════════════════════════════
#  ГЛАВНЫЙ КЛАСС РЕДАКТОРА
# ══════════════════════════════════════════════════════════════════════════════
class TextEditor:
    """
    Главный класс текстового редактора.
    Кнопки используют PNG-иконки из папки icons/.
    При наведении показывается Tooltip с описанием.
    """

    def __init__(self, root):
        self.root = root
        self.root.title("Безымянный — Текстовый Редактор")
        self.root.configure(bg=COLORS["bg_main"])

        # Путь к иконкам — рядом с editor.py
        icon_dir      = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons")
        self.icons    = IconManager(icon_dir, size=20)

        # ─── Состояние документа ────────────────────────────────────────────
        self.file_name   = ""
        self.is_modified = False
        self.tag_counter = 0
        self._images     = []

        # ─── Форматирование ──────────────────────────────────────────────────
        self.font_family    = tk.StringVar(value=DEFAULT_FONT_FAMILY)
        self.font_size      = tk.IntVar(value=DEFAULT_FONT_SIZE)
        self.font_bold      = False
        self.font_italic    = False
        self.font_underline = False
        self.font_strike    = False
        self.font_color     = COLORS["editor_text"]
        self.font_bg        = COLORS["bg_editor"]
        self.line_spacing   = tk.DoubleVar(value=1.0)

        self.fm = FileManager(self)

        self._setup_styles()
        self._build_menu()
        self._build_toolbar()
        self._build_format_bar()
        self._build_editor()
        self._build_statusbar()
        self._bind_shortcuts()

        self.text.bind("<<Modified>>",    self._on_text_modified)
        self.text.bind("<KeyRelease>",    self._update_status)
        self.text.bind("<ButtonRelease>", self._update_status)
        self._update_status()

    # ══════════════════════════════════════════════════════════════════════════
    #  СТИЛИ
    # ══════════════════════════════════════════════════════════════════════════
    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Dark.TCombobox",
            fieldbackground=COLORS["btn_normal"],
            background=COLORS["btn_normal"],
            foreground=COLORS["text_ui"],
            selectbackground=COLORS["accent"],
            selectforeground="#1E1E2E",
            arrowcolor=COLORS["accent"],
            borderwidth=0, relief="flat",
        )
        style.map("Dark.TCombobox",
            fieldbackground=[("readonly", COLORS["btn_normal"])],
            selectbackground=[("readonly", COLORS["btn_normal"])],
        )

    # ══════════════════════════════════════════════════════════════════════════
    #  ФАБРИЧНЫЙ МЕТОД КНОПКИ С ИКОНКОЙ
    # ══════════════════════════════════════════════════════════════════════════
    def _icon_btn(self, parent, icon_name, tooltip_text, cmd,
                  fallback_text=None, ref_attr=None):
        """
        Создать кнопку с PNG-иконкой и всплывающей подсказкой.
        Если иконка не найдена — показывает fallback_text.
        icon_name    — имя файла без .png (например 'bold')
        tooltip_text — текст подсказки при наведении
        fallback_text— текст если иконка недоступна
        ref_attr     — имя атрибута self для сохранения ссылки
        """
        photo = self.icons.get(icon_name)
        b = tk.Button(parent,
            command=cmd,
            bg=COLORS["btn_normal"],
            fg=COLORS["text_ui"],
            activebackground=COLORS["accent"],
            activeforeground="#1E1E2E",
            relief="flat", bd=0,
            padx=6, pady=4,
            cursor="hand2",
        )
        if photo:
            b.config(image=photo, width=26, height=26)
            b._icon_ref = photo   # Защита от сборщика мусора
        else:
            # Иконка не найдена — показываем текст
            b.config(text=fallback_text or icon_name,
                     font=("Segoe UI", 9))

        b.pack(side="left", padx=2, pady=2)
        b.bind("<Enter>", lambda e: b.config(bg=COLORS["btn_hover"]))
        b.bind("<Leave>", lambda e: b.config(bg=COLORS["btn_normal"]))
        Tooltip(b, tooltip_text)

        if ref_attr:
            setattr(self, ref_attr, b)
        return b

    def _make_sep(self, parent):
        """Вертикальный разделитель."""
        tk.Frame(parent, bg=COLORS["border"], width=1).pack(
            side="left", fill="y", padx=5, pady=4)

    # ══════════════════════════════════════════════════════════════════════════
    #  СТРОКА МЕНЮ
    # ══════════════════════════════════════════════════════════════════════════
    def _build_menu(self):
        menubar = tk.Menu(self.root,
            bg=COLORS["bg_toolbar"], fg=COLORS["text_ui"],
            activebackground=COLORS["accent"], activeforeground="#1E1E2E",
            bd=0, relief="flat",
        )
        self.root.config(menu=menubar)

        def make_menu(label, items):
            m = tk.Menu(menubar, tearoff=0,
                bg=COLORS["bg_toolbar"], fg=COLORS["text_ui"],
                activebackground=COLORS["accent"], activeforeground="#1E1E2E",
                bd=0, relief="flat",
            )
            menubar.add_cascade(label=label, menu=m)
            for item in items:
                if item == "---":
                    m.add_separator(background=COLORS["border"])
                else:
                    lbl = item[0]; cmd = item[1]
                    acc = item[2] if len(item) > 2 else ""
                    m.add_command(label=lbl, command=cmd,
                                  accelerator=acc, font=("Segoe UI", 9))
            return m

        make_menu("Файл", [
            ("Создать",          self.fm.new_file,     "Ctrl+N"),
            ("Открыть...",       self.fm.open_file,    "Ctrl+O"),
            "---",
            ("Сохранить",        self.fm.save_file,    "Ctrl+S"),
            ("Сохранить как...", self.fm.save_as_file, "Ctrl+Shift+S"),
            "---",
            ("Экспорт в PDF",    self.fm.export_pdf),
            ("Экспорт в RTF",    self.fm.export_rtf),
            "---",
            ("Выход",            self.quit_app,        "Alt+F4"),
        ])
        make_menu("Правка", [
            ("Отменить",         self.undo,         "Ctrl+Z"),
            ("Повторить",        self.redo,         "Ctrl+Y"),
            "---",
            ("Вырезать",         self.cut,          "Ctrl+X"),
            ("Копировать",       self.copy,         "Ctrl+C"),
            ("Вставить",         self.paste,        "Ctrl+V"),
            ("Удалить",          self.delete_sel),
            "---",
            ("Выделить всё",     self.select_all,   "Ctrl+A"),
            ("Очистить всё",     self.clear_all),
            "---",
            ("Найти и заменить", self.find_replace, "Ctrl+F"),
        ])
        make_menu("Формат", [
            ("Жирный",           self.toggle_bold,       "Ctrl+B"),
            ("Курсив",           self.toggle_italic,     "Ctrl+I"),
            ("Подчёркнутый",     self.toggle_underline,  "Ctrl+U"),
            ("Зачёркнутый",      self.toggle_strike),
            "---",
            ("Цвет текста...",   self.change_font_color),
            ("Цвет фона...",     self.change_highlight),
            "---",
            ("По левому краю",   self.align_left,    "Ctrl+L"),
            ("По центру",        self.align_center,  "Ctrl+E"),
            ("По правому краю",  self.align_right,   "Ctrl+R"),
            ("По ширине",        self.align_justify, "Ctrl+J"),
        ])
        make_menu("Вставка", [
            ("Маркированный список",  self.insert_bullet_list),
            ("Нумерованный список",   self.insert_numbered_list),
            "---",
            ("Таблица...",            self.insert_table),
            ("Изображение...",        self.insert_image),
            ("Ссылка...",             self.insert_link),
            ("График...",             self.insert_chart),
            "---",
            ("Горизонтальная линия",  self.insert_hr),
        ])
        make_menu("Справка", [("О программе", self.show_about)])

    # ══════════════════════════════════════════════════════════════════════════
    #  ПАНЕЛЬ ИНСТРУМЕНТОВ
    # ══════════════════════════════════════════════════════════════════════════
    def _build_toolbar(self):
        """Верхняя панель — иконки файловых операций и правки."""
        toolbar = tk.Frame(self.root, bg=COLORS["bg_toolbar"], pady=5, padx=8)
        toolbar.pack(side="top", fill="x")
        tk.Frame(toolbar, bg=COLORS["border"], height=1).pack(side="bottom", fill="x")

        b = lambda ic, tip, cmd, fb=None: self._icon_btn(toolbar, ic, tip, cmd, fb)
        s = lambda: self._make_sep(toolbar)

        # Файл
        b("new",     "Создать новый документ (Ctrl+N)",         self.fm.new_file,    "Новый")
        b("open",    "Открыть файл (Ctrl+O)",                   self.fm.open_file,   "Открыть")
        b("save",    "Сохранить (Ctrl+S)",                      self.fm.save_file,   "Сохранить")
        b("save_as", "Сохранить как... (Ctrl+Shift+S)",         self.fm.save_as_file,"Сохр.как")
        s()

        # Правка
        b("undo",    "Отменить (Ctrl+Z)",                       self.undo,    "Отменить")
        b("redo",    "Повторить (Ctrl+Y)",                      self.redo,    "Повторить")
        s()
        b("cut",     "Вырезать (Ctrl+X)",                       self.cut,     "Вырезать")
        b("copy",    "Копировать (Ctrl+C)",                     self.copy,    "Копировать")
        b("paste",   "Вставить (Ctrl+V)",                       self.paste,   "Вставить")
        s()

        # Поиск
        b("find",    "Найти и заменить (Ctrl+F)",               self.find_replace, "Найти")
        s()

        # Вставка объектов
        b("table",   "Вставить таблицу",                        self.insert_table,  "Таблица")
        b("image",   "Вставить изображение",                    self.insert_image,  "Картинка")
        b("link",    "Вставить ссылку",                         self.insert_link,   "Ссылка")
        b("chart",   "Вставить график",                         self.insert_chart,  "График")
        s()

        # Экспорт
        b("pdf",     "Экспортировать в PDF",                    self.fm.export_pdf, "PDF")
        b("rtf",     "Экспортировать в RTF",                    self.fm.export_rtf, "RTF")

    # ══════════════════════════════════════════════════════════════════════════
    #  ПАНЕЛЬ ФОРМАТИРОВАНИЯ
    # ══════════════════════════════════════════════════════════════════════════
    def _build_format_bar(self):
        """Вторая панель — шрифт, стили, выравнивание, списки, отступы."""
        fbar = tk.Frame(self.root, bg=COLORS["bg_toolbar"], pady=3, padx=8)
        fbar.pack(side="top", fill="x")
        tk.Frame(fbar, bg=COLORS["border"], height=1).pack(side="bottom", fill="x")

        b = lambda ic, tip, cmd, fb=None, ra=None: self._icon_btn(fbar, ic, tip, cmd, fb, ra)
        s = lambda: self._make_sep(fbar)

        # ── Шрифт ──
        fonts = sorted(tkfont.families())
        self.font_combo = ttk.Combobox(fbar,
            textvariable=self.font_family, values=fonts,
            width=18, style="Dark.TCombobox",
        )
        self.font_combo.pack(side="left", padx=(2,4), pady=3)
        self.font_combo.bind("<<ComboboxSelected>>", self._apply_font)
        Tooltip(self.font_combo, "Выбор шрифта")

        # ── Размер ──
        self.size_combo = ttk.Combobox(fbar,
            textvariable=self.font_size,
            values=[8,9,10,11,12,14,16,18,20,22,24,28,32,36,48,72],
            width=4, style="Dark.TCombobox",
        )
        self.size_combo.pack(side="left", padx=(0,4), pady=3)
        self.size_combo.bind("<<ComboboxSelected>>", self._apply_font)
        self.size_combo.bind("<Return>", self._apply_font)
        Tooltip(self.size_combo, "Размер шрифта")

        s()

        # ── Стили текста ──
        b("bold",      "Жирный (Ctrl+B)",       self.toggle_bold,      "Ж",  "btn_bold")
        b("italic",    "Курсив (Ctrl+I)",        self.toggle_italic,    "К",  "btn_italic")
        b("underline", "Подчёркнутый (Ctrl+U)",  self.toggle_underline, "Ч",  "btn_underline")
        b("strike",    "Зачёркнутый",            self.toggle_strike,    "З",  "btn_strike")
        s()

        # ── Цвета ──
        b("font_color","Цвет текста",            self.change_font_color, "А цвет")
        b("highlight", "Цвет фона текста",       self.change_highlight,  "А фон")
        s()

        # ── Выравнивание ──
        b("align_left",    "По левому краю (Ctrl+L)",   self.align_left,    "←")
        b("align_center",  "По центру (Ctrl+E)",         self.align_center,  "—")
        b("align_right",   "По правому краю (Ctrl+R)",   self.align_right,   "→")
        b("align_justify", "По ширине (Ctrl+J)",         self.align_justify, "⇔")
        s()

        # ── Списки ──
        b("bullet_list",   "Маркированный список",       self.insert_bullet_list,   "• —")
        b("numbered_list", "Нумерованный список",        self.insert_numbered_list, "1.")
        s()

        # ── Отступы ──
        b("indent_dec", "Уменьшить отступ",  self.decrease_indent, "←|")
        b("indent_inc", "Увеличить отступ",  self.increase_indent, "|→")
        s()

        # ── Межстрочный интервал ──
        tk.Label(fbar, text="Интервал:",
            bg=COLORS["bg_toolbar"], fg=COLORS["text_dim"],
            font=("Segoe UI", 8),
        ).pack(side="left", padx=(2,2))
        self.spacing_combo = ttk.Combobox(fbar,
            textvariable=self.line_spacing,
            values=[1.0, 1.15, 1.5, 2.0, 2.5, 3.0],
            width=4, style="Dark.TCombobox",
        )
        self.spacing_combo.pack(side="left", padx=(0,4), pady=3)
        self.spacing_combo.bind("<<ComboboxSelected>>", self._apply_spacing)
        Tooltip(self.spacing_combo, "Межстрочный интервал")

    # ══════════════════════════════════════════════════════════════════════════
    #  ОБЛАСТЬ РЕДАКТИРОВАНИЯ
    # ══════════════════════════════════════════════════════════════════════════
    def _build_editor(self):
        container = tk.Frame(self.root, bg=COLORS["bg_main"])
        container.pack(side="top", fill="both", expand=True)

        # Нумерация строк
        self.line_numbers = tk.Text(container,
            width=4, padx=6, state="disabled",
            bg=COLORS["line_num_bg"], fg=COLORS["line_num_fg"],
            font=("Courier New", 10),
            relief="flat", bd=0, wrap="none", cursor="arrow",
        )
        self.line_numbers.pack(side="left", fill="y")
        tk.Frame(container, bg=COLORS["border"], width=1).pack(side="left", fill="y")

        editor_frame = tk.Frame(container, bg=COLORS["bg_editor"])
        editor_frame.pack(side="left", fill="both", expand=True)

        vscroll = tk.Scrollbar(editor_frame, orient="vertical",
            bg=COLORS["bg_toolbar"], troughcolor=COLORS["bg_main"],
            activebackground=COLORS["accent"])
        vscroll.pack(side="right", fill="y")

        hscroll = tk.Scrollbar(editor_frame, orient="horizontal",
            bg=COLORS["bg_toolbar"], troughcolor=COLORS["bg_main"],
            activebackground=COLORS["accent"])
        hscroll.pack(side="bottom", fill="x")

        self.text = tk.Text(editor_frame,
            wrap="word",
            font=(self.font_family.get(), self.font_size.get()),
            bg=COLORS["bg_editor"],
            fg=COLORS["editor_text"],
            insertbackground=COLORS["accent"],
            selectbackground="#D4B8F5",
            selectforeground=COLORS["editor_text"],
            relief="flat", bd=0,
            padx=40, pady=30,
            undo=True, maxundo=-1,
            spacing1=4, spacing3=4,
            yscrollcommand=vscroll.set,
            xscrollcommand=hscroll.set,
        )
        self.text.pack(fill="both", expand=True)
        vscroll.config(command=self._sync_scroll)
        hscroll.config(command=self.text.xview)
        self.text.bind("<KeyRelease>",    self._update_line_numbers)
        self.text.bind("<ButtonRelease>", self._update_line_numbers)
        self.text.bind("<Button-3>",      self._context_menu)
        self._update_line_numbers()

    def _sync_scroll(self, *args):
        self.text.yview(*args)
        self.line_numbers.yview(*args)

    def _update_line_numbers(self, event=None):
        self.line_numbers.config(state="normal")
        self.line_numbers.delete("1.0", "end")
        count = int(self.text.index("end-1c").split(".")[0])
        self.line_numbers.insert("1.0", "\n".join(str(i) for i in range(1, count+1)))
        self.line_numbers.config(state="disabled")

    # ══════════════════════════════════════════════════════════════════════════
    #  СТАТУСНАЯ СТРОКА
    # ══════════════════════════════════════════════════════════════════════════
    def _build_statusbar(self):
        sbar = tk.Frame(self.root, bg=COLORS["bg_statusbar"], pady=3, padx=10)
        sbar.pack(side="bottom", fill="x")
        self.status_cursor = tk.Label(sbar, text="Строка 1, Столбец 1",
            bg=COLORS["bg_statusbar"], fg=COLORS["text_dim"],
            font=("Segoe UI", 8), anchor="w")
        self.status_cursor.pack(side="left")
        self.status_tip = tk.Label(sbar, text="",
            bg=COLORS["bg_statusbar"], fg=COLORS["accent"],
            font=("Segoe UI", 8), anchor="e")
        self.status_tip.pack(side="right")
        self.status_stats = tk.Label(sbar, text="Слов: 0 | Символов: 0",
            bg=COLORS["bg_statusbar"], fg=COLORS["text_dim"],
            font=("Segoe UI", 8), anchor="e")
        self.status_stats.pack(side="right", padx=20)
        self.status_file = tk.Label(sbar, text="Новый документ",
            bg=COLORS["bg_statusbar"], fg=COLORS["text_ui"],
            font=("Segoe UI", 8, "bold"), anchor="e")
        self.status_file.pack(side="right", padx=20)

    def _update_status(self, event=None):
        idx = self.text.index("insert")
        line, col = idx.split(".")
        self.status_cursor.config(text=f"Строка {line}, Столбец {int(col)+1}")
        content = self.text.get("1.0", "end-1c")
        words   = len(content.split()) if content.strip() else 0
        self.status_stats.config(text=f"Слов: {words} | Символов: {len(content)}")
        fname = os.path.basename(self.file_name) if self.file_name else "Новый документ"
        self.status_file.config(text=fname + (" *" if self.is_modified else ""))
        self._update_line_numbers()

    def _show_tip(self, t): self.status_tip.config(text=t)
    def _hide_tip(self):    self.status_tip.config(text="")

    # ══════════════════════════════════════════════════════════════════════════
    #  ГОРЯЧИЕ КЛАВИШИ
    # ══════════════════════════════════════════════════════════════════════════
    def _bind_shortcuts(self):
        r = self.root
        r.bind("<Control-n>", lambda e: self.fm.new_file())
        r.bind("<Control-o>", lambda e: self.fm.open_file())
        r.bind("<Control-s>", lambda e: self.fm.save_file())
        r.bind("<Control-S>", lambda e: self.fm.save_as_file())
        r.bind("<Control-z>", lambda e: self.undo())
        r.bind("<Control-y>", lambda e: self.redo())
        r.bind("<Control-x>", lambda e: self.cut())
        r.bind("<Control-c>", lambda e: self.copy())
        r.bind("<Control-v>", lambda e: self.paste())
        r.bind("<Control-a>", lambda e: self.select_all())
        r.bind("<Control-f>", lambda e: self.find_replace())
        r.bind("<Control-b>", lambda e: self.toggle_bold())
        r.bind("<Control-i>", lambda e: self.toggle_italic())
        r.bind("<Control-u>", lambda e: self.toggle_underline())
        r.bind("<Control-l>", lambda e: self.align_left())
        r.bind("<Control-e>", lambda e: self.align_center())
        r.bind("<Control-r>", lambda e: self.align_right())
        r.bind("<Control-j>", lambda e: self.align_justify())

    # ══════════════════════════════════════════════════════════════════════════
    #  ПРАВКА
    # ══════════════════════════════════════════════════════════════════════════
    def undo(self):
        try: self.text.edit_undo()
        except tk.TclError: pass

    def redo(self):
        try: self.text.edit_redo()
        except tk.TclError: pass

    def cut(self):
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.text.selection_get())
            self.text.delete("sel.first", "sel.last")
        except tk.TclError: pass

    def copy(self):
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.text.selection_get())
        except tk.TclError: pass

    def paste(self):
        try: self.text.insert("insert", self.root.clipboard_get())
        except tk.TclError: pass

    def delete_sel(self):
        try: self.text.delete("sel.first", "sel.last")
        except tk.TclError: pass

    def select_all(self): self.text.tag_add("sel", "1.0", "end")

    def clear_all(self):
        if messagebox.askyesno("Очистить", "Удалить весь текст?"):
            self.text.delete("1.0", "end")

    def _on_text_modified(self, event=None):
        self.is_modified = True
        self.text.edit_modified(False)
        self._update_status()

    # ══════════════════════════════════════════════════════════════════════════
    #  ФОРМАТИРОВАНИЕ
    # ══════════════════════════════════════════════════════════════════════════
    def _get_selection(self):
        try:    return self.text.index("sel.first"), self.text.index("sel.last")
        except: return None, None

    def _new_tag(self, prefix, **kw):
        self.tag_counter += 1
        tag = f"{prefix}_{self.tag_counter}"
        self.text.tag_configure(tag, **kw)
        return tag

    def _apply_font(self, event=None):
        try:
            fam = self.font_family.get()
            sz  = int(self.font_size.get())
        except ValueError: return
        start, end = self._get_selection()
        if not start:
            self.text.config(font=(fam, sz)); return
        self.text.tag_add(self._new_tag("font", font=(fam, sz)), start, end)

    def toggle_bold(self):
        self.font_bold = not self.font_bold
        start, end = self._get_selection()
        if not start: return
        tag = self._new_tag("bold", font=(self.font_family.get(),
            int(self.font_size.get()), "bold" if self.font_bold else "normal"))
        self.text.tag_add(tag, start, end)
        self.btn_bold.config(bg=COLORS["accent"] if self.font_bold else COLORS["btn_normal"])

    def toggle_italic(self):
        self.font_italic = not self.font_italic
        start, end = self._get_selection()
        if not start: return
        tag = self._new_tag("italic", font=(self.font_family.get(),
            int(self.font_size.get()), "italic" if self.font_italic else "roman"))
        self.text.tag_add(tag, start, end)
        self.btn_italic.config(bg=COLORS["accent"] if self.font_italic else COLORS["btn_normal"])

    def toggle_underline(self):
        self.font_underline = not self.font_underline
        start, end = self._get_selection()
        if not start: return
        self.text.tag_add(self._new_tag("ul", underline=int(self.font_underline)), start, end)
        self.btn_underline.config(bg=COLORS["accent"] if self.font_underline else COLORS["btn_normal"])

    def toggle_strike(self):
        self.font_strike = not self.font_strike
        start, end = self._get_selection()
        if not start: return
        self.text.tag_add(self._new_tag("strike", overstrike=int(self.font_strike)), start, end)
        self.btn_strike.config(bg=COLORS["accent"] if self.font_strike else COLORS["btn_normal"])

    def change_font_color(self):
        color = colorchooser.askcolor(initialcolor=self.font_color, title="Цвет текста")
        if color and color[1]:
            self.font_color = color[1]
            start, end = self._get_selection()
            if not start: return
            self.text.tag_add(self._new_tag("fg", foreground=self.font_color), start, end)

    def change_highlight(self):
        color = colorchooser.askcolor(initialcolor=self.font_bg, title="Цвет фона текста")
        if color and color[1]:
            self.font_bg = color[1]
            start, end = self._get_selection()
            if not start: return
            self.text.tag_add(self._new_tag("bg", background=self.font_bg), start, end)

    def _apply_justify(self, justify):
        start, end = self._get_selection()
        s = self.text.index(f"{start} linestart") if start else self.text.index("insert linestart")
        e = self.text.index(f"{end} lineend")     if start else self.text.index("insert lineend")
        self.text.tag_add(self._new_tag("align", justify=justify), s, e+"+1c")

    def align_left(self):    self._apply_justify("left")
    def align_center(self):  self._apply_justify("center")
    def align_right(self):   self._apply_justify("right")
    def align_justify(self): self._apply_justify("left")

    def increase_indent(self):
        pos = self.text.index("insert linestart")
        end = self.text.index("insert lineend+1c")
        cur = self._get_indent(pos)
        self.text.tag_add(self._new_tag(f"ind{cur+30}", lmargin1=cur+30, lmargin2=cur+30), pos, end)

    def decrease_indent(self):
        pos = self.text.index("insert linestart")
        end = self.text.index("insert lineend+1c")
        new = max(0, self._get_indent(pos) - 30)
        self.text.tag_add(self._new_tag(f"ind{new}", lmargin1=new, lmargin2=new), pos, end)

    def _get_indent(self, pos):
        for t in self.text.tag_names(pos):
            if t.startswith("ind"):
                try: return int(t.split("_")[0][3:])
                except: pass
        return 0

    def _apply_spacing(self, event=None):
        try: sp = float(self.line_spacing.get())
        except: return
        px = int(sp * 14)
        start, end = self._get_selection()
        tag = self._new_tag("spacing", spacing1=px, spacing3=px)
        self.text.tag_add(tag, start if start else "1.0", end if end else "end")

    # ══════════════════════════════════════════════════════════════════════════
    #  ВСТАВКА ЭЛЕМЕНТОВ
    # ══════════════════════════════════════════════════════════════════════════
    def insert_bullet_list(self):
        d = ListDialog(self.root, "Маркированный список")
        if d.result:
            for item in d.result: self.text.insert("insert", f"  •  {item}\n")

    def insert_numbered_list(self):
        d = ListDialog(self.root, "Нумерованный список")
        if d.result:
            for i, item in enumerate(d.result, 1): self.text.insert("insert", f"  {i}.  {item}\n")

    def insert_table(self):
        d = TableDialog(self.root)
        if d.result:
            rows, cols, headers = d.result
            col_w = 14
            sep   = "+" + (("-"*col_w+"+") * cols)
            self.text.insert("insert", "\n")
            if headers:
                hdr = "|" + "".join(h[:col_w-2].center(col_w)+"|" for h in headers)
                self.text.insert("insert", sep+"\n"+hdr+"\n")
            self.text.insert("insert", sep+"\n")
            for _ in range(rows):
                self.text.insert("insert", "|"+(" "*col_w+"|")*cols+"\n"+sep+"\n")
            self.text.insert("insert", "\n")

    def insert_image(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            title="Выбрать изображение",
            filetypes=[("Изображения","*.png *.jpg *.jpeg *.gif *.bmp"),("Все файлы","*.*")])
        if not path: return
        try:
            img = Image.open(path)
            if img.width > 500:
                img = img.resize((500, int(img.height*500/img.width)), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self._images.append(photo)
            self.text.image_create("insert", image=photo, padx=4, pady=4)
            self.text.insert("insert", f"\n[Изображение: {os.path.basename(path)}]\n")
        except Exception as e:
            messagebox.showerror("Ошибка вставки", str(e))

    def insert_link(self):
        d = LinkDialog(self.root)
        if not d.result: return
        url, display = d.result
        text = display if display else url
        tag  = self._new_tag("link", foreground=COLORS["accent2"], underline=1,
                              font=(self.font_family.get(), int(self.font_size.get())))
        start = self.text.index("insert")
        self.text.insert("insert", text)
        self.text.tag_add(tag, start, self.text.index("insert"))
        self.text.tag_bind(tag, "<Button-1>", lambda e, u=url: webbrowser.open(u))
        self.text.tag_bind(tag, "<Enter>",    lambda e: self.text.config(cursor="hand2"))
        self.text.tag_bind(tag, "<Leave>",    lambda e: self.text.config(cursor="xterm"))

    def insert_chart(self):
        d = ChartDialog(self.root)
        if not d.result: return
        title, values = d.result
        if not values: return
        max_val = max(v for _,v in values) or 1
        h = 10
        chart = f"\n  {title}\n  " + "─"*(len(values)*6+2) + "\n"
        for row in range(h, 0, -1):
            chart += "  │" + "".join("  ██  " if int((v/max_val)*h)>=row else "      " for _,v in values) + "\n"
        chart += "  └" + "─"*(len(values)*6+1) + "\n"
        chart += "   " + "".join(f" {l[:4]:^5}" for l,_ in values) + "\n"
        chart += "   " + "".join(f" {int(v):^5}" for _,v in values) + "\n\n"
        self.text.insert("insert", chart)

    def insert_hr(self):
        self.text.insert("insert", "\n" + "─"*60 + "\n\n")

    def find_replace(self):
        FindReplaceDialog(self.root, self.text)

    def _context_menu(self, event):
        ctx = tk.Menu(self.root, tearoff=0,
            bg=COLORS["bg_toolbar"], fg=COLORS["text_ui"],
            activebackground=COLORS["accent"], activeforeground="#1E1E2E")
        ctx.add_command(label="Вырезать",     command=self.cut)
        ctx.add_command(label="Копировать",   command=self.copy)
        ctx.add_command(label="Вставить",     command=self.paste)
        ctx.add_separator()
        ctx.add_command(label="Выделить всё", command=self.select_all)
        ctx.add_separator()
        ctx.add_command(label="Жирный",       command=self.toggle_bold)
        ctx.add_command(label="Курсив",       command=self.toggle_italic)
        ctx.add_command(label="Подчёркнутый", command=self.toggle_underline)
        ctx.tk_popup(event.x_root, event.y_root)

    def show_about(self):
        win = tk.Toplevel(self.root)
        win.title("О программе"); win.geometry("420x280")
        win.resizable(False,False); win.configure(bg=COLORS["bg_main"]); win.transient(self.root)
        tk.Label(win, text="Текстовый Редактор", font=("Georgia",18,"bold"),
            bg=COLORS["bg_main"], fg=COLORS["accent"]).pack(pady=(30,6))
        tk.Label(win, text="Лабораторная работа\nРазработан на Python 3 + Tkinter",
            font=("Segoe UI",10), bg=COLORS["bg_main"], fg=COLORS["text_ui"],
            justify="center").pack(pady=4)
        tk.Label(win,
            text="Функции: создание/открытие/сохранение (.txt, .rtf, .pdf)\n"
                 "форматирование текста, таблицы, списки,\nизображения, ссылки, графики, поиск и замена",
            font=("Segoe UI",9), bg=COLORS["bg_main"], fg=COLORS["text_dim"],
            justify="center").pack(pady=10)
        tk.Button(win, text="Закрыть", command=win.destroy,
            bg=COLORS["accent"], fg="#1E1E2E", font=("Segoe UI",10,"bold"),
            relief="flat", padx=20, pady=6, cursor="hand2").pack(pady=10)

    def quit_app(self):
        if self.fm._check_save(): self.root.quit()
