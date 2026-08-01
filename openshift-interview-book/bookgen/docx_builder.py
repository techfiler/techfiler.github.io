"""Renders the Book model into an editable .docx.

Infographics are the same reportlab drawings used by the PDF: each one is
written to a one-page PDF and rasterised with PyMuPDF, so both formats stay in
sync automatically.
"""

from __future__ import annotations

import os
import tempfile
from typing import List, Optional

import fitz
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_COLOR_INDEX
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import Inches, Pt, RGBColor
from reportlab.graphics import renderPDF

from . import highlight as hl
from . import infographics, theme
from .model import Book, Part, Question

INK = RGBColor(0x12, 0x23, 0x2E)
INK_SOFT = RGBColor(0x3B, 0x4A, 0x54)
MUTED = RGBColor(0x6B, 0x7A, 0x85)
RED = RGBColor(0xC0, 0x39, 0x2B)
TEAL = RGBColor(0x0E, 0x7C, 0x6B)
PURPLE = RGBColor(0x5B, 0x3E, 0x8E)
SLATE = RGBColor(0x44, 0x57, 0x6B)
AMBER = RGBColor(0xB7, 0x79, 0x1F)


def _shade(paragraph, hex_fill: str) -> None:
    pPr = paragraph._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_fill)
    pPr.append(shd)


def _left_bar(paragraph, hex_color: str, size: int = 18) -> None:
    pPr = paragraph._p.get_or_add_pPr()
    borders = OxmlElement("w:pBdr")
    left = OxmlElement("w:left")
    left.set(qn("w:val"), "single")
    left.set(qn("w:sz"), str(size))
    left.set(qn("w:space"), "6")
    left.set(qn("w:color"), hex_color)
    borders.append(left)
    pPr.append(borders)


def _spacing(paragraph, before: int = 0, after: int = 4, indent: float = 0.0) -> None:
    pf = paragraph.paragraph_format
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    if indent:
        pf.left_indent = Inches(indent)


