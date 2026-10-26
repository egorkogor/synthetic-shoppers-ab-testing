"""arXiv package of paper/paper_EN.md: build/arxiv/{main.tex, figures/*.png} + build/arxiv_submission.zip, and the abstract
in paper/arxiv_metadata.txt.

- pandoc (markdown -> LaTeX, standalone template, works under pdflatex as arXiv compiles and under XeTeX);
- the title goes to \title, section "0. Abstract" to the abstract environment, headings are unnumbered (numbers are in the text);
- a "**Figure N.** ..." paragraph after an image becomes that image's caption;
- every non-ASCII character is replaced by a LaTeX command; the build fails if one is left;
- the check compile uses tectonic if found; the PDF is a preview, arXiv builds its own from main.tex.

Needs pandoc and, for the check compile, tectonic (neither is installed by requirements.txt).
Run: PANDOC=... TECTONIC=... python tools/build_arxiv.py
"""
import os
import re
import shutil
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EN = ROOT / "paper"
SRC, OUT = EN / "paper_EN.md", ROOT / "build" / "arxiv"
PANDOC = os.environ.get("PANDOC", "pandoc")
TECTONIC = os.environ.get("TECTONIC", "tectonic")
AUTHOR = os.environ.get("PAPER_AUTHOR", "Egor Lozovoi")
ABSTRACT_LIMIT = 1920  # arXiv form limit, characters

UNI = {"\u2212": r"\ensuremath{-}", "\u2014": "---", "\u2013": "--", "\u03c1": r"\ensuremath{\rho}",
       "\u2248": r"\ensuremath{\approx}", "\u00d7": r"\ensuremath{\times}", "\u2192": r"\ensuremath{\rightarrow}",
       "\u2019": "'", "\u2018": "`", "\u201c": "``", "\u201d": "''", "\u2265": r"\ensuremath{\geq}",
       "\u03b1": r"\ensuremath{\alpha}", "\u2026": r"\ldots{}", "\u03c7": r"\ensuremath{\chi}",
       "\u00b2": r"\textsuperscript{2}", "\u0394": r"\ensuremath{\Delta}", "\u03ba": r"\ensuremath{\kappa}",
       "\u2075": r"\textsuperscript{5}", "\u2074": r"\textsuperscript{4}", "\u0141": r"\L{}",
       "\u00b1": r"\ensuremath{\pm}", "\u00a0": "~"}

HEADER = r"""
\usepackage[margin=2.4cm]{geometry}
\usepackage{etoolbox}
\usepackage{xurl}
\AtBeginEnvironment{longtable}{\footnotesize\setlength{\tabcolsep}{3pt}}
\setcounter{secnumdepth}{-2}
"""


def plain(md):
    """Markdown inline -> plain text for the arXiv abstract field."""
    return re.sub(r"\*\*|\*|`", "", md).strip()


def prepare(text):
    lines = text.split("\n")
    assert lines[0].startswith("# "), "first line must be the title"
    title = lines[0][2:].strip()
    body = "\n".join(lines[1:])
    m = re.search(r"(?ms)^## 0\. Abstract\n\n(.*?)\n\n(?=## )", body)
    abstract = m.group(1).strip()
    body = body[m.end():]
    # image + caption paragraph -> captioned figure
    def fig(mm):
        return f"![{mm.group(3).strip()}]({mm.group(2)})"
    body, nfig = re.subn(r"!\[([^\]]*)\]\(([^)]+)\)\n\n\*\*Figure \d+\.\*\* (.+)", fig, body)
    assert nfig == 4, nfig
    return title, abstract, widen_tables(body)


def widen_tables(md):
    """Pipe-table separator dashes proportional to the column's content, so pandoc's relative widths
    give long text columns more room (equal widths broke words like "Recommendations," into neighbours)."""
    out, block = [], []

    def flush():
        if len(block) >= 2 and re.fullmatch(r"\|(?:\s*-+:?\s*\|)+", block[1].strip()):
            cells = [[c.strip() for c in ln.strip().strip("|").split("|")] for ln in block if ln is not block[1]]
            ncol = len(cells[0])
            widths = []
            for j in range(ncol):
                longest = max(len(r[j]) if j < len(r) else 0 for r in cells)
                word = max((len(w) for r in cells if j < len(r) for w in r[j].split()), default=1)
                widths.append(min(max(longest, word + 3, 7), 45))
            seps = [c.strip() for c in block[1].strip().strip("|").split("|")]
            block[1] = "|" + "|".join("-" * w + (":" if s.endswith(":") else "") for w, s in zip(widths, seps)) + "|"
        out.extend(block)
        block.clear()

    for ln in md.split("\n"):
        if ln.startswith("|"):
            block.append(ln)
        else:
            flush()
            out.append(ln)
    flush()
    return "\n".join(out)


