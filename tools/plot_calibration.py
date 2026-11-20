#!/usr/bin/env python3
"""Build public agent-only Figure 3 from data/calibration.csv.

The categorical statuses encode the pre-recorded tolerance band. No human
rates or traffic denominators are read or plotted.
"""
import csv
from pathlib import Path
from xml.sax.saxutils import escape

import pymupdf

ROOT = Path(__file__).resolve().parents[1]
CALIBRATION = ROOT / "data" / "calibration.csv"
EN_SVG = ROOT / "paper" / "figures" / "fig3_calibration.svg"
EN_PNG = ROOT / "paper" / "figures" / "fig3_calibration.png"
RU_PNG = ROOT / "paper" / "figures_ru" / "fig3_calibration.png"

ROWS = (
    ("H1: at least two", "H1: at least two cards", "within 0.67--1.5x human band",
     "в коридоре 0.67--1.5x человеческого ориентира"),
    ("Add from a product card opened from search", "Card from search", "within 0.67--1.5x human band",
     "в коридоре 0.67--1.5x человеческого ориентира"),
    ("Add from a product card opened from a category", "Card from category", "above 1.5x human band",
     "выше 1.5x человеческого ориентира"),
    ("Add from the search results page", "Search page", "within 0.67--1.5x human band",
     "в коридоре 0.67--1.5x человеческого ориентира"),
)


def load_agent_values():
    with CALIBRATION.open(encoding="utf-8", newline="") as stream:
        data = list(csv.DictReader(stream))
    result = []
    for prefix, label_en, status_en, status_ru in ROWS:
        matches = [row for row in data if row["measure"].startswith(prefix)]
        if len(matches) != 1:
            raise ValueError(f"Expected one calibration row for {prefix!r}, got {len(matches)}")
        row = matches[0]
        result.append({
            "label_en": label_en,
            "status_en": status_en,
            "status_ru": status_ru,
            "before": 100 * int(row["agents_before_k"]) / int(row["agents_before_n"]),
            "after": 100 * int(row["agents_after_k"]) / int(row["agents_after_n"]),
        })
    return result


def make_svg(rows, language):
    width, height = 1120, 540
    plot_left, plot_right = 300, 690
    plot_top, plot_bottom = 75, 475
    row_y = [125, 235, 345, 455]
    scale = (plot_right - plot_left) / 100
    ru = language == "ru"
    title = "Действия агентов до и после калибровки" if ru else "Agent action frequencies before and after calibration"
    status_header = "Положение после калибровки" if ru else "Status after calibration"
    before_label = "Агент до" if ru else "Agent before"
    after_label = "Агент после" if ru else "Agent after"
    labels = ("H1: минимум две карточки", "Карточка из поиска", "Карточка из категории", "Страница поиска") if ru else tuple(r["label_en"] for r in rows)
    colors = {"before": "#2a78d6", "after": "#d76032"}
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<style>text{font-family:Arial,"DejaVu Sans",sans-serif;fill:#171717}.muted{fill:#555}.small{font-size:13px}.label{font-size:15px}.title{font-size:21px;font-weight:600}.status{font-size:14px}</style>',
        f'<text class="title" x="{plot_left}" y="35">{escape(title)}</text>',
        (f'<text class="small muted" x="{plot_left}" y="61">Agent share of sessions (%)</text>' if not ru else
         f'<text class="small muted" x="{plot_left}" y="61">Доля агентских сессий (%)</text>'),
        f'<text class="small muted" x="{plot_right + 32}" y="61">{escape(status_header)}</text>',
    ]
    for tick in range(0, 101, 20):
        x = plot_left + tick * scale
        parts.append(f'<line x1="{x:.1f}" y1="{plot_top}" x2="{x:.1f}" y2="{plot_bottom}" stroke="#d8d8d8" stroke-width="1"/>')
        parts.append(f'<text class="small muted" text-anchor="middle" x="{x:.1f}" y="{plot_bottom + 25}">{tick}%</text>')
    parts.append(f'<line x1="{plot_left}" y1="{plot_bottom}" x2="{plot_right}" y2="{plot_bottom}" stroke="#333" stroke-width="1.2"/>')
    for index, row in enumerate(rows):
        y = row_y[index]
        parts.append(f'<text class="label" x="24" y="{y + 5}">{escape(labels[index])}</text>')
        for key, offset, label in (("before", -10, before_label), ("after", 14, after_label)):
            x = plot_left + row[key] * scale
            color = colors[key]
            parts.append(f'<circle cx="{x:.1f}" cy="{y}" r="6.5" fill="{color}" stroke="#ffffff" stroke-width="1.5"/>')
            value_label = f"{row[key]:.1f}%".replace(".", ",") if ru else f"{row[key]:.1f}%"
            parts.append(f'<text class="small" text-anchor="middle" x="{x:.1f}" y="{y + offset}">{escape(label)}: {value_label}</text>')
        status = row["status_ru"] if ru else row["status_en"]
        parts.append(f'<text class="status" x="{plot_right + 32}" y="{y + 5}">{escape(status)}</text>')
    legend_y = 520
    for key, x, label in (("before", plot_left, before_label), ("after", plot_left + 150, after_label)):
        parts.append(f'<circle cx="{x}" cy="{legend_y - 5}" r="6" fill="{colors[key]}"/>')
        parts.append(f'<text class="small" x="{x + 12}" y="{legend_y}">{escape(label)}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def render_png(svg_text, destination):
    document = pymupdf.open(stream=svg_text.encode("utf-8"), filetype="svg")
    if len(document) < 1:
        raise RuntimeError("SVG renderer produced no pages")
    pixmap = document[0].get_pixmap(matrix=pymupdf.Matrix(1.5, 1.5), alpha=False)
    pixmap.save(destination)


def main():
    values = load_agent_values()
    english = make_svg(values, "en")
    russian = make_svg(values, "ru")
    EN_SVG.write_text(english, encoding="utf-8")
    render_png(english, EN_PNG)
    render_png(russian, RU_PNG)
    for output in (EN_SVG, EN_PNG, RU_PNG):
        print(output.relative_to(ROOT).as_posix())


if __name__ == "__main__":
    main()
