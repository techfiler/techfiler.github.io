"""Assemble the Cloud Platform & DevOps interview book from Markdown."""

from __future__ import annotations

import os

from bookgen.enrich import enrich_module
from bookgen.model import Book, Part
from bookgen.module_meta import meta_for
from bookgen.parse import parse_markdown

SOURCE = os.path.join(os.path.dirname(__file__), "source.md")


def build_book(source_path: str | None = None) -> Book:
    path = source_path or SOURCE
    with open(path, encoding="utf-8") as fh:
        modules = parse_markdown(fh.read())

    parts: list[Part] = []
    for index, module in enumerate(modules, start=1):
        info = meta_for(module.title)
        questions = enrich_module(module)
        parts.append(
            Part(
                number=index,
                title=info["title"],
                subtitle=info["subtitle"],
                intro=info["intro"],
                infographics=list(info["infographics"]),
                questions=questions,
            )
        )

    book = Book(
        title="Cloud Platform & DevOps Interview Book",
        subtitle="400 questions with spoken answers, analogies, production context, "
                 "mindmaps and highlighted quick-revision cues",
        edition="Edition 2026.08 - enriched from the 400 Q&A source",
        stack="Linux  ·  Networking  ·  Docker  ·  Kubernetes  ·  AWS  ·  Terraform  ·  "
              "Python  ·  Airflow  ·  CI/CD  ·  Observability  ·  DevSecOps  ·  Production",
        parts=parts,
    )
    book.number_questions()
    book.validate()
    return book