class DocxBuilder:
    def __init__(self, book: Book, path: str, highlight: bool = False):
        self.book = book
        self.path = path
        self.highlight = highlight
        self.doc = Document()
        self._tmpdir = tempfile.mkdtemp(prefix="bookgen-img-")
        self._setup_styles()

    def _numbered(self, index: int, text: str) -> None:
        """A manually numbered step.

        Word's List Number style shares one numbering sequence across the whole
        document, so every question's steps would continue from the last one.
        Writing the number as text keeps each list starting at 1.
        """
        p = self.doc.add_paragraph()
        marker = p.add_run(f"{index}.  ")
        marker.bold = True
        marker.font.size = Pt(10)
        marker.font.color.rgb = SLATE
        run = p.add_run(text)
        run.font.size = Pt(10)
        _spacing(p, after=2, indent=0.32)
        p.paragraph_format.first_line_indent = Inches(-0.17)

    @property
    def edition_label(self) -> str:
        if self.highlight:
            return f"{self.book.edition}  -  quick-learning highlighted copy"
        return self.book.edition

    def _write(self, paragraph, text: str, size: float, color: RGBColor,
               bold: bool = False, italic: bool = False, font: Optional[str] = None,
               lead: bool = False, limit: int = 0) -> None:
        """Add text to a paragraph, splitting into runs so key spans can be highlighted."""
        spans = hl.pick(text, lead, limit) if (self.highlight and limit) else []
        pieces = []
        cursor = 0
        for start, end in spans:
            if start > cursor:
                pieces.append((text[cursor:start], False))
            pieces.append((text[start:end], True))
            cursor = end
        if cursor < len(text):
            pieces.append((text[cursor:], False))

        for chunk, marked in pieces:
            run = paragraph.add_run(chunk)
            run.font.size = Pt(size)
            run.font.color.rgb = color
            run.bold = bold
            run.italic = italic
            if font:
                run.font.name = font
                run._element.rPr.rFonts.set(qn("w:ascii"), font)
                run._element.rPr.rFonts.set(qn("w:hAnsi"), font)
            if marked:
                run.font.highlight_color = WD_COLOR_INDEX.YELLOW

    # ---------------------------------------------------------------- styles
    def _setup_styles(self) -> None:
        section = self.doc.sections[0]
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.75)
        section.left_margin = Inches(0.85)
        section.right_margin = Inches(0.85)

        normal = self.doc.styles["Normal"]
        normal.font.name = "Calibri"
        normal.font.size = Pt(10.5)
        normal.font.color.rgb = INK_SOFT
        normal.paragraph_format.space_after = Pt(5)
        normal.paragraph_format.line_spacing = 1.13
        rpr = normal.element.get_or_add_rPr()
        rfonts = rpr.get_or_add_rFonts()
        rfonts.set(qn("w:eastAsia"), "Calibri")

        for name, size, color, bold in [
            ("Heading 1", 20, INK, True),
            ("Heading 2", 14, INK, True),
            ("Heading 3", 11.5, INK, True),
        ]:
            style = self.doc.styles[name]
            style.font.name = "Calibri"
            style.font.size = Pt(size)
            style.font.color.rgb = color
            style.font.bold = bold
            style.paragraph_format.space_before = Pt(12)
            style.paragraph_format.space_after = Pt(5)

    # ------------------------------------------------------------- utilities
    def _para(self, text: str = "", size: float = 10.5, color: RGBColor = INK_SOFT,
              bold: bool = False, italic: bool = False, font: Optional[str] = None,
              align=None, lead: bool = False, limit: int = 0):
        p = self.doc.add_paragraph()
        self._write(p, text, size, color, bold, italic, font, lead, limit)
        if align is not None:
            p.alignment = align
        return p

    def _label(self, text: str, color: RGBColor):
        p = self._para(text.upper(), size=7.5, color=color, bold=True)
        _spacing(p, before=6, after=1)
        return p

    def _callout(self, text: str, fill: str, bar: str, color: RGBColor,
                 italic: bool = False, font: Optional[str] = None, size: float = 10.5,
                 lead: bool = False, limit: int = 0):
        p = self._para(text, size=size, color=color, italic=italic, font=font,
                       lead=lead, limit=limit)
        _shade(p, fill)
        _left_bar(p, bar)
        _spacing(p, before=2, after=6, indent=0.06)
        return p

    def _image(self, name: str) -> None:
        drawing = infographics.render(name)
        pdf_path = os.path.join(self._tmpdir, f"{name}.pdf")
        png_path = os.path.join(self._tmpdir, f"{name}.png")
        renderPDF.drawToFile(drawing, pdf_path, name)
        with fitz.open(pdf_path) as doc:
            doc[0].get_pixmap(dpi=220).save(png_path)
        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run().add_picture(png_path, width=Inches(6.5))
        _spacing(p, before=6, after=8)

    def _rule(self) -> None:
        p = self.doc.add_paragraph()
        pPr = p._p.get_or_add_pPr()
        borders = OxmlElement("w:pBdr")
        bottom = OxmlElement("w:bottom")
        bottom.set(qn("w:val"), "single")
        bottom.set(qn("w:sz"), "12")
        bottom.set(qn("w:space"), "1")
        bottom.set(qn("w:color"), "C0392B")
        borders.append(bottom)
        pPr.append(borders)
        _spacing(p, before=0, after=8)

    def _footer(self) -> None:
        for section in self.doc.sections:
            para = section.footer.paragraphs[0]
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            label = "  (highlighted copy)" if self.highlight else ""
            run = para.add_run(f"{self.book.title}{label}   -   ")
            run.font.size = Pt(7.5)
            run.font.color.rgb = MUTED
            fld = OxmlElement("w:fldSimple")
            fld.set(qn("w:instr"), "PAGE")
            para._p.append(fld)

    # ---------------------------------------------------------- book sections
    def _cover(self) -> None:
        for _ in range(3):
            self.doc.add_paragraph()
        p = self._para(self.book.title, size=26, color=INK, bold=True,
                       align=WD_ALIGN_PARAGRAPH.CENTER)
        _spacing(p, after=10)
        p = self._para(self.book.subtitle, size=13, color=SLATE,
                       align=WD_ALIGN_PARAGRAPH.CENTER)
        _spacing(p, after=10)
        self._rule()
        self._para(self.book.stack, size=9.5, color=MUTED, align=WD_ALIGN_PARAGRAPH.CENTER)
        self._para(self.edition_label, size=9.5, color=MUTED, align=WD_ALIGN_PARAGRAPH.CENTER)
        self.doc.add_paragraph()
        self._image("learning_route")
        self._para(
            "Every question carries a spoken answer, an analogy, production context, a step-by-step "
            "procedure, the evidence you would quote, the red flag that costs you the offer, and the "
            "follow-up question the interviewer is already holding.",
            size=9.5, color=MUTED, align=WD_ALIGN_PARAGRAPH.CENTER)

    def _contents(self) -> None:
        self.doc.add_page_break()
        self.doc.add_heading("Contents", level=1)
        self._rule()
        self._para(
            f"{self.book.total} questions across {len(self.book.parts)} parts. Parts are ordered so that "
            "nothing depends on a concept you have not met yet, and inside each part the questions climb "
            "from Foundation to Architect.")
        table = self.doc.add_table(rows=1, cols=3)
        table.style = "Light Grid Accent 1"
        hdr = table.rows[0].cells
        for cell, text in zip(hdr, ["Part", "Topic", "Questions"]):
            cell.text = ""
            run = cell.paragraphs[0].add_run(text)
            run.bold = True
            run.font.size = Pt(9.5)
        for part in self.book.parts:
            row = table.add_row().cells
            row[0].text = ""
            row[0].paragraphs[0].add_run(str(part.number)).font.size = Pt(9.5)
            row[1].text = ""
            run = row[1].paragraphs[0].add_run(part.title)
            run.bold = True
            run.font.size = Pt(9.5)
            sub = row[1].add_paragraph()
            sub_run = sub.add_run(part.subtitle)
            sub_run.font.size = Pt(8.5)
            sub_run.font.color.rgb = MUTED
            row[2].text = ""
            row[2].paragraphs[0].add_run(part.span).font.size = Pt(9.5)
        table.columns[0].width = Inches(0.5)
        table.columns[1].width = Inches(5.1)
        table.columns[2].width = Inches(0.9)

    def _how_to_use(self) -> None:
        self.doc.add_page_break()
        self.doc.add_heading("Read this page first", level=1)
        self._rule()
        self._para(
            "This book exists because most interview prep fails in the same way: you can recite the "
            "definition, the interviewer asks \"and how would you prove that?\", and the conversation stops. "
            "Definitions are table stakes. What gets scored is whether you can name the owning controller, "
            "quote the evidence, choose the smallest safe action, and say what you would change afterwards so "
            "it never happens again.")
        self._para(
            "So every one of the 250 questions here is answered in six layers. Read the first layer if you "
            "are short on time. Read all six if this is a topic you would rather not be surprised by.")
        if self.highlight:
            self._label("About the yellow highlighting", AMBER)
            p = self.doc.add_paragraph()
            self._write(p, "This is the quick-learning copy. In every question the opening claim of the "
                           "spoken answer and the closing consequence of the production context are ",
                        10.5, INK_SOFT)
            run = p.add_run("marked in yellow like this")
            run.font.size = Pt(10.5)
            run.font.color.rgb = INK_SOFT
            run.font.highlight_color = WD_COLOR_INDEX.YELLOW
            self._write(p, ". Read only the highlighted sentences for a fast revision pass through all 250 "
                           "questions, then come back to the full text for the topics where the highlight did "
                           "not feel like enough. A clean unhighlighted copy of the same book is published "
                           "alongside this one.", 10.5, INK_SOFT)
            _shade(p, "FBF3E2")
            _left_bar(p, "B7791F")
            _spacing(p, before=2, after=8, indent=0.06)
        self._image("six_layer_method")
        self.doc.add_heading("Levels, and why they are marked", level=2)
        self._para(
            "Each question is tagged Foundation, Intermediate, Senior or Architect. The tag is not about how "
            "hard the topic is - it is about how deep the expected answer goes. A Foundation question about "
            "etcd quorum and an Architect question about etcd quorum are the same subject scored on "
            "completely different scales.")
        self._image("answer_ladder")
        self.doc.add_page_break()
        self.doc.add_heading("Two frameworks that carry most of the interview", level=2)
        self._para(
            "Roughly a third of a senior platform interview is troubleshooting and another third is design. "
            "If you only memorise two things from this book, memorise these two loops. They give you a "
            "structure to speak into when a question catches you cold, which is worth more than any "
            "individual fact.")
        self._image("evidence_first_loop")
        self._para(
            "For design and architecture questions, swap the loop for: Requirement, Options, Trade-off, "
            "Decision, Risk, Verification. Say the requirement back before you propose anything - it is the "
            "single fastest way to sound like someone who has shipped a platform rather than read about one.")
        self._image("scoring_card")
        self.doc.add_page_break()
        self.doc.add_heading("A three-day, twenty-hour run", level=2)
        self._para(
            "If you have three days, do not read this book front to back at a constant speed. Spend day one "
            "on Parts 1 to 6 for breadth and to find your weak spots. Spend day two on Parts 7 to 13, which "
            "is where most senior interviews actually live: storage, security, lifecycle, observability, "
            "troubleshooting and recovery. Spend day three on Parts 14 to 17 plus spoken rehearsal - answer "
            "thirty questions out loud, timed, without notes.")
        self._para(
            "In the final hour, stop reading new material. Re-read only the red flags and the analogies. The "
            "red flags stop you from losing points you have already earned, and the analogies are what you "
            "will reach for when you are asked something you did not prepare.")
        self.doc.add_heading("Honest scope note", level=2)
        self._para(
            "The healthcare and enterprise examples in this book are illustrative. They are not descriptions "
            "of any specific customer environment or confidential architecture. Product behaviour is "
            "described against current OpenShift 4.x and ACM 2.x documentation; a real project may run an "
            "earlier supported or EUS release. In the interview, state the principle first, then ask which "
            "version and infrastructure provider the project runs on. That question reads as experience, not "
            "ignorance.")

    def _question(self, q: Question) -> None:
        fill, tint = theme.DOCX_LEVEL_COLORS[q.level]
        color = RGBColor.from_string(fill)

        head = self.doc.add_paragraph()
        badge = head.add_run(f" Q{q.number} ")
        badge.bold = True
        badge.font.size = Pt(9.5)
        badge.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        _shade(head, fill)
        lvl = head.add_run(f"   {q.level.upper()}")
        lvl.bold = True
        lvl.font.size = Pt(8)
        lvl.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        _spacing(head, before=10, after=2)

        title = self._para(q.q, size=12, color=INK, bold=True)
        _spacing(title, before=2, after=4)

        self._label("Say this", color)
        self._callout(q.answer, tint, fill, INK, lead=True, limit=2)

        self._label("Think of it like", TEAL)
        self._callout(q.analogy, "E6F4F1", "0E7C6B", TEAL, italic=True)

        self._label("Why it matters in production", MUTED)
        self._para(q.context, limit=1)

        self._label("Step by step", SLATE)
        for i, step in enumerate(q.steps, 1):
            self._numbered(i, step)

        self._label("Evidence you would quote", MUTED)
        for line in q.evidence:
            p = self._callout(line, "F3F6F8", "D6DEE3", INK, font="Consolas", size=9)
            _spacing(p, before=0, after=2, indent=0.06)

        self._label("Red flag - do not say this", RED)
        self._callout(q.redflag, "FBEDEB", "C0392B", RED)

        self._label("Expect this follow-up", PURPLE)
        self._callout(q.followup, "F0EBF8", "5B3E8E", PURPLE)

        self._rule()

    def _part(self, part: Part) -> None:
        self.doc.add_page_break()
        p = self._para(f"PART {part.number}  ·  {part.span}  ·  {len(part.questions)} QUESTIONS",
                       size=9.5, color=RED, bold=True)
        _spacing(p, before=0, after=2)
        self.doc.add_heading(part.title, level=1)
        self._para(part.subtitle, size=11, color=SLATE)
        self._rule()
        self._para(part.intro, limit=1)
        levels = {}
        for q in part.questions:
            levels[q.level] = levels.get(q.level, 0) + 1
        self._para("Level mix - " + "  |  ".join(f"{k}: {v}" for k, v in levels.items()),
                   size=8.5, color=MUTED)
        for name in part.infographics:
            self._image(name)
        for q in part.questions:
            self._question(q)

    def _closing(self) -> None:
        self.doc.add_page_break()
        self.doc.add_heading("The last hour", level=1)
        self._rule()
        self._para(
            "You will not learn anything new in the last hour, so use it to protect what you already know. "
            "Say these six sentences out loud until they sound unrehearsed:")
        for i, text in enumerate([
            "\"Let me start with impact and scope, then the evidence I would collect.\"",
            "\"The owning controller here is X, so that is where I would read conditions first.\"",
            "\"The smallest safe action is Y, because it limits blast radius to one pool.\"",
            "\"I would validate against the customer-visible symptom, not just resource status.\"",
            "\"The trade-off is A versus B; I would choose A because of this constraint.\"",
            "\"To prevent recurrence I would add this alert and this guardrail.\"",
        ], 1):
            self._numbered(i, text)
        self.doc.add_heading("Three habits that reliably lose offers", level=2)
        for text in [
            "Restarting things before reading anything. It sometimes works, and it always sounds junior.",
            "Answering a design question with a product name instead of a requirement and a trade-off.",
            "Claiming a backup, a policy or a failover works without ever having tested the restore.",
        ]:
            p = self.doc.add_paragraph(style="List Bullet")
            run = p.add_run(text)
            run.font.size = Pt(10)
            run.font.color.rgb = RED
            _spacing(p, after=2, indent=0.25)
        self.doc.add_heading("Where to check current behaviour", level=2)
        self._para(
            "Product behaviour moves. Before an interview, spot-check anything version-sensitive against the "
            "Red Hat OpenShift Container Platform documentation, the Red Hat Advanced Cluster Management "
            "documentation, the Red Hat Ansible Automation Platform documentation and the upstream Kubernetes "
            "concepts pages. If you are unsure in the room, say which release you are describing and offer to "
            "confirm - that is how senior engineers actually talk.")

    def build(self) -> None:
        self._cover()
        self._contents()
        self._how_to_use()
        for part in self.book.parts:
            self._part(part)
        self._closing()
        self._footer()
        self.doc.save(self.path)
