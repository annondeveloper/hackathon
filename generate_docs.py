"""
generate_docs.py — Generate formatted Word (.docx) documents from Markdown files.

Usage:
    python generate_docs.py

Outputs:
    docs/ClaimClear_AI_README.docx
    docs/ClaimClear_AI_Architecture.docx
    docs/ClaimClear_AI_Deployment_Guide.docx
    docs/ClaimClear_AI_Design_Decisions.docx
"""

import os
import re

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH


def create_styled_doc(title: str) -> Document:
    """Create a Word document with consistent branding."""
    doc = Document()

    # Set default font
    style = doc.styles["Normal"]
    font = style.font
    font.name = "Calibri"
    font.size = Pt(11)
    font.color.rgb = RGBColor(0x33, 0x33, 0x33)

    # Title
    heading = doc.add_heading(title, level=0)
    for run in heading.runs:
        run.font.color.rgb = RGBColor(0x0F, 0x4C, 0x81)  # Navy

    # Subtitle
    subtitle = doc.add_paragraph("ClaimClear AI — AI-Powered Insurance Claim Explanation Assistant")
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in subtitle.runs:
        run.font.size = Pt(12)
        run.font.color.rgb = RGBColor(0x17, 0xA2, 0xB8)  # Teal
        run.font.italic = True

    doc.add_paragraph("")  # Spacer
    return doc


def markdown_to_docx(md_path: str, title: str, output_path: str) -> None:
    """Convert a Markdown file to a formatted Word document."""
    with open(md_path, "r") as f:
        content = f.read()

    doc = create_styled_doc(title)

    lines = content.split("\n")
    i = 0
    in_code_block = False
    code_buffer = []
    in_table = False
    table_rows = []

    while i < len(lines):
        line = lines[i]

        # Code block handling
        if line.strip().startswith("```"):
            if in_code_block:
                # End code block
                code_text = "\n".join(code_buffer)
                para = doc.add_paragraph()
                run = para.add_run(code_text)
                run.font.name = "Consolas"
                run.font.size = Pt(9)
                run.font.color.rgb = RGBColor(0x2D, 0x2D, 0x2D)
                para.paragraph_format.left_indent = Inches(0.3)
                code_buffer = []
                in_code_block = False
            else:
                in_code_block = True
            i += 1
            continue

        if in_code_block:
            code_buffer.append(line)
            i += 1
            continue

        # Table handling
        if "|" in line and not line.strip().startswith("#"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            # Skip separator rows
            if all(re.match(r"^[-:]+$", c) for c in cells):
                i += 1
                continue
            if not in_table:
                in_table = True
                table_rows = []
            table_rows.append(cells)
            # Check if next line continues the table
            if i + 1 < len(lines) and "|" in lines[i + 1]:
                i += 1
                continue
            else:
                # Render table
                if table_rows:
                    num_cols = max(len(r) for r in table_rows)
                    table = doc.add_table(
                        rows=len(table_rows), cols=num_cols, style="Light Grid Accent 1"
                    )
                    for ri, row_data in enumerate(table_rows):
                        for ci, cell_text in enumerate(row_data):
                            if ci < num_cols:
                                cell = table.cell(ri, ci)
                                cell.text = cell_text.strip("*")
                                for para in cell.paragraphs:
                                    for run in para.runs:
                                        run.font.size = Pt(9)
                    doc.add_paragraph("")  # Spacer after table
                in_table = False
                table_rows = []
                i += 1
                continue

        # Headings
        if line.startswith("# ") and not line.startswith("##"):
            # Skip the top-level title (already in doc title)
            i += 1
            continue
        elif line.startswith("## "):
            text = line.lstrip("#").strip()
            heading = doc.add_heading(text, level=2)
            for run in heading.runs:
                run.font.color.rgb = RGBColor(0x0F, 0x4C, 0x81)
            i += 1
            continue
        elif line.startswith("### "):
            text = line.lstrip("#").strip()
            heading = doc.add_heading(text, level=3)
            for run in heading.runs:
                run.font.color.rgb = RGBColor(0x17, 0xA2, 0xB8)
            i += 1
            continue

        # Horizontal rule
        if line.strip() == "---":
            doc.add_paragraph("_" * 60)
            i += 1
            continue

        # Blockquote
        if line.startswith("> "):
            text = line.lstrip("> ").strip()
            para = doc.add_paragraph()
            para.paragraph_format.left_indent = Inches(0.5)
            run = para.add_run(text)
            run.font.italic = True
            run.font.color.rgb = RGBColor(0x55, 0x55, 0x55)
            i += 1
            continue

        # Bullet points
        if re.match(r"^[-*] ", line.strip()):
            text = re.sub(r"^[-*] ", "", line.strip())
            text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)  # Remove bold markers
            doc.add_paragraph(text, style="List Bullet")
            i += 1
            continue

        # Numbered lists
        if re.match(r"^\d+\. ", line.strip()):
            text = re.sub(r"^\d+\. ", "", line.strip())
            text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
            doc.add_paragraph(text, style="List Number")
            i += 1
            continue

        # Empty lines
        if not line.strip():
            i += 1
            continue

        # Regular paragraphs
        text = line.strip()
        para = doc.add_paragraph()
        # Handle bold text
        parts = re.split(r"(\*\*.+?\*\*)", text)
        for part in parts:
            if part.startswith("**") and part.endswith("**"):
                run = para.add_run(part[2:-2])
                run.bold = True
            else:
                para.add_run(part)

        i += 1

    doc.save(output_path)
    print(f"  Generated: {output_path}")


def main():
    """Generate all Word documents."""
    os.makedirs("docs", exist_ok=True)

    documents = [
        ("README.md", "ClaimClear AI", "docs/ClaimClear_AI_README.docx"),
        ("ARCHITECTURE.md", "Architecture", "docs/ClaimClear_AI_Architecture.docx"),
        ("DEPLOYMENT.md", "Deployment Guide", "docs/ClaimClear_AI_Deployment_Guide.docx"),
        ("DESIGN_DECISIONS.md", "Design Decisions", "docs/ClaimClear_AI_Design_Decisions.docx"),
    ]

    print("Generating Word documents...")
    for md_file, title, output in documents:
        if os.path.exists(md_file):
            markdown_to_docx(md_file, title, output)
        else:
            print(f"  Skipped: {md_file} (not found)")

    print(f"\nDone! {len(documents)} documents generated in docs/")


if __name__ == "__main__":
    main()
