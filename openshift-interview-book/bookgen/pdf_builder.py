"""Renders the Book model into a print-ready PDF."""

from __future__ import annotations

from typing import List

from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (BaseDocTemplate, CondPageBreak, Flowable, Frame,
                                KeepTogether, ListFlowable, ListItem, NextPageTemplate,
                                PageBreak, PageTemplate, Paragraph, Spacer, Table,
                                TableStyle)

from . import infographics, theme
from .model import Book, Part, Question

MARGIN_X = 21 * mm
MARGIN_TOP = 20 * mm
MARGIN_BOTTOM = 18 * mm


def _styles() -> dict:
    base = ParagraphStyle(
        "body", fontName=theme.BODY_FONT, fontSize=9.4, leading=13.4,
        textColor=theme.INK_SOFT, spaceAfter=0, alignment=TA_LEFT,
    )
    return {
        "body": base,
        "cover_title": ParagraphStyle("cover_title", parent=base, fontName=theme.BODY_BOLD,
                                      fontSize=27, leading=32, textColor=theme.INK,
                                      alignment=TA_CENTER),
        "cover_sub": ParagraphStyle("cover_sub", parent=base, fontSize=12.5, leading=18,
                                    textColor=theme.SLATE, alignment=TA_CENTER),
        "cover_meta": ParagraphStyle("cover_meta", parent=base, fontSize=9.2, leading=14,
                                     textColor=theme.MUTED, alignment=TA_CENTER),
        "h1": ParagraphStyle("h1", parent=base, fontName=theme.BODY_BOLD, fontSize=19,
                             leading=23, textColor=theme.INK, spaceAfter=4),
        "h2": ParagraphStyle("h2", parent=base, fontName=theme.BODY_BOLD, fontSize=12.5,
                             leading=16, textColor=theme.INK, spaceBefore=10, spaceAfter=4),
        "part_kicker": ParagraphStyle("part_kicker", parent=base, fontName=theme.BODY_BOLD,
                                      fontSize=9.6, leading=12, textColor=theme.RED,
                                      spaceAfter=3),
        "part_sub": ParagraphStyle("part_sub", parent=base, fontSize=10.6, leading=15,
                                   textColor=theme.SLATE, spaceAfter=8),
        "question": ParagraphStyle("question", parent=base, fontName=theme.BODY_BOLD,
                                   fontSize=11.4, leading=14.6, textColor=theme.INK),
        "label": ParagraphStyle("label", parent=base, fontName=theme.BODY_BOLD, fontSize=7.0,
                                leading=9, textColor=theme.MUTED),
        "answer": ParagraphStyle("answer", parent=base, fontSize=9.8, leading=14.2,
                                 textColor=theme.INK),
        "analogy": ParagraphStyle("analogy", parent=base, fontName=theme.BODY_ITALIC,
                                  fontSize=9.3, leading=13.2, textColor=theme.TEAL),
        "step": ParagraphStyle("step", parent=base, fontSize=9.1, leading=12.8),
        "mono": ParagraphStyle("mono", parent=base, fontName=theme.MONO_FONT, fontSize=8.0,
                               leading=11.2, textColor=theme.INK),
        "redflag": ParagraphStyle("redflag", parent=base, fontSize=9.1, leading=12.8,
                                  textColor=theme.RED),
        "followup": ParagraphStyle("followup", parent=base, fontSize=9.1, leading=12.8,
                                   textColor=theme.PURPLE),
        "toc": ParagraphStyle("toc", parent=base, fontSize=9.6, leading=15),
        "caption": ParagraphStyle("caption", parent=base, fontSize=8.2, leading=11.4,
                                  textColor=theme.MUTED),
    }


S = _styles()


class Rule(Flowable):
    def __init__(self, width, color=theme.RULE, thickness=0.7, space=0.0):
        super().__init__()
        self.width = width
        self.color = color
        self.thickness = thickness
        self.height = thickness + space

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, self.height - self.thickness, self.width, self.height - self.thickness)


