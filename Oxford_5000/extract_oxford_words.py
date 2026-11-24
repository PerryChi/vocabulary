"""从牛津 5000 词 PDF 中提取单词和词性。

安装依赖：python -m pip install -r requirements.txt
运行方式：python extract_oxford_words.py
指定文件：python extract_oxford_words.py input.pdf output.txt

默认读取脚本同目录下的牛津词表 PDF，并写入同名 UTF-8 TXT 文件。
"""

import argparse
import re
from pathlib import Path


DEFAULT_PDF = Path(__file__).resolve().with_name(
    "牛津词表2-niu-jin-5000ci-zhuan-lian-jie-shang-chuan-the-oxford-5000-by-cefr-level.pdf"
)

POS_LABEL = r"(?:adj\.?|adv\.?|conj\.?|det\.?|exclam\.?|n\.?|number|phr\.?|prep\.?|pron\.?|v\.?)"
ENTRY_PATTERN = re.compile(
    rf"^(?P<word>.+?)\s+(?P<pos>{POS_LABEL}(?:\s*[,/]\s*{POS_LABEL})*)$",
    re.IGNORECASE,
)


def extract_entries(text: str) -> list[tuple[str, str]]:
    """从 PDF 提取的文本中，按原顺序解析 (单词, 词性) 条目。"""
    entries = []
    for original_line in text.splitlines():
        line = original_line.replace("© Oxford University Press", "")
        line = line.replace("The Oxford 5000™ by CEFR level", "")
        line = re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", "", line)
        line = re.sub(r"\s+", " ", line).strip()
        match = ENTRY_PATTERN.fullmatch(line)
        if match:
            word = match.group("word").strip()
            pos = match.group("pos").strip()
            entries.append((word, pos))
    return entries


def extract_pdf_text(pdf_path: Path) -> str:
    """读取 PDF 各页的文本；缺少 pypdf 时给出安装提示。"""
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError(
            "缺少 pypdf 依赖，请先运行：python -m pip install -r requirements.txt"
        ) from exc

    reader = PdfReader(str(pdf_path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def main() -> None:
    parser = argparse.ArgumentParser(description="从 Oxford 5000 PDF 提取单词和词性")
    parser.add_argument(
        "pdf_file",
        nargs="?",
        type=Path,
        default=DEFAULT_PDF,
        help="输入 PDF，默认读取脚本同目录中的牛津词表 PDF",
    )
    parser.add_argument(
        "txt_file",
        nargs="?",
        type=Path,
        help="输出 TXT，默认使用 PDF 同名的 .txt 文件",
    )
    args = parser.parse_args()
    output_path = args.txt_file or args.pdf_file.with_suffix(".txt")

    if not args.pdf_file.is_file():
        parser.error(f"找不到输入 PDF：{args.pdf_file}")

    try:
        entries = extract_entries(extract_pdf_text(args.pdf_file))
    except RuntimeError as exc:
        parser.error(str(exc))
    except Exception as exc:
        parser.error(f"读取 PDF 失败：{exc}")

    if not entries:
        parser.error("没有从 PDF 中识别到单词和词性条目；请检查 PDF 文本格式。")

    content = "\n".join(f"{word}\t{pos}" for word, pos in entries) + "\n"
    try:
        output_path.write_text(content, encoding="utf-8")
    except OSError as exc:
        parser.error(f"无法写入输出文件 {output_path}：{exc}")

    print(f"已提取 {len(entries)} 个词条：{output_path}")


if __name__ == "__main__":
    main()
