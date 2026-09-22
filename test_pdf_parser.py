from pathlib import Path
import sys

from parsers.pdf_parser import extract_pdf_text
if len(sys.argv) > 1:
    txt = extract_pdf_text(Path(sys.argv[1]))
    print(txt)
else:
    print("Использование:")
    print(f"python test_pdf_parser.py <путь_к_pdf>")