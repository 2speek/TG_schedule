from pathlib import Path


def detect_file_type(
    file_path: Path,
) -> str:

    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        return "pdf"

    if suffix == ".docx":
        return "docx"

    if suffix == ".doc":
        return "doc"

    if suffix == ".xlsx":
        return "xlsx"

    if suffix == ".txt":
        return "txt"

    return "unknown"