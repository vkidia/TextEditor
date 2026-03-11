# -*- coding: utf-8 -*-
# file_manager.py — Все операции с файлами: открытие, сохранение, экспорт в PDF/RTF

import os
import re
from tkinter import filedialog, messagebox

# ─── reportlab ────────────────────────────────────────────────────────────────
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors as rl_colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
    )
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfbase.pdfmetrics import registerFontFamily

    _DEJAVU = {
        "normal":     "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "bold":       "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "italic":     "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf",
        "boldItalic": "/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf",
    }
    if all(os.path.exists(p) for p in _DEJAVU.values()):
        pdfmetrics.registerFont(TTFont("DejaVu",            _DEJAVU["normal"]))
        pdfmetrics.registerFont(TTFont("DejaVu-Bold",       _DEJAVU["bold"]))
        pdfmetrics.registerFont(TTFont("DejaVu-Italic",     _DEJAVU["italic"]))
        pdfmetrics.registerFont(TTFont("DejaVu-BoldItalic", _DEJAVU["boldItalic"]))
        registerFontFamily("DejaVu",
            normal="DejaVu", bold="DejaVu-Bold",
            italic="DejaVu-Italic", boldItalic="DejaVu-BoldItalic")
        _PDF_FONT      = "DejaVu"
        _PDF_FONT_BOLD = "DejaVu-Bold"
    else:
        _PDF_FONT      = "Helvetica"
        _PDF_FONT_BOLD = "Helvetica-Bold"

    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    _PDF_FONT      = "Helvetica"
    _PDF_FONT_BOLD = "Helvetica-Bold"


