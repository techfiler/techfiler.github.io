"""Parse the Markdown source into structured question records."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


MODULE_RE = re.compile(r"^# Module \d+: (.+)$", re.M)
QUESTION_RE = re.compile(r"^### ([A-Z0-9]+) — (.+)$", re.M)
FIELD_RE = re.compile(
    r"^\*\*(Straight answer|Easy explanation|Production example / senior context|"
    r"Useful command or example|Common mistake|What makes this a strong interview answer)\*\*\s*$",
    re.M,
)
META_RE = {
    "level": re.compile(r"^- \*\*Level:\*\* (.+)$", re.M),
    "qtype": re.compile(r"^- \*\*Type:\*\* (.+)$", re.M),
    "topic": re.compile(r"^- \*\*Topic:\*\* (.+)$", re.M),
}
FOLLOWUP_RE = re.compile(r"^\*\*Likely follow-up:\*\*\s*(.+)$", re.M)
REFERENCE_RE = re.compile(r"^\*\*Official reference:\*\*\s*(.+)$", re.M)
CODE_FENCE_RE = re.compile(r"```(?:\w+)?\n(.*?)```", re.S)


@dataclass
class RawQuestion:
    qid: str
    question: str
    level: str
    qtype: str
    topic: str
    answer: str
    easy: str
    production: str
    command: str
    mistake: str
    strong: str
    followup: str
    reference: str
    module: str = ""


@dataclass
class RawModule:
    title: str
    intro_raw: str
    questions: List[RawQuestion] = field(default_factory=list)


def _section(text: str, name: str) -> str:
    matches = list(FIELD_RE.finditer(text))
    for i, match in enumerate(matches):
        if match.group(1) != name:
            continue
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end]
        # Cut trailing meta lines that belong after the field block.
        body = FOLLOWUP_RE.split(body)[0]
        body = REFERENCE_RE.split(body)[0]
        body = re.split(r"\n---\s*\n", body)[0]
        return body.strip()
    return ""


def _command(text: str) -> str:
    raw = _section(text, "Useful command or example")
    fences = CODE_FENCE_RE.findall(raw)
    if fences:
        return "\n".join(f.strip() for f in fences if f.strip())
    return raw.strip()


def _meta(block: str, key: str, default: str = "") -> str:
    match = META_RE[key].search(block)
    return match.group(1).strip() if match else default


def parse_markdown(text: str) -> List[RawModule]:
    modules: List[RawModule] = []
    module_matches = list(MODULE_RE.finditer(text))
    for i, match in enumerate(module_matches):
        title = match.group(1).strip()
        start = match.end()
        end = module_matches[i + 1].start() if i + 1 < len(module_matches) else len(text)
        body = text[start:end]
        first_q = QUESTION_RE.search(body)
        intro_raw = body[: first_q.start()].strip() if first_q else body.strip()
        module = RawModule(title=title, intro_raw=intro_raw)

        q_matches = list(QUESTION_RE.finditer(body))
        for j, qmatch in enumerate(q_matches):
            q_start = qmatch.end()
            q_end = q_matches[j + 1].start() if j + 1 < len(q_matches) else len(body)
            qblock = body[q_start:q_end]
            follow = FOLLOWUP_RE.search(qblock)
            ref = REFERENCE_RE.search(qblock)
            module.questions.append(
                RawQuestion(
                    qid=qmatch.group(1).strip(),
                    question=qmatch.group(2).strip(),
                    level=_meta(qblock, "level", "Beginner"),
                    qtype=_meta(qblock, "qtype", "Concept"),
                    topic=_meta(qblock, "topic", qmatch.group(2).strip()),
                    answer=_section(qblock, "Straight answer"),
                    easy=_section(qblock, "Easy explanation"),
                    production=_section(qblock, "Production example / senior context"),
                    command=_command(qblock),
                    mistake=_section(qblock, "Common mistake"),
                    strong=_section(qblock, "What makes this a strong interview answer"),
                    followup=follow.group(1).strip() if follow else "How would you prove that in production?",
                    reference=ref.group(1).strip() if ref else "",
                    module=title,
                )
            )
        modules.append(module)
    return modules
