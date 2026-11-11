"""Render the role-specific Markdown report as a readable academic PDF.

Run using the bundled Python runtime with reportlab and pypdf.
"""
from pathlib import Path
import argparse
import re
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
)
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "market_research_literature_review.md"
OUTPUT = ROOT.parent / "output/pdf/amazon_india_market_research_literature_review.pdf"


def register_fonts():
    folder = Path("C:/Windows/Fonts")
    for name, file in [("Arial", "arial.ttf"), ("Arial-Bold", "arialbd.ttf"),
                       ("Arial-Italic", "ariali.ttf"), ("Arial-BoldItalic", "arialbi.ttf")]:
        pdfmetrics.registerFont(TTFont(name, str(folder / file)))
    pdfmetrics.registerFontFamily("Arial", normal="Arial", bold="Arial-Bold",
                                  italic="Arial-Italic", boldItalic="Arial-BoldItalic")


def wrap_url(url):
    # Break long URLs after "/" rather than mid-word; ReportLab only wraps at spaces.
    lines = [""]
    for part in re.split(r"(?<=/)", url):
        if lines[-1] and pdfmetrics.stringWidth(lines[-1] + part, "Arial", 11) > A4[0] - 96:
            lines.append("")
        lines[-1] += part
    return "<br/>".join(escape(line) for line in lines)


def inline(text, show_urls=False):
    pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)|\*\*([^*]+)\*\*|\*([^*]+)\*")
    result, last = [], 0
    for match in pattern.finditer(text):
        result.append(escape(text[last:match.start()]))
        if match.group(1) is not None:
            label, url = match.group(1), match.group(2)
            if label.isdigit():
                label = "[" + label + "]"
            link = '<link href="' + escape(url, {'"': '&quot;'}) + '" color="#174E70">'
            if show_urls:
                # Print the full address on its own line so readers can see and copy it.
                result.append(escape(label) + ":<br/>" + link + wrap_url(url) + '</link>')
            else:
                result.append(link + escape(label) + '</link>')
        elif match.group(3) is not None:
            result.append("<b>" + escape(match.group(3)) + "</b>")
        else:
            result.append("<i>" + escape(match.group(4)) + "</i>")
        last = match.end()
    result.append(escape(text[last:]))
    rendered = "".join(result)
    # Keep numeric citations with the preceding word, including adjacent links.
    return re.sub(r" (?=(?:<link\b[^>]*>\[\d+\]</link>|\[\d+\]))", "&#160;", rendered)


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Arial", 9)
    canvas.setFillColor(colors.HexColor("#555555"))
    canvas.drawString(48, 25, "SC4025  |  Amazon India market research")
    canvas.drawRightString(A4[0] - 48, 25, str(doc.page))
    canvas.restoreState()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--title", default="Market Research and Literature Review for Amazon India")
    parser.add_argument("--required-text", action="append", default=[])
    parser.add_argument("--references-new-page", action="store_true")
    args = parser.parse_args()
    register_fonts()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    body = ParagraphStyle("Body", fontName="Arial", fontSize=11, leading=16.5,
                          textColor=colors.black, alignment=TA_LEFT, spaceAfter=6,
                          allowWidows=0, allowOrphans=0)
    title = ParagraphStyle("Title", parent=body, fontName="Arial-Bold", fontSize=20,
                           leading=25, spaceAfter=11, keepWithNext=True)
    heading = ParagraphStyle("Heading", parent=body, fontName="Arial-Bold", fontSize=13,
                             leading=18, spaceBefore=13, spaceAfter=7, keepWithNext=True)
    subheading = ParagraphStyle("Subheading", parent=body, fontName="Arial-Bold",
                                spaceBefore=9, spaceAfter=4, keepWithNext=True)
    cellstyle = ParagraphStyle("Cell", parent=body, spaceAfter=0,
                              allowWidows=1, allowOrphans=1)
    headerstyle = ParagraphStyle("TableHeader", parent=cellstyle, fontName="Arial-Bold")
    refstyle = ParagraphStyle("References", parent=body, spaceAfter=7)
    story = []
    lines = args.source.read_text(encoding="utf-8").splitlines()
    index = 0
    in_references = False
    while index < len(lines):
        line = lines[index].strip()
        if not line:
            index += 1
            continue
        if line.startswith("# "):
            story.append(Paragraph(inline(line[2:]), title))
        elif line.startswith("## "):
            name = line[3:]
            if name == "References":
                in_references = True
                if args.references_new_page:
                    story.append(PageBreak())
            story.append(Paragraph(inline(name), heading))
        elif line.startswith("### "):
            story.append(Paragraph(inline(line[4:]), subheading))
        elif line.startswith("|"):
            tablelines = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                cells = [x.strip() for x in lines[index].strip().strip("|").split("|")]
                if not all(re.fullmatch(r"[:\- ]+", x) for x in cells):
                    tablelines.append(cells)
                index += 1
            widths = [112, 184, A4[0]-96-296]
            if tablelines[0][0] == "Layer":
                widths = [80, 228, A4[0]-96-308]
            rendered = [[Paragraph(inline(cell), headerstyle if rowidx == 0 else cellstyle)
                         for cell in row] for rowidx, row in enumerate(tablelines)]
            table = Table(rendered, colWidths=widths, repeatRows=1, hAlign="LEFT")
            table.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#E5EDF2")),
                ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#F6F8FA")]),
                ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#D9D9D9")),
                ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                ("LEFTPADDING", (0,0), (-1,-1), 7),
                ("RIGHTPADDING", (0,0), (-1,-1), 7),
                ("TOPPADDING", (0,0), (-1,-1), 7),
                ("BOTTOMPADDING", (0,0), (-1,-1), 7),
            ]))
            story.extend([Spacer(1, 5), table, Spacer(1, 10)])
            continue
        else:
            numbered = re.match(r"^(?:\[(\d+)\]|(\d+)\.)\s+(.*)", line)
            if in_references and numbered:
                number = numbered.group(1) or numbered.group(2)
                # Drop the full stop after a closing URL so it is not copied with it.
                entry = re.sub(r"(\]\([^)]+\))\.$", r"\1", numbered.group(3))
                text = "<b>[" + number + "]</b> " + inline(entry, show_urls=True)
                story.append(Paragraph(text, refstyle))
            else:
                story.append(Paragraph(inline(line), body))
        index += 1
    document = SimpleDocTemplate(str(args.output), pagesize=A4,
        leftMargin=48, rightMargin=48, topMargin=45, bottomMargin=47,
        title=args.title,
        author="SC4025 project", subject="Academic and consulting evidence, competitor benchmark, SWOT and market sizing")
    document.build(story, onFirstPage=footer, onLaterPages=footer)
    reader = PdfReader(args.output)
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    normalized_text = re.sub(r"\s+", " ", text)
    assert len(reader.pages) <= 12, "Review pagination before delivery"
    assert all(phrase in normalized_text for phrase in ["References", *args.required_text])
    assert not any(token in text for token in ["turn16search", "\ufffd", "\u25a0"])
    links = sum(1 for page in reader.pages for ref in page.get("/Annots", [])
                if ref.get_object().get("/Subtype") == "/Link")
    print(f"Saved: {args.output}\nPages: {len(reader.pages)}\nClickable citations: {links}")
    for i, page in enumerate(reader.pages, 1):
        content = page.extract_text() or ""
        print(f"Page {i}: {len(content.split())} words; starts {content[:80]!r}")


if __name__ == "__main__":
    main()
