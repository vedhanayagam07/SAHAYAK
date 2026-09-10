"""
generate_sample_data.py
=======================
Generates two sample data files used by Parts A and C:

1. sample_data/sample_timetable.png
   A Monday-to-Friday class timetable grid (6 subjects, 5 time slots)
   rendered with Pillow — simulates a photograph of a student's timetable.

2. sample_data/sample_syllabus.pdf
   A 1-page CS101 syllabus PDF (12 topics) generated with ReportLab —
   used by Part C to test document-grounded memory.

Run:
    python generate_sample_data.py
"""

import os
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "sample_data"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# PART 1 — Generate timetable PNG using Pillow
# ─────────────────────────────────────────────────────────────────────────────

def generate_timetable_image():
    from PIL import Image, ImageDraw, ImageFont
    import textwrap

    # Timetable data: rows = time slots, cols = Mon–Fri
    DAYS   = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    TIMES  = ["9:00–10:00", "10:00–11:00", "11:00–12:00", "2:00–3:00", "3:00–4:00"]

    # Subject grid — deliberately uneven so Part A can identify least-studied
    SCHEDULE = [
        ["Mathematics",  "Physics",     "Mathematics",  "Chemistry",  "Mathematics"],
        ["English",      "Mathematics", "Physics",      "Mathematics","English"],
        ["Chemistry",    "English",     "Chemistry",    "Physics",    "Chemistry"],
        ["Physics",      "Chemistry",   "English",      "English",    "Physics"],
        ["Free Period",  "Free Period", "Mathematics",  "Free Period","Chemistry"],
    ]

    # Subject → pastel color mapping
    COLORS = {
        "Mathematics": "#AED6F1",
        "Physics":     "#A9DFBF",
        "Chemistry":   "#F9E79F",
        "English":     "#F1948A",
        "Free Period": "#D5DBDB",
    }

    CELL_W    = 160
    CELL_H    = 70
    HDR_W     = 120   # width of the time label column
    TOP_H     = 50    # height of the day header row
    MARGIN    = 20

    IMG_W = MARGIN * 2 + HDR_W + CELL_W * len(DAYS)
    IMG_H = MARGIN * 2 + TOP_H + CELL_H * len(TIMES) + 60   # +60 for title

    img  = Image.new("RGB", (IMG_W, IMG_H), "#FDFEFE")
    draw = ImageDraw.Draw(img)

    # Try to load a nicer font; fall back to default
    try:
        font_title  = ImageFont.truetype("arial.ttf", 20)
        font_header = ImageFont.truetype("arial.ttf", 14)
        font_cell   = ImageFont.truetype("arial.ttf", 13)
        font_time   = ImageFont.truetype("arial.ttf", 11)
    except OSError:
        font_title  = ImageFont.load_default()
        font_header = font_title
        font_cell   = font_title
        font_time   = font_title

    # Title
    title_x = IMG_W // 2
    draw.text((title_x, MARGIN), "📅 Weekly Class Timetable — Semester 5",
              fill="#1A5276", font=font_title, anchor="mt")

    base_y = MARGIN + 50   # below title

    # Day headers
    for col, day in enumerate(DAYS):
        x0 = MARGIN + HDR_W + col * CELL_W
        y0 = base_y
        x1, y1 = x0 + CELL_W, y0 + TOP_H
        draw.rectangle([x0, y0, x1, y1], fill="#1A5276", outline="#FDFEFE", width=2)
        draw.text(((x0 + x1) // 2, (y0 + y1) // 2), day,
                  fill="white", font=font_header, anchor="mm")

    # Time labels + cells
    for row, (time_label, day_row) in enumerate(zip(TIMES, SCHEDULE)):
        y0 = base_y + TOP_H + row * CELL_H
        y1 = y0 + CELL_H

        # Time label cell
        draw.rectangle([MARGIN, y0, MARGIN + HDR_W, y1],
                       fill="#2C3E50", outline="#FDFEFE", width=1)
        draw.text((MARGIN + HDR_W // 2, (y0 + y1) // 2), time_label,
                  fill="white", font=font_time, anchor="mm")

        for col, subject in enumerate(day_row):
            x0 = MARGIN + HDR_W + col * CELL_W
            x1 = x0 + CELL_W
            color = COLORS.get(subject, "#FDFEFE")
            draw.rectangle([x0, y0, x1, y1], fill=color, outline="#BFC9CA", width=1)
            # Wrap long text
            lines = textwrap.wrap(subject, width=14)
            total_h = len(lines) * 16
            start_y = (y0 + y1) // 2 - total_h // 2
            for i, line in enumerate(lines):
                draw.text(((x0 + x1) // 2, start_y + i * 16),
                          line, fill="#1C2833", font=font_cell, anchor="mt")

    # Legend
    legend_y = base_y + TOP_H + len(TIMES) * CELL_H + 10
    draw.text((MARGIN, legend_y), "Subjects: ", fill="#1C2833", font=font_time)
    lx = MARGIN + 70
    for subj, color in COLORS.items():
        if subj == "Free Period":
            continue
        draw.rectangle([lx, legend_y, lx + 14, legend_y + 14], fill=color, outline="#999")
        draw.text((lx + 18, legend_y), subj, fill="#1C2833", font=font_time)
        lx += len(subj) * 7 + 30

    out_path = OUTPUT_DIR / "sample_timetable.png"
    img.save(out_path, "PNG", dpi=(150, 150))
    print(f"[OK] Timetable image saved -> {out_path}")
    return out_path


# ─────────────────────────────────────────────────────────────────────────────
# PART 2 — Generate syllabus PDF using ReportLab
# ─────────────────────────────────────────────────────────────────────────────

def generate_syllabus_pdf():
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.enums import TA_CENTER, TA_LEFT

    out_path = OUTPUT_DIR / "sample_syllabus.pdf"
    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=A4,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
    )

    styles = getSampleStyleSheet()
    style_title   = ParagraphStyle("title",   parent=styles["Title"],  fontSize=20, textColor=colors.HexColor("#1A5276"), spaceAfter=6)
    style_sub     = ParagraphStyle("sub",     parent=styles["Normal"], fontSize=11, textColor=colors.HexColor("#555555"), spaceAfter=12, alignment=TA_CENTER)
    style_section = ParagraphStyle("section", parent=styles["Heading2"], fontSize=13, textColor=colors.HexColor("#1A5276"), spaceBefore=16, spaceAfter=6)
    style_body    = ParagraphStyle("body",    parent=styles["Normal"], fontSize=10.5, leading=16, spaceAfter=4)
    style_topic   = ParagraphStyle("topic",   parent=styles["Normal"], fontSize=10.5, leading=18, leftIndent=20)

    # 12 syllabus topics — these are what Part C will track
    TOPICS = [
        ("1",  "Introduction to Algorithms & Complexity",          "Week 1–2"),
        ("2",  "Arrays and Linked Lists",                          "Week 2–3"),
        ("3",  "Stacks and Queues",                                "Week 3"),
        ("4",  "Recursion and Backtracking",                       "Week 4"),
        ("5",  "Sorting Algorithms (Bubble, Merge, Quick)",        "Week 5"),
        ("6",  "Binary Search and Divide & Conquer",               "Week 5–6"),
        ("7",  "Trees and Binary Search Trees (BST)",              "Week 6–7"),
        ("8",  "Graphs: BFS and DFS Traversal",                    "Week 7–8"),
        ("9",  "Dynamic Programming Fundamentals",                 "Week 8–9"),
        ("10", "Hashing and Hash Tables",                          "Week 9"),
        ("11", "Object-Oriented Programming Principles",           "Week 10–11"),
        ("12", "File Handling and Exception Management",           "Week 11–12"),
    ]

    story = []

    story.append(Paragraph("CS101: Introduction to Computer Science", style_title))
    story.append(Paragraph("Academic Year 2025–26 | Semester 1 | Credits: 4", style_sub))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1A5276"), spaceAfter=12))

    story.append(Paragraph("Course Description", style_section))
    story.append(Paragraph(
        "This course introduces students to the fundamental concepts of computer science including "
        "algorithm design, data structures, object-oriented programming, and computational thinking. "
        "By the end of the course, students will be able to analyse algorithmic complexity, "
        "implement core data structures, and apply OOP principles in practical projects.",
        style_body
    ))

    story.append(Paragraph("Syllabus Topics", style_section))
    story.append(Paragraph(
        "The following 12 topics form the complete syllabus. All topics are examinable.",
        style_body
    ))
    story.append(Spacer(1, 6))

    table_data = [["#", "Topic", "Schedule"]]
    for num, topic, schedule in TOPICS:
        table_data.append([num, topic, schedule])

    tbl = Table(table_data, colWidths=[1.2 * cm, 11 * cm, 3.5 * cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0),  colors.HexColor("#1A5276")),
        ("TEXTCOLOR",    (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",     (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, 0),  10),
        ("ALIGN",        (0, 0), (-1, -1), "LEFT"),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#EBF5FB"), colors.white]),
        ("FONTNAME",     (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",     (0, 1), (-1, -1), 10),
        ("GRID",         (0, 0), (-1, -1), 0.5, colors.HexColor("#BFC9CA")),
        ("LEFTPADDING",  (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
    ]))
    story.append(tbl)

    story.append(Spacer(1, 16))
    story.append(Paragraph("Assessment", style_section))
    story.append(Paragraph("• Mid-term Exam (Topics 1–6): 30%", style_topic))
    story.append(Paragraph("• End-term Exam (Topics 1–12): 50%", style_topic))
    story.append(Paragraph("• Assignments & Practicals: 20%", style_topic))

    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#BFC9CA"), spaceAfter=8))
    story.append(Paragraph(
        "This syllabus document is intended for use with SAHAYAK AI Study Assistant "
        "as a knowledge-base grounding document for memory testing (Part C).",
        ParagraphStyle("footer", parent=styles["Normal"], fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
    ))

    doc.build(story)
    print(f"[OK] Syllabus PDF saved -> {out_path}")
    return out_path


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("  SAHAYAK -- Generating Sample Data Files")
    print("=" * 60)
    generate_timetable_image()
    generate_syllabus_pdf()
    print("\n[OK] All sample data files generated successfully.")
    print(f"    Output directory: {OUTPUT_DIR.resolve()}")
