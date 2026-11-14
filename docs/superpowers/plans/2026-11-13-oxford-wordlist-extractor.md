# Oxford Wordlist Extractor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract word entries and POS labels from the supplied Oxford 5000 PDF into a UTF-8 text file.

**Architecture:** A standalone argparse CLI uses pypdf to extract page text, recognizes entry lines by their trailing POS markers, then writes tab-separated output. The supplied PDF is the default input and its `.txt` sibling is the default output.

**Tech Stack:** Python standard library and `pypdf`.

**Spec:** `docs/superpowers/specs/2026-11-13-oxford-wordlist-extractor-design.md`

## Global Constraints

- Preserve displayed word spelling, notes, and POS labels.
- Output one `word<TAB>POS` entry per line as UTF-8.
- Skip CEFR headings, repeated document headers/footers, and page numbers.
- Do not require OCR or network access at runtime.

## Review Focus

- Multi-POS entries such as `bid n., v.` must remain a single entry with all labels.
- Words with spaces or notes such as `counter (long flat surface) n.` must not be split incorrectly.
- Page headers, footers, and CEFR section labels must not be emitted as entries.
- Missing input and unreadable PDF errors should be clear and non-zero.
- A PDF with no recognized entries must fail clearly instead of silently creating an empty result.

---

### Task 1: Add the PDF extraction CLI

**Files:**
- Create: `extract_oxford_words.py`
- Create: `requirements.txt` (if no dependency manifest exists)

**Interfaces:**
- `extract_entries(text: str) -> list[tuple[str, str]]`: return `(word, POS)` entries in document order.
- CLI positional arguments: optional input PDF path and optional output TXT path.

- [x] Add the standalone CLI using `pypdf`, UTF-8 output, sensible same-basename `.txt` default, clear parser errors, and a documented install/run example in the module docstring.

### Task 2: Generate the requested text file

**Files:**
- Create: `牛津词表2-niu-jin-5000ci-zhuan-lian-jie-shang-chuan-the-oxford-5000-by-cefr-level.txt`

**Interfaces:**
- Consume the CLI from Task 1 with the supplied PDF as input.

- [x] Generate the requested TXT using the implemented entry parser and confirm it contains extracted entries, each with a word and POS separated by a tab.

Ruling: `pypdf` is not installed in the current environment, so the supplied PDF's text was read with macOS PDFKit and passed to `extract_entries` to create the requested TXT. The Python CLI can be run after installing `requirements.txt`; it was not run end-to-end here.
