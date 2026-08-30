"""Renders resume.json (+ a profile) into a resume PDF.

resume.json is the single, ever-growing source of truth for resume content
— new certifications, bootcamps, skills, and projects get added there, not
hand-edited into a PDF. index.html's Experience section mirrors it by hand
today; the job-search tool (later) and cover-letter generation will read it
directly.

Two kinds of output:
  --profile full   The comprehensive "portfolio resume" — every skill,
                    every highlight, every public project. No length cap.
                    This is what the portfolio site links to.
  --profile <name> A tailored, ~2-page resume for one role family, driven
                    by scripts/profiles/<name>.json (which selects a subset
                    of resume.json's skills/highlights/projects). Used for
                    the per-archetype resumes kept in the profile repo's
                    Resume/ folder.

Usage:
    python scripts/generate_resume.py --profile full
    python scripts/generate_resume.py --profile ai --out /path/to/out.pdf
"""

import argparse
import json
import os
from datetime import date

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESUME_JSON = os.path.join(ROOT, "assets", "resume.json")
PROJECTS_JSON = os.path.join(ROOT, "assets", "projects-curated.json")
PROFILES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "profiles")
DEFAULT_OUTPUT = os.path.join(ROOT, "assets", "Bishal-Dhungana-Resume.pdf")

INK = colors.HexColor("#1a1a1a")
NAVY = colors.HexColor("#1F3864")
RULE = colors.HexColor("#444444")
LINK_COLOR = "#1F3864"

styles = {
    "name": ParagraphStyle("name", fontName="Helvetica-Bold", fontSize=16, leading=19, textColor=NAVY, alignment=TA_CENTER, spaceAfter=6),
    "contact": ParagraphStyle("contact", fontName="Helvetica", fontSize=9, leading=12, textColor=INK, alignment=TA_CENTER, spaceAfter=6),
    "section": ParagraphStyle("section", fontName="Helvetica-Bold", fontSize=11, leading=13, textColor=NAVY, spaceBefore=12, spaceAfter=2),
    "summary": ParagraphStyle("summary", fontName="Helvetica", fontSize=10, textColor=INK, leading=13.5, spaceAfter=4),
    "role_title": ParagraphStyle("role_title", fontName="Helvetica-Bold", fontSize=10, leading=12.5, textColor=INK),
    "role_meta": ParagraphStyle("role_meta", fontName="Helvetica-Oblique", fontSize=9.2, leading=12.5, textColor=INK, alignment=TA_RIGHT),
    "bullet": ParagraphStyle("bullet", fontName="Helvetica", fontSize=9.5, textColor=INK, leading=12.5, leftIndent=14, spaceAfter=2),
    "edu": ParagraphStyle("edu", fontName="Helvetica", fontSize=9.5, textColor=INK, leading=13, spaceAfter=3),
    "small": ParagraphStyle("small", fontName="Helvetica", fontSize=9.5, textColor=INK, leading=13, spaceAfter=2),
    "project": ParagraphStyle("project", fontName="Helvetica", fontSize=9, textColor=INK, leading=13, spaceAfter=5),
}


def rule(color=RULE, thickness=0.75, space_before=2, space_after=8):
    return HRFlowable(width="100%", thickness=thickness, color=color, spaceBefore=space_before, spaceAfter=space_after)


def section_header(story, title):
    story.append(Paragraph(title, styles["section"]))
    story.append(rule())


def fmt_date(ym):
    if not ym:
        return "Present"
    y, m = ym.split("-")
    return date(int(y), int(m), 1).strftime("%b %Y")


def load_project_catalog():
    with open(PROJECTS_JSON, encoding="utf-8") as f:
        return {p["name"]: p for p in json.load(f)["projects"]}


def project_line(p):
    links = []
    if p.get("live_url"):
        links.append(f'<link href="{p["live_url"]}" color="{LINK_COLOR}">Demo</link>')
    if p.get("docs_url"):
        links.append(f'<link href="{p["docs_url"]}" color="{LINK_COLOR}">Docs</link>')
    if p.get("repo"):
        links.append(f'<link href="https://github.com/{p["repo"]}" color="{LINK_COLOR}">Repo</link>')
    stack = ", ".join(p.get("stack", []))
    line = f"<b>{p['name']}:</b> {p['description']}"
    if stack:
        line += f" <i>({stack})</i>"
    if links:
        line += "  " + " | ".join(links)
    return line


