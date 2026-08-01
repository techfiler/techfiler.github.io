"""Data model for the interview book.

A book is a list of parts; a part is a list of questions. Everything the
builders need is expressed here so the PDF and DOCX renderers stay dumb.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

FOUNDATION = "Foundation"
INTERMEDIATE = "Intermediate"
SENIOR = "Senior"
ARCHITECT = "Architect"

LEVEL_ORDER = {FOUNDATION: 0, INTERMEDIATE: 1, SENIOR: 2, ARCHITECT: 3}


@dataclass
class Question:
    q: str
    level: str
    answer: str
    analogy: str
    context: str
    steps: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
    redflag: str = ""
    followup: str = ""
    number: int = 0

    def validate(self, where: str) -> None:
        if self.level not in LEVEL_ORDER:
            raise ValueError(f"{where}: unknown level {self.level!r}")
        for name in ("q", "answer", "analogy", "context", "redflag", "followup"):
            if not getattr(self, name).strip():
                raise ValueError(f"{where}: empty field {name!r} in {self.q!r}")
        if len(self.steps) < 3:
            raise ValueError(f"{where}: fewer than 3 steps in {self.q!r}")
        if not self.evidence:
            raise ValueError(f"{where}: no evidence commands in {self.q!r}")


@dataclass
class Part:
    number: int
    title: str
    subtitle: str
    intro: str
    infographic: Optional[str]
    questions: List[Question]

    @property
    def first(self) -> int:
        return self.questions[0].number

    @property
    def last(self) -> int:
        return self.questions[-1].number

    @property
    def span(self) -> str:
        return f"Q{self.first}-Q{self.last}"


@dataclass
class Book:
    title: str
    subtitle: str
    edition: str
    stack: str
    parts: List[Part]

    def number_questions(self) -> None:
        n = 0
        for part in self.parts:
            part.questions.sort(key=lambda x: LEVEL_ORDER[x.level])
            for q in part.questions:
                n += 1
                q.number = n

    def validate(self) -> None:
        seen = set()
        for part in self.parts:
            for q in part.questions:
                q.validate(f"Part {part.number}")
                key = q.q.strip().lower()
                if key in seen:
                    raise ValueError(f"duplicate question: {q.q}")
                seen.add(key)

    @property
    def total(self) -> int:
        return sum(len(p.questions) for p in self.parts)