class Badge(Flowable):
    """Question number plus level chip, drawn as one line."""

    def __init__(self, number: int, level: str, width: float):
        super().__init__()
        self.number = number
        self.level = level
        self.width = width
        self.height = 15.0

    def draw(self):
        color, tint = theme.LEVEL_COLORS[self.level]
        c = self.canv
        num = f"Q{self.number}"
        num_w = c.stringWidth(num, theme.BODY_BOLD, 9.0) + 14
        c.setFillColor(color)
        c.roundRect(0, 1, num_w, 13, 3, stroke=0, fill=1)
        c.setFillColor(theme.PAPER)
        c.setFont(theme.BODY_BOLD, 9.0)
        c.drawString(7, 5, num)

        lvl_w = c.stringWidth(self.level.upper(), theme.BODY_BOLD, 7.2) + 14
        c.setFillColor(tint)
        c.setStrokeColor(color)
        c.setLineWidth(0.7)
        c.roundRect(num_w + 5, 1, lvl_w, 13, 3, stroke=1, fill=1)
        c.setFillColor(color)
        c.setFont(theme.BODY_BOLD, 7.2)
        c.drawString(num_w + 12, 5.2, self.level.upper())

        c.setStrokeColor(theme.RULE)
        c.setLineWidth(0.6)
        c.line(num_w + lvl_w + 14, 7.5, self.width, 7.5)


def _label(text: str, color) -> Paragraph:
    style = ParagraphStyle(f"label_{text}", parent=S["label"], textColor=color)
    return Paragraph(text.upper(), style)


def _panel(rows: List[List], width: float, bg, border, pad_left=8) -> Table:
    t = Table(rows, colWidths=[width])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("BOX", (0, 0), (-1, -1), 0.7, border),
        ("LEFTPADDING", (0, 0), (-1, -1), pad_left),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def _accent_panel(rows: List[List], width: float, bg, accent) -> Table:
    t = Table(rows, colWidths=[width])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("LINEBEFORE", (0, 0), (0, -1), 2.4, accent),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t


