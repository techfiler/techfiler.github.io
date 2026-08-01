"""Colour palette and shared typography settings."""

from reportlab.lib.colors import HexColor

INK = HexColor("#12232E")
INK_SOFT = HexColor("#3B4A54")
MUTED = HexColor("#6B7A85")
RULE = HexColor("#D6DEE3")
PAPER = HexColor("#FFFFFF")

RED = HexColor("#C0392B")
RED_TINT = HexColor("#FBEDEB")
BLUE = HexColor("#1B5E8C")
BLUE_TINT = HexColor("#E8F1F7")
TEAL = HexColor("#0E7C6B")
TEAL_TINT = HexColor("#E6F4F1")
AMBER = HexColor("#B7791F")
AMBER_TINT = HexColor("#FBF3E2")
PURPLE = HexColor("#5B3E8E")
PURPLE_TINT = HexColor("#F0EBF8")
SLATE = HexColor("#44576B")
SLATE_TINT = HexColor("#EDF1F4")
CODE_BG = HexColor("#F3F6F8")

LEVEL_COLORS = {
    "Foundation": (TEAL, TEAL_TINT),
    "Intermediate": (BLUE, BLUE_TINT),
    "Senior": (PURPLE, PURPLE_TINT),
    "Architect": (RED, RED_TINT),
}

# Hex strings for the DOCX builder, which cannot consume reportlab colours.
DOCX_LEVEL_COLORS = {
    "Foundation": ("0E7C6B", "E6F4F1"),
    "Intermediate": ("1B5E8C", "E8F1F7"),
    "Senior": ("5B3E8E", "F0EBF8"),
    "Architect": ("C0392B", "FBEDEB"),
}

BODY_FONT = "Helvetica"
BODY_BOLD = "Helvetica-Bold"
BODY_ITALIC = "Helvetica-Oblique"
MONO_FONT = "Courier"
MONO_BOLD = "Courier-Bold"