class FileManager:
    def __init__(self, editor):
        self.editor = editor

    # ── Новый документ ────────────────────────────────────────────────────────
    def new_file(self):
        if not self._check_save():
            return
        self.editor.text.delete("1.0", "end")
        self.editor.file_name   = ""
        self.editor.is_modified = False
        self.editor.root.title("Безымянный — Текстовый Редактор")
        self.editor._update_status()

    # ── Открытие файла ────────────────────────────────────────────────────────
    def open_file(self):
        if not self._check_save():
            return
        path = filedialog.askopenfilename(
            title="Открыть файл",
            filetypes=[("Текстовые файлы","*.txt"),("RTF файлы","*.rtf"),("Все файлы","*.*")]
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            self.editor.text.delete("1.0", "end")
            if path.lower().endswith(".rtf"):
                content = self._strip_rtf(content)
            self.editor.text.insert("1.0", content)
            self.editor.file_name   = path
            self.editor.is_modified = False
            self.editor.root.title(f"{os.path.basename(path)} — Текстовый Редактор")
            self.editor._update_status()
        except Exception as e:
            messagebox.showerror("Ошибка открытия файла", str(e))

    # ── Сохранение ───────────────────────────────────────────────────────────
    def save_file(self):
        if not self.editor.file_name:
            self.save_as_file()
            return
        self._write_file(self.editor.file_name)

    def save_as_file(self):
        path = filedialog.asksaveasfilename(
            title="Сохранить как",
            defaultextension=".txt",
            filetypes=[("Текстовые файлы","*.txt"),("RTF файлы","*.rtf"),("Все файлы","*.*")]
        )
        if not path:
            return
        self.editor.file_name = path
        self._write_file(path)

    def _write_file(self, path):
        try:
            content = self.editor.text.get("1.0", "end-1c")
            if path.lower().endswith(".rtf"):
                with open(path, "wb") as f:
                    f.write(self._to_rtf(content))
            else:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
            self.editor.is_modified = False
            self.editor.root.title(f"{os.path.basename(path)} — Текстовый Редактор")
            self.editor._update_status()
        except Exception as e:
            messagebox.showerror("Ошибка сохранения файла", str(e))

    # ── Экспорт в PDF ─────────────────────────────────────────────────────────
    def export_pdf(self):
        if not REPORTLAB_AVAILABLE:
            messagebox.showwarning("Библиотека не установлена",
                "Для экспорта в PDF установите reportlab:\n\npip install reportlab")
            return
        path = filedialog.asksaveasfilename(
            title="Экспорт в PDF",
            defaultextension=".pdf",
            filetypes=[("PDF файлы","*.pdf")]
        )
        if not path:
            return
        try:
            doc = SimpleDocTemplate(
                path, pagesize=A4,
                leftMargin=2*cm, rightMargin=2*cm,
                topMargin=2*cm, bottomMargin=2*cm,
            )
            normal = ParagraphStyle("CyrNormal", fontName=_PDF_FONT,
                                    fontSize=11, leading=16, spaceAfter=4)
            bullet = ParagraphStyle("CyrBullet", fontName=_PDF_FONT,
                                    fontSize=11, leading=16,
                                    leftIndent=20, spaceAfter=2)
            story  = self._build_story(normal, bullet)
            doc.build(story)
            messagebox.showinfo("Экспорт завершён", f"Файл сохранён:\n{path}")
        except Exception as e:
            messagebox.showerror("Ошибка экспорта PDF", str(e))

    def _build_story(self, normal_style, bullet_style):
        story   = []
        content = self.editor.text.get("1.0", "end-1c")
        lines   = content.split("\n")
        img_map = self._get_embedded_images()   # {basename: full_path}
        i       = 0
        while i < len(lines):
            line = lines[i]

            # ASCII-таблица
            if re.match(r"^\+[-+]+\+$", line.strip()):
                tbl_lines, consumed = self._collect_table(lines, i)
                rl_tbl = self._ascii_to_table(tbl_lines, normal_style)
                if rl_tbl:
                    story.append(Spacer(1, 6))
                    story.append(rl_tbl)
                    story.append(Spacer(1, 6))
                i += consumed
                continue

            # Маркированный список
            if line.startswith("  •  "):
                story.append(Paragraph("• " + self._esc(line[5:].strip()), bullet_style))
                i += 1; continue

            # Нумерованный список
            m = re.match(r"^\s+(\d+)\.\s+(.+)", line)
            if m:
                story.append(Paragraph(f"{m.group(1)}. {self._esc(m.group(2))}", bullet_style))
                i += 1; continue

            # Горизонтальная линия
            if len(line) > 8 and all(c == "─" for c in line.strip()):
                from reportlab.platypus import HRFlowable
                story.append(Spacer(1, 4))
                story.append(HRFlowable(width="100%", thickness=1, color=rl_colors.grey))
                story.append(Spacer(1, 4))
                i += 1; continue

            # Изображение
            if line.startswith("[Изображение:") and line.endswith("]"):
                img_name = line[len("[Изображение: "):-1].strip()
                img_path = img_map.get(img_name)
                if img_path and os.path.exists(img_path):
                    try:
                        from PIL import Image as PILImage
                        pil = PILImage.open(img_path)
                        w, h = pil.size
                        max_w = 14 * cm
                        if w > max_w:
                            h = int(h * max_w / w)
                            w = max_w
                        story.append(Spacer(1, 6))
                        story.append(RLImage(img_path, width=w, height=h))
                        story.append(Spacer(1, 6))
                    except Exception:
                        story.append(Paragraph(self._esc(line), normal_style))
                else:
                    story.append(Paragraph(self._esc(line), normal_style))
                i += 1; continue

            # Обычный текст
            if line.strip():
                story.append(Paragraph(self._esc(line), normal_style))
            else:
                story.append(Spacer(1, 8))
            i += 1
        return story

    def _collect_table(self, lines, start):
        collected = []
        i = start
        while i < len(lines):
            l = lines[i]
            if l.startswith("+") or l.startswith("|"):
                collected.append(l)
                i += 1
            else:
                break
        return collected, i - start

    def _ascii_to_table(self, lines, style):
        rows = []
        for line in lines:
            if line.startswith("|") and not re.match(r"^\+[-+]+\+$", line.strip()):
                cells = [c.strip() for c in line.split("|")[1:-1]]
                rows.append(cells)
        if not rows:
            return None
        n_cols = max(len(r) for r in rows)
        col_w  = (17 * cm) / n_cols
        # Нормализуем
        for r in rows:
            while len(r) < n_cols:
                r.append("")
        para_rows = [
            [Paragraph(self._esc(c), style) for c in row]
            for row in rows
        ]
        t = Table(para_rows, colWidths=[col_w] * n_cols)
        t.setStyle(TableStyle([
            ("FONTNAME",      (0, 0), (-1, -1), _PDF_FONT),
            ("FONTNAME",      (0, 0), (-1,  0), _PDF_FONT_BOLD),
            ("FONTSIZE",      (0, 0), (-1, -1), 10),
            ("BACKGROUND",    (0, 0), (-1,  0), rl_colors.HexColor("#D8D8D8")),
            ("GRID",          (0, 0), (-1, -1), 0.5, rl_colors.black),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING",   (0, 0), (-1, -1), 7),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 7),
        ]))
        return t

    def _get_embedded_images(self):
        result = {}
        for path in getattr(self.editor, "_image_paths", {}).values():
            result[os.path.basename(path)] = path
        return result

    @staticmethod
    def _esc(text):
        return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))

    # ── Экспорт в RTF ─────────────────────────────────────────────────────────
    def export_rtf(self):
        path = filedialog.asksaveasfilename(
            title="Экспорт в RTF",
            defaultextension=".rtf",
            filetypes=[("RTF файлы","*.rtf")]
        )
        if not path:
            return
        try:
            content = self.editor.text.get("1.0", "end-1c")
            with open(path, "wb") as f:
                f.write(self._to_rtf(content))
            messagebox.showinfo("Экспорт завершён", f"Файл сохранён:\n{path}")
        except Exception as e:
            messagebox.showerror("Ошибка экспорта RTF", str(e))

    def _to_rtf(self, text_content):
        """
        RTF с кодировкой Windows-1251 (\'XX) — корректно открывается
        в Word, LibreOffice и большинстве RTF-просмотрщиков.
        """
        lines = text_content.split("\n")
        parts = []
        for line in lines:
            parts.append(self._rtf_encode_line(line) + r"\par ")

        header = (
            r"{\rtf1\ansi\ansicpg1251\deff0\deflang1049"
            r"{\fonttbl{\f0\froman\fcharset204 Times New Roman;}}"
            r"{\colortbl;\red0\green0\blue0;}"
            r"\f0\fs24\cf1 "
        )
        body = "\n".join(parts)
        return (header + "\n" + body + "\n}").encode("cp1251", errors="replace")

    @staticmethod
    def _rtf_encode_line(line):
        out = ""
        for ch in line:
            if ch == "\\":
                out += "\\\\"
            elif ch == "{":
                out += "\\{"
            elif ch == "}":
                out += "\\}"
            elif ord(ch) < 128:
                out += ch
            else:
                try:
                    byte_val = ch.encode("cp1251")[0]
                    out += f"\\'{byte_val:02x}"
                except (UnicodeEncodeError, IndexError):
                    out += f"\\u{ord(ch)}?"
        return out

    # ── Прочее ────────────────────────────────────────────────────────────────
    def _check_save(self):
        if self.editor.is_modified:
            ans = messagebox.askyesnocancel(
                "Сохранить изменения?",
                "Документ был изменён. Сохранить перед закрытием?",
            )
            if ans is None:
                return False
            elif ans:
                self.save_file()
        return True

    def _strip_rtf(self, rtf_content):
        text = re.sub(r"\\[a-z]+\-?\d* ?", "", rtf_content)
        text = re.sub(r"[{}\\]", "", text)
        return text.replace("\r\n", "\n").replace("\r", "\n").strip()
