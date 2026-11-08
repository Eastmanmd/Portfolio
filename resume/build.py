"""Build ATS-friendly resume PDFs from the plain-text resumes in resume/.

Each plain-text file is the single source of truth for its PDFs. This script turns
them into single-column Typst documents and compiles:

  files/Ali_Oku_CV.pdf                    public copy of the master resume, linked from the website (no phone number)
  resume/Ali_Oku_Master_Resume.pdf        AI x Biology master resume (includes phone; git-ignored)
  resume/Ali_Oku_Resume_private.pdf       earlier ATS resume (includes phone; git-ignored)

Usage:  python3 resume/build.py            (expects `quarto` on PATH, or set QUARTO=/path/to/quarto)
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ATS_SRC = ROOT / "resume" / "Ali_Oku_Resume_ATS.txt"
MASTER_SRC = ROOT / "resume" / "Ali_Oku_Master_Resume.txt"
FONTS = ROOT / "resume" / "fonts"
QUARTO = os.environ.get("QUARTO", "quarto")

SECTIONS = {
    "Professional Summary", "Technical Skills", "Professional Experience",
    "Projects", "Education", "Publications",
    "PROFESSIONAL SUMMARY", "TECHNICAL SKILLS", "PROFESSIONAL EXPERIENCE",
    "EDUCATION", "PUBLICATIONS AND OPEN-SOURCE", "CLEARANCE",
}
PHONE = re.compile(r"^\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}$")

PREAMBLE = r"""
#set document(title: "Ali Oku - Resume", author: "Ali Oku")
#set page(paper: "us-letter", margin: (x: 0.6in, y: 0.5in))
#set text(font: "IBM Plex Sans", size: 9.2pt, fill: rgb("#161616"), hyphenate: false)
#set par(leading: 0.5em, spacing: 0.5em)
#let bold(s) = text(font: "IBM Plex Sans SmBld", s)
#let section(s) = block(above: 11pt, below: 6pt, width: 100%,
  stroke: (bottom: 0.6pt + rgb("#161616")), inset: (bottom: 3pt),
  text(font: "IBM Plex Sans SmBld", size: 10.5pt, s))
#let bullet(s) = block(above: 3.5pt, below: 0pt, par(hanging-indent: 9pt, [•#h(4pt)#s]))
"""


def esc(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def to_typst(lines: list[str]) -> str:
    out = [PREAMBLE]
    name, *rest = lines
    out.append(f"#text(font: \"IBM Plex Sans SmBld\", size: 20pt, {esc(name)})")

    # Contact block: everything before the first section header, joined with separators.
    contact = []
    while rest and rest[0] not in SECTIONS:
        line = rest.pop(0).strip()
        if line:
            contact.append(line)
    out.append(f"#block(above: 6pt, text(size: 9pt, {esc('  |  '.join(contact))}))")

    section = None
    new_entry = False
    for raw in rest:
        line = raw.strip()
        if not line:
            new_entry = True
            continue
        if line in SECTIONS:
            section = line
            out.append(f"#section({esc(line)})")
            new_entry = True
            continue
        if line.startswith("•"):
            out.append(f"#bullet({esc(line.lstrip('• ').strip())})")
            new_entry = False
            continue
        if section in {"Technical Skills", "TECHNICAL SKILLS"} and ":" in line:
            cat, items = line.split(":", 1)
            out.append(f"#block(above: 4pt, [#bold({esc(cat + ':')}) #text({esc(items.strip())})])")
            continue
        if section in {"PROFESSIONAL EXPERIENCE", "EDUCATION"}:
            # Master format: every role or degree header is one bold line.
            out.append(f"#block(above: 8pt, bold({esc(line)}))")
            continue
        if section in {"Professional Experience", "Projects", "Education"}:
            # First line of an entry (organisation) is bold; following lines are titles and dates.
            if new_entry and section != "Education":
                out.append(f"#block(above: 8pt, bold({esc(line)}))")
            else:
                out.append(f"#block(above: 3pt, text({esc(line)}))")
            new_entry = False
            continue
        out.append(f"#block(above: 4pt, text({esc(line)}))")
    return "\n".join(out) + "\n"


def strip_phone(line: str) -> str:
    parts = [p for p in line.split(" | ") if not PHONE.match(p.strip())]
    return " | ".join(parts)


def build(src: Path, include_phone: bool, pdf: Path) -> None:
    lines = src.read_text(encoding="utf-8").splitlines()
    if not include_phone:
        lines = [strip_phone(l) for l in lines if not PHONE.match(l.strip())]
    typ = ROOT / "resume" / ".resume_build.typ"
    typ.write_text(to_typst(lines), encoding="utf-8")
    pdf.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([QUARTO, "typst", "compile", str(typ), str(pdf),
                    "--font-path", str(FONTS), "--ignore-system-fonts"], check=True)
    typ.unlink()
    print(f"built {pdf.relative_to(ROOT)}")


if __name__ == "__main__":
    build(MASTER_SRC, include_phone=False, pdf=ROOT / "files" / "Ali_Oku_CV.pdf")
    build(MASTER_SRC, include_phone=True, pdf=ROOT / "resume" / "Ali_Oku_Master_Resume.pdf")
    if ATS_SRC.exists():
        build(ATS_SRC, include_phone=True, pdf=ROOT / "resume" / "Ali_Oku_Resume_private.pdf")
    sys.exit(0)