def job_header_row(job):
    left = Paragraph(f"{job['title']} — {job['company']}", styles["role_title"])
    meta = f"{fmt_date(job['startDate'])} – {fmt_date(job['endDate'])}"
    if job.get("location"):
        meta = f"{job['location']}  |  {meta}"
    right = Paragraph(meta, styles["role_meta"])
    t = Table([[left, right]], colWidths=[4.9 * inch, 2.5 * inch])
    t.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def build_story(data, profile):
    story = []
    basics = data["basics"]

    story.append(Paragraph(basics["name"], styles["name"]))

    profile_map = {p["network"]: p["url"] for p in basics.get("profiles", [])}

    def linked(url):
        display = url.replace("https://www.", "").replace("https://", "").rstrip("/")
        return f'<link href="{url}" color="{LINK_COLOR}"><u>{display}</u></link>'

    contact_bits = [basics["location"]]
    if basics.get("phone"):
        contact_bits.append(basics["phone"])
    contact_bits.append(basics["email"])
    if "LinkedIn" in profile_map:
        contact_bits.append(linked(profile_map["LinkedIn"]))
    contact_bits.append(linked(basics["website"]))
    if "GitHub" in profile_map:
        contact_bits.append(linked(profile_map["GitHub"]))
    story.append(Paragraph(" &nbsp;|&nbsp; ".join(contact_bits), styles["contact"]))

    section_header(story, "SUMMARY")
    story.append(Paragraph(profile.get("summary", data["summary"]), styles["summary"]))

    section_header(story, "SKILLS")
    skill_groups = profile.get("skill_groups") or list(data["skills"].keys())
    for group in skill_groups:
        items = data["skills"].get(group)
        if items:
            story.append(Paragraph(f"<b>{group}:</b> {', '.join(items)}", styles["small"]))

    section_header(story, "EXPERIENCE")
    work_filter = profile.get("work_highlights")
    for i, job in enumerate(data["work"]):
        story.append(job_header_row(job))
        indices = work_filter.get(str(i)) if work_filter else None
        highlights = job["highlights"] if indices is None else [job["highlights"][j] for j in indices]
        for h in highlights:
            story.append(Paragraph(f"&bull;&nbsp;&nbsp;{h}", styles["bullet"]))
        story.append(Spacer(1, 6))

    section_header(story, "EDUCATION")
    for ed in data["education"]:
        story.append(Paragraph(
            f"<b>{ed['studyType']}</b> — {ed['institution']} · {ed['startDate']}–{ed['endDate']} · GPA {ed['gpa']}",
            styles["edu"],
        ))

    section_header(story, "CERTIFICATIONS &amp; TRAINING")
    cert_line = " &nbsp;·&nbsp; ".join(data["certifications"])
    story.append(Paragraph(cert_line, styles["small"]))
    for group in data.get("certification_groups", []):
        story.append(Paragraph(f"<b>{group['label']} ({group['count']}):</b> {group['summary']}", styles["small"]))

    if data.get("publications"):
        section_header(story, "PUBLICATIONS")
        for pub in data["publications"]:
            story.append(Paragraph(f"{pub['authors']} <i>{pub['name']}</i>. {pub['venue']}.", styles["small"]))

    catalog = load_project_catalog()
    if profile.get("all_public_projects"):
        tier_order = {"flagship": 0, "shipped": 1}
        projects = sorted(
            (p for p in catalog.values() if p.get("visibility") == "public"),
            key=lambda p: tier_order.get(p.get("tier"), 9),
        )
    else:
        project_names = profile.get("projects")
        if project_names is None:
            project_names = data.get("selected_projects", [])
        projects = [catalog[n] for n in project_names if n in catalog]
    if projects:
        section_header(story, "PROJECTS")
        for p in projects:
            story.append(Paragraph(project_line(p), styles["project"]))

    if profile.get("show_working", False):
        working = [p for p in catalog.values() if p.get("tier") == "working"]
        if working:
            section_header(story, "CURRENTLY BUILDING")
            for p in working:
                story.append(Paragraph(f"<b>{p['name']}:</b> {p['description']}", styles["project"]))

    return story


def load_profile(name):
    if name == "full":
        return {
            "show_working": True,
            "all_public_projects": True,
            "label_override": "Geospatial Data Scientist | AI/ML | Cloud Platform Engineering",
        }
    path = os.path.join(PROFILES_DIR, f"{name}.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default="full", help="'full' or a name under scripts/profiles/")
    parser.add_argument("--out", default=None, help="Output PDF path (defaults per profile)")
    args = parser.parse_args()

    with open(RESUME_JSON, encoding="utf-8") as f:
        data = json.load(f)

    profile = load_profile(args.profile)
    output_path = args.out or (
        DEFAULT_OUTPUT if args.profile == "full"
        else os.path.join(ROOT, "assets", profile.get("output", f"Bishal_Dhungana_{args.profile}.pdf"))
    )

    doc = SimpleDocTemplate(
        output_path,
        pagesize=LETTER,
        topMargin=0.45 * inch,
        bottomMargin=0.45 * inch,
        leftMargin=0.5 * inch,
        rightMargin=0.5 * inch,
        title=f"{data['basics']['name']} — Resume",
    )
    doc.build(build_story(data, profile))
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
