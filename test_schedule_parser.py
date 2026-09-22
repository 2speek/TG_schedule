from pathlib import Path
import sys

from parsers.pdf_parser import extract_pdf_text
from parsers.schedule_parser import (
    parse_schedule_days,
    parse_day_events,
    parse_event,
)


if len(sys.argv) > 1:
    pdf_path = Path(sys.argv[1])

    txt = extract_pdf_text(pdf_path)
    parsed = parse_schedule_days(txt)

    for day, lines in parsed.items():
        print(f"{day}:")

        events = parse_day_events(lines)

        for event_line in events:
            event = parse_event(event_line)
            print(f"\t{event}")

        print()

else:
    print("Использование:")
    print("python test_schedule_parser.py <путь_к_pdf>")