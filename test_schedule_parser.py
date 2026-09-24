from pathlib import Path
import sys

from parsers.pdf_parser import (
    extract_pdf_text,
)

from parsers.schedule_parser import (
    parse_full_schedule,
)


if len(sys.argv) > 1:

    pdf_path = Path(
        sys.argv[1]
    )

    text = extract_pdf_text(
        pdf_path
    )

    schedule = parse_full_schedule(
        text
    )

    total = 0

    for day, events in schedule.items():

        print(
            f"{day}:"
        )

        for event in events:
            print(
                f"\t{event}"
            )

            total += 1

        print()

    print(
        f"Всего событий: {total}"
    )

else:
    print(
        "Использование:"
    )

    print(
        "python test_schedule_parser.py "
        "<путь_к_pdf>"
    )