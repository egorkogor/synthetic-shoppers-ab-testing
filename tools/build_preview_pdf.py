"""Preview PDF of the paper without a TeX installation: markdown-it-py -> HTML -> PyMuPDF Story.

The PDF is a reading copy of the same text as the Markdown; the arXiv version is built from LaTeX (tools/build_arxiv.py).

    python tools/build_preview_pdf.py        -> paper/paper_EN_preview.pdf
    python tools/build_preview_pdf.py ru     -> paper/paper_RU_preview.pdf
"""
import io
import sys
from pathlib import Path

import pymupdf
from markdown_it import MarkdownIt

ROOT = Path(__file__).resolve().parents[1]
LANG = {"en": ("paper_EN", "figures"), "ru": ("paper_RU", "figures_ru")}
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


def main(lang: str = "en"):
    name, figs = LANG[lang]
    src, out = ROOT / "paper" / f"{name}.md", ROOT / "paper" / f"{name}_preview.pdf"
    md = src.read_text(encoding="utf-8")
    html = MarkdownIt("commonmark").enable("table").render(md)
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
    doc.subset_fonts()  # the Story embeds the whole TrueType font per text run; keep only the used glyphs once
    doc.save(out, garbage=4, deflate=True, clean=True)
    print(f"{out.relative_to(ROOT).as_posix()}: {len(doc)} pages")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "en")
