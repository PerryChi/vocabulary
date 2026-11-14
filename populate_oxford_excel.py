#!/usr/bin/env python3
"""Write the Oxford word list TXT into the Book1.xlsx study workbook."""

from __future__ import annotations

import argparse
import math
import re
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side


DEFAULT_TXT = "牛津词表2-牛津5000常用中文释义与音标学习版.txt"
DEFAULT_XLSX = "Book1.xlsx"

POS_PATTERN = re.compile(
    r"^(adj|adv|conj|det|exclam|n|number|phr|prep|pron|v)\.\s*(.*)$",
    re.IGNORECASE,
)

# The source dictionary supplies several pronunciations in a single field for
# these entries. Keep each pronunciation with its matching part of speech.
PRONUNCIATION_OVERRIDES = {
    "abuse": {"n.": "ә'bju:s", "v.": "ә'bju:z"},
    "bow1": {"v.": "bәu", "n.": "bau"},
}

# A few source entries list multiple parts of speech but only label one meaning.
# These short additions keep the split Excel rows useful and non-empty.
MISSING_POS_GLOSSES = {
    ("amateur", "adj."): "业余的；非专业的",
    ("cult", "adj."): "受特定群体狂热追捧的；狂热崇拜的",
    ("dairy", "adj."): "乳品的；乳制品的",
    ("feminist", "adj."): "女权主义的；男女平等主义的",
    ("latter", "n."): "后者",
    ("mainstream", "adj."): "主流的",
    ("militant", "n."): "激进分子；好战分子",
    ("racist", "adj."): "种族主义的；种族歧视的",
}


def split_parts_of_speech(value: str) -> list[str]:
    parts = [part.strip().lower() for part in re.split(r"[,/]", value)]
    return [part if part.endswith(".") else f"{part}." for part in parts if part]


def split_glosses(gloss: str) -> dict[str, list[str]]:
    """Map POS labels in the source gloss to the text that follows each label."""
    segments = re.split(r"[；;]", gloss)
    found: dict[str, list[str]] = {}
    active_pos: str | None = None
    had_labels = False

    for segment in segments:
        segment = segment.strip()
        if not segment:
            continue
        match = POS_PATTERN.match(segment)
        if match:
            had_labels = True
            active_pos = f"{match.group(1).lower()}."
            remainder = match.group(2).strip()
            if remainder:
                found.setdefault(active_pos, []).append(remainder)
        elif active_pos:
            found.setdefault(active_pos, []).append(segment)

    if not had_labels:
        return {"*": [gloss.strip()]}
    return {pos: values for pos, values in found.items()}