class PdfBuilder:
    def __init__(self, book: Book, path: str):
        self.book = book
        self.path = path
        self.width = A4[0] - 2 * MARGIN_X
        self._outline: List[tuple] = []

    # ---------------------------------------------------------------- chrome
    def _page_chrome(self, canvas, doc):
        canvas.saveState()
        page = canvas.getPageNumber()
        if page > 1:
            canvas.setFont(theme.BODY_FONT, 7.4)
            canvas.setFillColor(theme.MUTED)
            canvas.drawString(MARGIN_X, A4[1] - MARGIN_TOP + 8, self.book.title)
            canvas.drawRightString(A4[0] - MARGIN_X, A4[1] - MARGIN_TOP + 8, self.book.stack)
            canvas.setStrokeColor(theme.RULE)
            canvas.setLineWidth(0.5)
            canvas.line(MARGIN_X, A4[1] - MARGIN_TOP + 4, A4[0] - MARGIN_X, A4[1] - MARGIN_TOP + 4)
            canvas.line(MARGIN_X, MARGIN_BOTTOM - 8, A4[0] - MARGIN_X, MARGIN_BOTTOM - 8)
            canvas.drawString(MARGIN_X, MARGIN_BOTTOM - 18, self.book.edition)
            canvas.setFont(theme.BODY_BOLD, 8.0)
            canvas.setFillColor(theme.INK)
            canvas.drawRightString(A4[0] - MARGIN_X, MARGIN_BOTTOM - 18, str(page))
        canvas.restoreState()

    def _cover_chrome(self, canvas, doc):
        canvas.saveState()
        canvas.setFillColor(theme.INK)
        canvas.rect(0, A4[1] - 14 * mm, A4[0], 14 * mm, stroke=0, fill=1)
        canvas.setFillColor(theme.RED)
        canvas.rect(0, A4[1] - 17 * mm, A4[0], 3 * mm, stroke=0, fill=1)
        canvas.setFillColor(theme.INK)
        canvas.rect(0, 0, A4[0], 10 * mm, stroke=0, fill=1)
        canvas.restoreState()

    # ------------------------------------------------------------ components
    def _graphic(self, name: str) -> List[Flowable]:
        drawing = infographics.render(name)
        return [Spacer(1, 6), drawing, Spacer(1, 8)]

    def _question(self, q: Question) -> List[Flowable]:
        color, tint = theme.LEVEL_COLORS[q.level]
        head = KeepTogether([
            Badge(q.number, q.level, self.width),
            Spacer(1, 4),
            Paragraph(q.q, S["question"]),
            Spacer(1, 6),
            _accent_panel([[Paragraph("SAY THIS", ParagraphStyle(
                "l", parent=S["label"], textColor=color))],
                [Paragraph(q.answer, S["answer"])]], self.width, tint, color),
        ])

        steps = ListFlowable(
            [ListItem(Paragraph(s, S["step"]), leftIndent=14, value=i + 1)
             for i, s in enumerate(q.steps)],
            bulletType="1", bulletFontName=theme.BODY_BOLD, bulletFontSize=8.6,
            bulletColor=theme.SLATE, leftIndent=15, bulletDedent=13, spaceBefore=1,
        )

        evidence_rows = [[Paragraph("EVIDENCE YOU WOULD QUOTE", S["label"])]]
        for line in q.evidence:
            evidence_rows.append([Paragraph(line.replace("&", "&amp;").replace("<", "&lt;"), S["mono"])])

        return [
            head,
            Spacer(1, 7),
            KeepTogether([
                _label("THINK OF IT LIKE", theme.TEAL),
                Spacer(1, 2),
                Paragraph(q.analogy, S["analogy"]),
            ]),
            Spacer(1, 7),
            _label("WHY IT MATTERS IN PRODUCTION", theme.MUTED),
            Spacer(1, 2),
            Paragraph(q.context, S["body"]),
            Spacer(1, 7),
            _label("STEP BY STEP", theme.SLATE),
            Spacer(1, 2),
            steps,
            Spacer(1, 7),
            _panel(evidence_rows, self.width, theme.CODE_BG, theme.RULE),
            Spacer(1, 7),
            KeepTogether([
                _accent_panel([[Paragraph("RED FLAG - DO NOT SAY THIS", ParagraphStyle(
                    "rf", parent=S["label"], textColor=theme.RED))],
                    [Paragraph(q.redflag, S["redflag"])]], self.width, theme.RED_TINT, theme.RED),
                Spacer(1, 5),
                _accent_panel([[Paragraph("EXPECT THIS FOLLOW-UP", ParagraphStyle(
                    "fu", parent=S["label"], textColor=theme.PURPLE))],
                    [Paragraph(q.followup, S["followup"])]], self.width, theme.PURPLE_TINT,
                    theme.PURPLE),
            ]),
            Spacer(1, 10),
            Rule(self.width, theme.RULE, 0.6, 6),
            Spacer(1, 10),
        ]

    def _part(self, part: Part) -> List[Flowable]:
        levels = {}
        for q in part.questions:
            levels[q.level] = levels.get(q.level, 0) + 1
        mix = "  ·  ".join(f"{k}: {v}" for k, v in levels.items())
        story: List[Flowable] = [
            PageBreak(),
            Paragraph(f"PART {part.number}  ·  {part.span}  ·  {len(part.questions)} QUESTIONS",
                      S["part_kicker"]),
            Paragraph(part.title, S["h1"]),
            Paragraph(part.subtitle, S["part_sub"]),
            Rule(self.width, theme.RED, 1.6, 8),
            Spacer(1, 4),
            Paragraph(part.intro, S["body"]),
            Spacer(1, 4),
            Paragraph(f"Level mix - {mix}", S["caption"]),
        ]
        for name in part.infographics:
            story += self._graphic(name)
        story.append(Spacer(1, 6))
        for q in part.questions:
            story += self._question(q)
        return story

    # ------------------------------------------------------------ front matter
    def _cover(self) -> List[Flowable]:
        return [
            Spacer(1, 34 * mm),
            Paragraph(self.book.title, S["cover_title"]),
            Spacer(1, 6 * mm),
            Paragraph(self.book.subtitle, S["cover_sub"]),
            Spacer(1, 8 * mm),
            Rule(self.width, theme.RED, 1.6, 4),
            Spacer(1, 6 * mm),
            Paragraph(self.book.stack, S["cover_meta"]),
            Spacer(1, 3 * mm),
            Paragraph(self.book.edition, S["cover_meta"]),
            Spacer(1, 12 * mm),
            infographics.render("learning_route"),
            Spacer(1, 8 * mm),
            Paragraph(
                "Every question carries a spoken answer, an analogy, production context, a step-by-step "
                "procedure, the evidence you would quote, the red flag that costs you the offer, and the "
                "follow-up question the interviewer is already holding.",
                S["cover_meta"]),
        ]

    def _how_to_use(self) -> List[Flowable]:
        story: List[Flowable] = [
            PageBreak(),
            Paragraph("Read this page first", S["h1"]),
            Rule(self.width, theme.RED, 1.6, 8),
            Spacer(1, 4),
            Paragraph(
                "This book exists because most interview prep fails in the same way: you can recite the "
                "definition, the interviewer asks \"and how would you prove that?\", and the conversation "
                "stops. Definitions are table stakes. What gets scored is whether you can name the owning "
                "controller, quote the evidence, choose the smallest safe action, and say what you would "
                "change afterwards so it never happens again.",
                S["body"]),
            Spacer(1, 6),
            Paragraph(
                "So every one of the 250 questions here is answered in six layers. Read the first layer if "
                "you are short on time. Read all six if this is a topic you would rather not be surprised by.",
                S["body"]),
        ]
        story += self._graphic("six_layer_method")
        story += [
            Paragraph("Levels, and why they are marked", S["h2"]),
            Paragraph(
                "Each question is tagged Foundation, Intermediate, Senior or Architect. The tag is not about "
                "how hard the topic is - it is about how deep the expected answer goes. A Foundation question "
                "about etcd quorum and an Architect question about etcd quorum are the same subject scored on "
                "completely different scales.",
                S["body"]),
        ]
        story += self._graphic("answer_ladder")
        story += [
            PageBreak(),
            Paragraph("Two frameworks that carry most of the interview", S["h2"]),
            Paragraph(
                "Roughly a third of a senior platform interview is troubleshooting and another third is design. "
                "If you only memorise two things from this book, memorise these two loops. They give you a "
                "structure to speak into when a question catches you cold, which is worth more than any "
                "individual fact.",
                S["body"]),
        ]
        story += self._graphic("evidence_first_loop")
        story += [
            Paragraph(
                "For design and architecture questions, swap the loop for: Requirement, Options, Trade-off, "
                "Decision, Risk, Verification. Say the requirement back before you propose anything - it is "
                "the single fastest way to sound like someone who has shipped a platform rather than read "
                "about one.",
                S["body"]),
        ]
        story += self._graphic("scoring_card")
        story += [
            PageBreak(),
            Paragraph("A three-day, twenty-hour run", S["h2"]),
            Paragraph(
                "If you have three days, do not read this book front to back at a constant speed. Spend day "
                "one on Parts 1 to 6 for breadth and to find your weak spots. Spend day two on Parts 7 to 13, "
                "which is where most senior interviews actually live: storage, security, lifecycle, "
                "observability, troubleshooting and recovery. Spend day three on Parts 14 to 17 plus spoken "
                "rehearsal - answer thirty questions out loud, timed, without notes.",
                S["body"]),
            Spacer(1, 6),
            Paragraph(
                "In the final hour, stop reading new material. Re-read only the red flags and the analogies. "
                "The red flags stop you from losing points you have already earned, and the analogies are what "
                "you will reach for when you are asked something you did not prepare.",
                S["body"]),
            Spacer(1, 8),
            Paragraph("Honest scope note", S["h2"]),
            Paragraph(
                "The healthcare and enterprise examples in this book are illustrative. They are not "
                "descriptions of any specific customer environment or confidential architecture. Product "
                "behaviour is described against current OpenShift 4.x and ACM 2.x documentation; a real "
                "project may run an earlier supported or EUS release. In the interview, state the principle "
                "first, then ask which version and infrastructure provider the project runs on. That question "
                "reads as experience, not ignorance.",
                S["body"]),
        ]
        return story

    def _contents(self) -> List[Flowable]:
        rows = [[Paragraph("<b>Part</b>", S["toc"]), Paragraph("<b>Topic</b>", S["toc"]),
                 Paragraph("<b>Questions</b>", S["toc"])]]
        for part in self.book.parts:
            rows.append([
                Paragraph(str(part.number), S["toc"]),
                Paragraph(f"<b>{part.title}</b><br/><font size=8 color='#6B7A85'>{part.subtitle}</font>",
                          S["toc"]),
                Paragraph(part.span, S["toc"]),
            ])
        table = Table(rows, colWidths=[34, self.width - 34 - 74, 74], repeatRows=1)
        table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LINEBELOW", (0, 0), (-1, 0), 1.0, theme.INK),
            ("LINEBELOW", (0, 1), (-1, -2), 0.4, theme.RULE),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [theme.PAPER, theme.SLATE_TINT]),
        ]))
        return [
            PageBreak(),
            Paragraph("Contents", S["h1"]),
            Rule(self.width, theme.RED, 1.6, 8),
            Spacer(1, 6),
            Paragraph(
                f"{self.book.total} questions across {len(self.book.parts)} parts. Parts are ordered so that "
                "nothing depends on a concept you have not met yet, and inside each part the questions climb "
                "from Foundation to Architect.",
                S["body"]),
            Spacer(1, 8),
            table,
        ]

    def _closing(self) -> List[Flowable]:
        return [
            PageBreak(),
            Paragraph("The last hour", S["h1"]),
            Rule(self.width, theme.RED, 1.6, 8),
            Spacer(1, 4),
            Paragraph(
                "You will not learn anything new in the last hour, so use it to protect what you already know. "
                "Say these six sentences out loud until they sound unrehearsed:",
                S["body"]),
            Spacer(1, 6),
            ListFlowable([
                ListItem(Paragraph(t, S["step"]), leftIndent=14, value=i + 1)
                for i, t in enumerate([
                    "\"Let me start with impact and scope, then the evidence I would collect.\"",
                    "\"The owning controller here is X, so that is where I would read conditions first.\"",
                    "\"The smallest safe action is Y, because it limits blast radius to one pool.\"",
                    "\"I would validate against the customer-visible symptom, not just resource status.\"",
                    "\"The trade-off is A versus B; I would choose A because of this constraint.\"",
                    "\"To prevent recurrence I would add this alert and this guardrail.\"",
                ])
            ], bulletType="1", bulletFontName=theme.BODY_BOLD, bulletFontSize=8.6,
                bulletColor=theme.SLATE, leftIndent=15, bulletDedent=13),
            Spacer(1, 10),
            Paragraph("Three habits that reliably lose offers", S["h2"]),
            ListFlowable([
                ListItem(Paragraph(t, S["step"]), leftIndent=14)
                for t in [
                    "Restarting things before reading anything. It sometimes works, and it always sounds junior.",
                    "Answering a design question with a product name instead of a requirement and a trade-off.",
                    "Claiming a backup, a policy or a failover works without ever having tested the restore.",
                ]
            ], bulletType="bullet", bulletFontSize=7, bulletColor=theme.RED, leftIndent=15,
                bulletDedent=10),
            Spacer(1, 10),
            Paragraph("Where to check current behaviour", S["h2"]),
            Paragraph(
                "Product behaviour moves. Before an interview, spot-check anything version-sensitive against "
                "the Red Hat OpenShift Container Platform documentation, the Red Hat Advanced Cluster "
                "Management documentation, the Red Hat Ansible Automation Platform documentation and the "
                "upstream Kubernetes concepts pages. If you are unsure in the room, say which release you are "
                "describing and offer to confirm - that is how senior engineers actually talk.",
                S["body"]),
        ]

    # ------------------------------------------------------------------ build
    def build(self) -> None:
        doc = BaseDocTemplate(
            self.path, pagesize=A4,
            leftMargin=MARGIN_X, rightMargin=MARGIN_X,
            topMargin=MARGIN_TOP, bottomMargin=MARGIN_BOTTOM,
            title=self.book.title, author="Interview preparation edition",
            subject=self.book.subtitle,
        )
        frame = Frame(MARGIN_X, MARGIN_BOTTOM, self.width,
                      A4[1] - MARGIN_TOP - MARGIN_BOTTOM, id="main",
                      leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        doc.addPageTemplates([
            PageTemplate(id="cover", frames=[frame], onPage=self._cover_chrome),
            PageTemplate(id="body", frames=[frame], onPage=self._page_chrome),
        ])

        story: List[Flowable] = []
        story += self._cover()
        story.append(NextPageTemplate("body"))
        story += self._contents()
        story += self._how_to_use()
        for part in self.book.parts:
            story += self._part(part)
        story += self._closing()
        doc.build(story)
