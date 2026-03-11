# -*- coding: utf-8 -*-
# config.py — Константы конфигурации: цветовая схема и иконки интерфейса

# ─── Цветовая палитра (тёмная тема Catppuccin Mocha) ──────────────────────────
COLORS = {
    "bg_main":      "#1E1E2E",   # Основной фон окна
    "bg_toolbar":   "#181825",   # Фон панелей инструментов
    "bg_editor":    "#FAFAF8",   # Фон области редактирования (светлый)
    "bg_statusbar": "#11111B",   # Фон статусной строки
    "accent":       "#CBA6F7",   # Акцентный цвет (фиолетовый)
    "accent2":      "#89DCEB",   # Второй акцент (голубой)
    "btn_normal":   "#313244",   # Кнопка — обычное состояние
    "btn_hover":    "#45475A",   # Кнопка — при наведении
    "btn_active":   "#CBA6F7",   # Кнопка — активное состояние
    "text_ui":      "#CDD6F4",   # Цвет текста интерфейса
    "text_dim":     "#6C7086",   # Приглушённый текст
    "border":       "#313244",   # Цвет границ
    "editor_text":  "#1E1E2E",   # Цвет текста в редакторе
    "line_num_bg":  "#E8E8E4",   # Фон номеров строк
    "line_num_fg":  "#9CA3AF",   # Цвет номеров строк
}

# ─── Иконки в виде типографских Unicode-символов (без PNG-файлов) ─────────────
ICONS = {
    "new":            "□",
    "open":           "↗",
    "save":           "↓",
    "save_as":        "⇩",
    "cut":            "✂",
    "copy":           "⎘",
    "paste":          "⎗",
    "undo":           "↺",
    "redo":           "↻",
    "find":           "⌕",
    "bold":           "B",
    "italic":         "I",
    "underline":      "U",
    "strike":         "S",
    "font_color":     "A",
    "highlight":      "▌",
    "align_left":     "⬛⬜⬜",
    "align_center":   "⬜⬛⬜",
    "align_right":    "⬜⬜⬛",
    "align_justify":  "⬛⬛⬛",
    "bullet_list":    "•—",
    "numbered_list":  "1.",
    "table":          "⊞",
    "image":          "⊡",
    "link":           "⊂",
    "increase_indent":"→←",
    "decrease_indent":"←→",
    "chart":          "▦",
    "export_pdf":     "PDF",
    "export_rtf":     "RTF",
    "hr":             "─",
}

# ─── Параметры редактора по умолчанию ─────────────────────────────────────────
DEFAULT_FONT_FAMILY = "Georgia"
DEFAULT_FONT_SIZE   = 12
WINDOW_WIDTH        = 1200
WINDOW_HEIGHT       = 780
WINDOW_MIN_WIDTH    = 900
WINDOW_MIN_HEIGHT   = 600
