# Oxford Wordlist Extractor Design

## Intent

Create a small Python command-line program that extracts Oxford 5000 word entries and their part-of-speech labels from the supplied searchable PDF and saves them as UTF-8 text.

## Goals and constraints

- Preserve each entry's displayed spelling/parenthetical note and all displayed POS labels.
- Write one entry per line as `word<TAB>POS`.
- Default input is the supplied PDF beside the script; default output uses the same basename with a `.txt` extension. Allow input and output paths as command-line arguments.
- Use `pypdf`; do not require OCR or network access at runtime.
- Skip CEFR headings, document headers/footers, and page numbers.

## Non-goals

- Translate the words or expand POS abbreviations.
- Reformat the list by CEFR level or create CSV/Excel output.

## Approaches

- `pypdf` text extraction and line parsing: lightweight, appropriate for this PDF's selectable text, and recommended.
- PyMuPDF layout extraction: more control over positioning but a larger dependency; unnecessary for the observed regular one-entry-per-line layout.

## Implementation choice

Use `pypdf`, parse complete lines as entries only when they end in recognized Oxford POS labels, and save UTF-8 tab-separated lines. Report clear errors for missing files, unreadable PDFs, and no parsed entries.

## Output

Add a standalone script and generate the requested `.txt` beside the input PDF.
