#!/usr/bin/env python3
"""Build the interview book as PDF and DOCX.

    python3 build.py [--outdir dist]
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bookgen.docx_builder import DocxBuilder  # noqa: E402
from bookgen.pdf_builder import PdfBuilder  # noqa: E402
from content import build_book  # noqa: E402

BASENAME = "OpenShift_Platform_Engineer_Interview_Book_V5_250QA"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outdir", default=os.path.join(os.path.dirname(
        os.path.abspath(__file__)), "output"))
    args = parser.parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    book = build_book()
    print(f"parts: {len(book.parts)}   questions: {book.total}")
    if book.total != 250:
        print(f"ERROR: expected 250 questions, found {book.total}", file=sys.stderr)
        return 1

    pdf_path = os.path.join(args.outdir, f"{BASENAME}.pdf")
    docx_path = os.path.join(args.outdir, f"{BASENAME}.docx")

    PdfBuilder(book, pdf_path).build()
    print(f"wrote {pdf_path} ({os.path.getsize(pdf_path) / 1024:.0f} KB)")

    DocxBuilder(book, docx_path).build()
    print(f"wrote {docx_path} ({os.path.getsize(docx_path) / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
