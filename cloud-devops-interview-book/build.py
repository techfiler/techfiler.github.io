#!/usr/bin/env python3
"""Build the Cloud Platform & DevOps interview book as DOCX.

    python3 build.py [--outdir output] [--pdf]
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bookgen.docx_builder import DocxBuilder  # noqa: E402
from content import build_book  # noqa: E402

BASENAME = "Cloud_Platform_DevOps_Interview_Book_400QA"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--outdir",
        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "output"),
    )
    parser.add_argument(
        "--source",
        default=None,
        help="Optional path to the Markdown source (defaults to content/source.md)",
    )
    args = parser.parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    book = build_book(args.source)
    print(f"parts: {len(book.parts)}   questions: {book.total}")
    if book.total != 400:
        print(f"ERROR: expected 400 questions, found {book.total}", file=sys.stderr)
        return 1

    editions = [
        (BASENAME, False),
        (f"{BASENAME}_Highlighted", True),
    ]
    for name, highlight in editions:
        docx_path = os.path.join(args.outdir, f"{name}.docx")
        DocxBuilder(book, docx_path, highlight=highlight).build()
        print(f"wrote {docx_path} ({os.path.getsize(docx_path) / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