def parse_source(txt_path: Path) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for line_number, raw_line in enumerate(txt_path.read_text(encoding="utf-8-sig").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith(("#", "//")):
            continue
        # The study TXT may contain repeated tabs to align visual columns.
        fields = re.split(r"\t+", line)
        if len(fields) < 4:
            continue
        word, raw_pos, phonetic = (field.strip() for field in fields[:3])
        gloss = "\t".join(fields[3:]).strip()
        if not word or not raw_pos or not gloss or word.lower() in {"word", "单词"}:
            continue

        positions = split_parts_of_speech(raw_pos)
        glosses = split_glosses(gloss)
        pronunciations = PRONUNCIATION_OVERRIDES.get(word.lower(), {})
        # In this source, full stops separate alternate IPA strings only for
        # the manually mapped heteronyms above. Other punctuation is preserved.
        for pos_index, pos in enumerate(positions):
            matched_glosses = glosses.get(pos, glosses.get("*", []))
            meaning = "；".join(matched_glosses).strip()
            if not meaning:
                meaning = MISSING_POS_GLOSSES.get((word.lower(), pos), gloss)
            ipa = pronunciations.get(pos, phonetic)
            entries.append({"word": word, "pos": pos, "ipa": ipa, "meaning": meaning})

    if not entries:
        raise ValueError(f"没有从 {txt_path} 解析到词条，请检查 TXT 的制表符分隔格式。")
    return entries


def display_width(value: str) -> int:
    return sum(2 if ord(char) > 0x2FF else 1 for char in value)


def populate_workbook(txt_path: Path, xlsx_path: Path) -> int:
    entries = parse_source(txt_path)
    if xlsx_path.exists():
        workbook = load_workbook(xlsx_path)
        sheet = workbook.active
    else:
        from openpyxl import Workbook

        workbook = Workbook()
        sheet = workbook.active

    sheet.title = "牛津5000"
    # Delete old rows so rerunning starts at row 1 instead of appending after
    # the worksheet's previous used range.
    if sheet.max_row:
        sheet.delete_rows(1, sheet.max_row)
    sheet.row_dimensions.clear()
    for table_name in list(sheet.tables):
        del sheet.tables[table_name]

    headers = ["序号", "单词", "词性", "音标", "释义"]
    sheet.append(headers)
    for serial, entry in enumerate(entries, start=1):
        sheet.append([serial, entry["word"], entry["pos"], entry["ipa"], entry["meaning"]])

    header_fill = PatternFill("solid", fgColor="1F4E78")
    # Excel falls back to the system's Chinese font for glosses and headers.
    header_font = Font(name="Arial", size=10, bold=True, color="FFFFFF")
    body_font = Font(name="Arial", size=10, color="222222")
    bottom_line = Side(style="hair", color="D9E2F3")
    for cell in sheet[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = Border(bottom=Side(style="thin", color="17365D"))
    sheet.row_dimensions[1].height = 24

    for row_num in range(2, len(entries) + 2):
        row = sheet[row_num]
        for cell in row:
            cell.font = body_font
            cell.border = Border(bottom=bottom_line)
            cell.alignment = Alignment(vertical="top" if cell.column == 5 else "center", wrap_text=cell.column == 5)
        row[0].number_format = "0"
        row[3].alignment = Alignment(horizontal="center", vertical="center")
        text = str(row[4].value or "")
        lines = max(1, math.ceil(display_width(text) / 62))
        sheet.row_dimensions[row_num].height = min(90, max(19, lines * 14 + 4))

    for column, width in {"A": 8, "B": 20, "C": 12, "D": 24, "E": 64}.items():
        sheet.column_dimensions[column].width = width
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = f"A1:E{len(entries) + 1}"
    sheet.sheet_view.showGridLines = False
    sheet.sheet_properties.pageSetUpPr.fitToPage = True
    sheet.page_setup.orientation = "landscape"
    sheet.page_setup.paperSize = sheet.PAPERSIZE_A4
    sheet.page_setup.fitToWidth = 1
    sheet.page_setup.fitToHeight = 0
    sheet.page_margins.left = 0.25
    sheet.page_margins.right = 0.25
    sheet.page_margins.top = 0.45
    sheet.page_margins.bottom = 0.45
    sheet.page_margins.header = 0.2
    sheet.page_margins.footer = 0.2
    sheet.print_title_rows = "1:1"
    sheet.print_area = f"A1:E{len(entries) + 1}"
    sheet.oddFooter.center.text = "第 &[Page] 页 / 共 &[Pages] 页"
    sheet.oddFooter.center.size = 8

    workbook.save(xlsx_path)
    return len(entries)


def main() -> None:
    parser = argparse.ArgumentParser(description="将牛津词表 TXT 整理到 Excel 学习表。")
    parser.add_argument("txt", nargs="?", type=Path, help="输入 TXT 路径")
    parser.add_argument("xlsx", nargs="?", type=Path, help="输出 Excel 路径")
    args = parser.parse_args()
    base_dir = Path(__file__).resolve().parent
    txt_path = (args.txt or base_dir / DEFAULT_TXT).resolve()
    xlsx_path = (args.xlsx or base_dir / DEFAULT_XLSX).resolve()

    if not txt_path.is_file():
        raise SystemExit(f"找不到输入文件：{txt_path}")
    count = populate_workbook(txt_path, xlsx_path)
    print(f"已写入 {count} 行词条：{xlsx_path}")


if __name__ == "__main__":
    main()
