from pathlib import Path

import pymupdf


def extract_pdf_text(file_path: Path) -> str:
    with pymupdf.open(file_path) as pdf:
        texts = []

        for page in pdf.pages():
            texts.append(
                page.get_text(sort=True)
            )

    return "\f".join(texts)