def to_latex(md, extra=()):
    r = subprocess.run([PANDOC, "-f", "markdown", "-t", "latex",
                        "--shift-heading-level-by=-1", "--columns=10", *extra],
                       input=md.encode("utf-8"), capture_output=True, check=True)
    return r.stdout.decode("utf-8").replace("\r\n", "\n")  # pandoc.exe writes CRLF on Windows


def asciify(tex):
    for k, v in UNI.items():
        tex = tex.replace(k, v)
    left = sorted({f"U+{ord(c):04X}" for c in tex if ord(c) > 127})
    if left:
        raise SystemExit(f"non-ASCII characters left in LaTeX: {left}")
    return tex


def main():
    title, abstract, body = prepare(SRC.read_text(encoding="utf-8"))
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "figures").mkdir(parents=True)
    figs = sorted(set(re.findall(r"\]\(figures/([^)]+\.png)\)", body)))
    for f in figs:
        shutil.copy2(EN / "figures" / f, OUT / "figures" / f)
    abs_tex = to_latex(abstract)
    meta = [f"title={title}", f"author={AUTHOR}", "date=", "documentclass=article", "fontsize=11pt",
            "colorlinks=true", "linkcolor=black", "urlcolor=blue!50!black"]
    # standalone with the real body, so pandoc loads longtable, graphicx etc.
    tex = to_latex(f"---\nheader-includes: |\n  ```{{=latex}}\n" + "\n".join("  " + ln for ln in HEADER.strip().splitlines())
                   + "\n  ```\n---\n\n" + body, ["--standalone", *sum((["-V", m] for m in meta), [])])
    assert tex.count("\\maketitle\n") == 1
    tex = tex.replace("\\maketitle\n", "\\maketitle\n\\begin{abstract}\n" + abs_tex + "\\end{abstract}\n", 1)
    tex = asciify(tex)
    (OUT / "main.tex").write_text(tex, encoding="ascii", newline="\n")

    abstract_plain = plain(abstract)
    (EN / "arxiv_metadata.txt").write_text(
        f"Title: {title}\n\nAuthors: {AUTHOR}\n\nPrimary category: cs.AI\nCross-list: stat.AP\n\n"
        f"Comments: {{pages}} pages, {len(figs)} figures\n\nLicense: choose on the form (arXiv non-exclusive licence by default)\n\n"
        f"Abstract ({len(abstract_plain)} characters, limit {ABSTRACT_LIMIT}):\n{abstract_plain}\n", encoding="utf-8")
    print(f"abstract: {len(abstract_plain)} characters (limit {ABSTRACT_LIMIT})")
    if len(abstract_plain) > ABSTRACT_LIMIT:
        print("WARNING: abstract is over the arXiv form limit")

    zp = ROOT / "build" / "arxiv_submission.zip"
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(OUT / "main.tex", "main.tex")
        for f in figs:
            z.write(OUT / "figures" / f, f"figures/{f}")
    print(f"OK {zp.name}: main.tex + {len(figs)} figures")

    if shutil.which(TECTONIC) or Path(TECTONIC).exists():
        r = subprocess.run([TECTONIC, "--keep-logs", "main.tex"], cwd=OUT, capture_output=True, text=True, encoding="utf-8", errors="replace")
        print(r.stdout[-1500:], r.stderr[-3000:])
        if r.returncode:
            raise SystemExit("tectonic failed")
        pdf = OUT / "main.pdf"
        print("LaTeX PDF:", pdf)
        import pymupdf  # object streams hide /Type /Page from a byte regex
        pages = len(pymupdf.open(pdf))
        if pages:
            md = EN / "arxiv_metadata.txt"
            md.write_text(md.read_text(encoding="utf-8").replace("{pages}", str(pages)), encoding="utf-8")


if __name__ == "__main__":
    main()
