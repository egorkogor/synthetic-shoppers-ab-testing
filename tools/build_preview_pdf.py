"""Preview PDF of the paper without a TeX installation: markdown-it-py -> HTML -> PyMuPDF Story.

The PDF is a reading copy of the same text as the Markdown; the arXiv version is built from LaTeX (tools/build_arxiv.py).

    python tools/build_preview_pdf.py        -> paper/paper_EN_preview.pdf
    python tools/build_preview_pdf.py ru     -> paper/paper_RU_preview.pdf
"""
import io
import re
import sys
from pathlib import Path

import pymupdf
from markdown_it import MarkdownIt

ROOT = Path(__file__).resolve().parents[1]
LANG = {"en": ("paper_EN", "figures"), "ru": ("paper_RU", "figures_ru")}
REPOSITORY = "https://github.com/egorkogor/synthetic-shoppers-ab-testing"
FONT_DIRS = (Path("C:/Windows/Fonts"), Path("/usr/share/fonts/truetype/dejavu"), Path("/Library/Fonts"))
CSS = """
body { font-family: sans-serif; font-size: 9.5pt; line-height: 1.35; }
h1 { font-size: 16pt; margin: 0 0 8pt 0; }
h2 { font-size: 12.5pt; margin: 12pt 0 4pt 0; }
h3 { font-size: 10.5pt; margin: 9pt 0 3pt 0; }
p, li { margin: 0 0 5pt 0; text-align: justify; }
table { border-collapse: collapse; margin: 4pt 0 8pt 0; font-size: 7.2pt; }
th, td { border: 0.4pt solid #888; padding: 1.5pt 3pt; vertical-align: top; }
th { background-color: #eeeeee; }
blockquote { margin: 3pt 12pt; color: #333; }
code { font-family: monospace; font-size: 8pt; }
img { width: 100%; }
"""


def fonts(archive) -> str:
    """A system TrueType font with Greek and math signs (the built-in Base14 fonts have no rho, kappa or minus sign)."""
    for d in FONT_DIRS:
        for regular, bold in (("arial.ttf", "arialbd.ttf"), ("DejaVuSans.ttf", "DejaVuSans-Bold.ttf")):
            if (d / regular).exists() and (d / bold).exists():
                archive.add(str(d / regular), regular)
                archive.add(str(d / bold), bold)
                return (f"@font-face {{font-family: sans-serif; src: url({regular});}}\n"
                        f"@font-face {{font-family: sans-serif; font-weight: bold; src: url({bold});}}\n")
    return ""


def markdown_links(parser, md):
    """Extract rendered Markdown link labels and destinations, including URLs with parentheses."""
    links = []
    for token in parser.parse(md):
        children = token.children or []
        i = 0
        while i < len(children):
            child = children[i]
            if child.type != "link_open":
                i += 1
                continue
            url = child.attrGet("href")
            label = []
            i += 1
            while i < len(children) and children[i].type != "link_close":
                if children[i].type in {"text", "code_inline"}:
                    label.append(children[i].content)
                i += 1
            if url:
                links.append(("".join(label), url))
            i += 1
    return links


def link_pdf_text(doc, label, url):
    """Add a URI annotation over rendered text, accounting for PDF soft hyphens in DOI strings."""
    if url.startswith("https://doi.org/"):
        identifier = label.split(":", 1)[-1].strip()
        search_prefix = identifier.split("(", 1)[0] if "(" in identifier else identifier
        for page in doc:
            words = page.get_text("words")
            matches = []
            for word in words:
                visible = (word[4].replace("\u00ad", "-").replace("\u2010", "-")
                          .replace("\u2011", "-").replace("\u2012", "-").replace("\u2013", "-"))
                visible = visible.rstrip(".,;:")
                if visible.startswith(identifier) or ("(" in identifier and visible.startswith(search_prefix)):
                    matches.append(pymupdf.Rect(word[:4]))
            for rect in matches:
                page.insert_link({"kind": pymupdf.LINK_URI, "from": rect, "uri": url})
    else:
        for page in doc:
            for rect in page.search_for(label):
                page.insert_link({"kind": pymupdf.LINK_URI, "from": rect, "uri": url})


def main(lang: str = "en"):
    name, figs = LANG[lang]
    src, out = ROOT / "paper" / f"{name}.md", ROOT / "paper" / f"{name}_preview.pdf"
    md = src.read_text(encoding="utf-8")
    md = md.replace(r"$\rho$", "\u03c1")  # render the TeX math used in the arXiv abstract in reading copies
    parser = MarkdownIt("commonmark").enable("table")
    html = parser.render(md)
    html = html.replace(f'src="{figs}/', 'src="')
    archive = pymupdf.Archive(str(ROOT / "paper" / figs))
    story = pymupdf.Story(html=html, user_css=fonts(archive) + CSS, archive=archive)
    buf = io.BytesIO()
    writer = pymupdf.DocumentWriter(buf)
    rect, where = pymupdf.paper_rect("a4"), pymupdf.paper_rect("a4") + (54, 54, -54, -54)
    more = True
    while more:
        dev = writer.begin_page(rect)
        more, _ = story.place(where)
        story.draw(dev)
        writer.end_page()
    writer.close()
    doc = pymupdf.open("pdf", buf.getvalue())
    doc.set_metadata({"title": md.splitlines()[0][2:].strip(), "author": "Egor Lozovoi"})
    pdf_links = [(label, url) for label, url in markdown_links(parser, md)
                 if url == REPOSITORY or url.startswith(("https://doi.org/", "https://arxiv.org/"))]
    for arxiv_id in set(re.findall(r"\barXiv:\s*(\d{4}\.\d{4,5}(?:v\d+)?)", md, flags=re.IGNORECASE)):
        pdf_links.append((f"arXiv:{arxiv_id}", f"https://arxiv.org/abs/{arxiv_id}"))
    for label, url in set(pdf_links):
        link_pdf_text(doc, label, url)
    doc.subset_fonts()  # the Story embeds the whole TrueType font per text run; keep only the used glyphs once
    doc.save(out, garbage=4, deflate=True, clean=True)
    print(f"{out.relative_to(ROOT).as_posix()}: {len(doc)} pages")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "en")
