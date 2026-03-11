# -*- coding: utf-8 -*-
# file_manager.py — Все операции с файлами: открытие, сохранение, экспорт в PDF/RTF

import os
from tkinter import filedialog, messagebox

# ─── Попытка импорта reportlab для экспорта в PDF ─────────────────────────────
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.units import cm
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


class FileManager:
    """
    Класс отвечает за все файловые операции редактора:
    - создание нового документа
    - открытие существующего файла (.txt, .rtf)
    - сохранение и «сохранить как»
    - экспорт в форматы PDF и RTF
    """

    def __init__(self, editor):
        # Ссылка на главный объект редактора (для доступа к тексту и заголовку)
        self.editor = editor

    # ──────────────────────────────────────────────────────────────────────────
    #  НОВЫЙ ДОКУМЕНТ
    # ──────────────────────────────────────────────────────────────────────────
    def new_file(self):
        """Создать новый пустой документ. Предложить сохранить текущий если нужно."""
        if not self._check_save():
            return
        self.editor.text.delete("1.0", "end")
        self.editor.file_name   = ""
        self.editor.is_modified = False
        self.editor.root.title("Безымянный — Текстовый Редактор")
        self.editor._update_status()

    # ──────────────────────────────────────────────────────────────────────────
    #  ОТКРЫТИЕ ФАЙЛА
    # ──────────────────────────────────────────────────────────────────────────
    def open_file(self):
        """Открыть диалог выбора файла и загрузить его содержимое."""
        if not self._check_save():
            return
        path = filedialog.askopenfilename(
            title="Открыть файл",
            filetypes=[
                ("Текстовые файлы", "*.txt"),
                ("RTF файлы",       "*.rtf"),
                ("Все файлы",       "*.*"),
            ]
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            self.editor.text.delete("1.0", "end")
            # Для RTF-файлов убираем управляющие последовательности
            if path.lower().endswith(".rtf"):
                content = self._strip_rtf(content)
            self.editor.text.insert("1.0", content)
            self.editor.file_name   = path
            self.editor.is_modified = False
            self.editor.root.title(
                f"{os.path.basename(path)} — Текстовый Редактор"
            )
            self.editor._update_status()
        except Exception as e:
            messagebox.showerror("Ошибка открытия файла", str(e))

    # ──────────────────────────────────────────────────────────────────────────
    #  СОХРАНЕНИЕ ФАЙЛА
    # ──────────────────────────────────────────────────────────────────────────
    def save_file(self):
        """Сохранить файл по текущему пути. Если пути нет — вызвать «Сохранить как»."""
        if not self.editor.file_name:
            self.save_as_file()
            return
        self._write_file(self.editor.file_name)

    def save_as_file(self):
        """Открыть диалог и сохранить файл с новым именем."""
        path = filedialog.asksaveasfilename(
            title="Сохранить как",
            defaultextension=".txt",
            filetypes=[
                ("Текстовые файлы", "*.txt"),
                ("RTF файлы",       "*.rtf"),
                ("Все файлы",       "*.*"),
            ]
        )
        if not path:
            return
        self.editor.file_name = path
        self._write_file(path)

    def _write_file(self, path):
        """Записать содержимое текстового поля в файл на диске."""
        try:
            content = self.editor.text.get("1.0", "end-1c")
            if path.lower().endswith(".rtf"):
                # Сохраняем в формате RTF с поддержкой кириллицы
                data = self._to_rtf(content)
                with open(path, "w", encoding="ascii", errors="replace") as f:
                    f.write(data)
            else:
                # Обычный текстовый файл в UTF-8
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
            self.editor.is_modified = False
            self.editor.root.title(
                f"{os.path.basename(path)} — Текстовый Редактор"
            )
            self.editor._update_status()
        except Exception as e:
            messagebox.showerror("Ошибка сохранения файла", str(e))

    # ──────────────────────────────────────────────────────────────────────────
    #  ЭКСПОРТ В PDF
    # ──────────────────────────────────────────────────────────────────────────
    def export_pdf(self):
        """Экспортировать текущий документ в PDF через библиотеку reportlab."""
        if not REPORTLAB_AVAILABLE:
            messagebox.showwarning(
                "Библиотека не установлена",
                "Для экспорта в PDF установите reportlab:\n\n"
                "pip install reportlab",
            )
            return
        path = filedialog.asksaveasfilename(
            title="Экспорт в PDF",
            defaultextension=".pdf",
            filetypes=[("PDF файлы", "*.pdf")],
        )
        if not path:
            return
        try:
            content = self.editor.text.get("1.0", "end-1c")
            doc     = SimpleDocTemplate(
                path, pagesize=A4,
                leftMargin=2*cm, rightMargin=2*cm,
                topMargin=2*cm,  bottomMargin=2*cm,
            )
            styles = getSampleStyleSheet()
            story  = []
            # Каждый абзац — отдельный блок; пустая строка → отступ
            for para in content.split("\n"):
                if para.strip():
                    safe = (para
                        .replace("&", "&amp;")
                        .replace("<", "&lt;")
                        .replace(">", "&gt;")
                    )
                    story.append(Paragraph(safe, styles["Normal"]))
                else:
                    story.append(Spacer(1, 10))
            doc.build(story)
            messagebox.showinfo("Экспорт завершён", f"Файл сохранён:\n{path}")
        except Exception as e:
            messagebox.showerror("Ошибка экспорта PDF", str(e))

    # ──────────────────────────────────────────────────────────────────────────
    #  ЭКСПОРТ В RTF
    # ──────────────────────────────────────────────────────────────────────────
    def export_rtf(self):
        """Экспортировать текущий документ в формат RTF."""
        path = filedialog.asksaveasfilename(
            title="Экспорт в RTF",
            defaultextension=".rtf",
            filetypes=[("RTF файлы", "*.rtf")],
        )
        if not path:
            return
        try:
            content = self.editor.text.get("1.0", "end-1c")
            rtf     = self._to_rtf(content)
            with open(path, "w", encoding="ascii", errors="replace") as f:
                f.write(rtf)
            messagebox.showinfo("Экспорт завершён", f"Файл сохранён:\n{path}")
        except Exception as e:
            messagebox.showerror("Ошибка экспорта RTF", str(e))

    # ──────────────────────────────────────────────────────────────────────────
    #  ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ
    # ──────────────────────────────────────────────────────────────────────────
    def _check_save(self):
        """
        Если документ изменён — предложить сохранить.
        Возвращает False если пользователь нажал «Отмена».
        """
        if self.editor.is_modified:
            ans = messagebox.askyesnocancel(
                "Сохранить изменения?",
                "Документ был изменён. Сохранить перед закрытием?",
            )
            if ans is None:
                return False    # Отмена — прервать действие
            elif ans:
                self.save_file()  # Да — сохранить
        return True

    def _to_rtf(self, text_content):
        """
        Конвертировать простой текст в формат RTF.
        Кириллица передаётся через Unicode-escape \\uN.
        """
        rtf  = r"{\rtf1\ansi\ansicpg1251\deff0"
        rtf += r"{\fonttbl{\f0\froman\fcharset204 Times New Roman;}}"
        rtf += r"{\colortbl ;\red0\green0\blue0;}"
        rtf += r"\f0\fs24\cf1 "
        for char in text_content:
            code = ord(char)
            if code < 128:
                if char in "\\{}":
                    rtf += "\\" + char   # Экранируем спецсимволы RTF
                elif char == "\n":
                    rtf += r"\par "      # Перевод строки в RTF
                else:
                    rtf += char
            else:
                rtf += f"\\u{code}?"     # Unicode-символ (кириллица и др.)
        rtf += "}"
        return rtf

    def _strip_rtf(self, rtf_content):
        """
        Убрать RTF-теги из содержимого файла и вернуть чистый текст.
        Используется при открытии .rtf файлов.
        """
        import re
        text = re.sub(r'\\[a-z]+\-?\d* ?', '', rtf_content)  # управляющие слова
        text = re.sub(r'[{}\\]', '', text)                     # скобки и слеши
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        return text.strip()
