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
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESUME_JSON = os.path.join(ROOT, "assets", "resume.json")
PROJECTS_JSON = os.path.join(ROOT, "assets", "projects-curated.json")
PROFILES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "profiles")
DEFAULT_OUTPUT = os.path.join(ROOT, "assets", "Bishal-Dhungana-Resume.pdf")

INK = colors.HexColor("#1a1a1a")
DIM = colors.HexColor("#5a5a5a")
ACCENT = colors.HexColor("#b8560a")
ACCENT_LINE = colors.HexColor("#e3b088")
RULE = colors.HexColor("#dddddd")

styles = {
    "name": ParagraphStyle("name", fontName="Helvetica-Bold", fontSize=24, leading=27, textColor=INK, spaceAfter=3),
    "label": ParagraphStyle("label", fontName="Helvetica", fontSize=12.5, leading=15, textColor=ACCENT, spaceAfter=8),
    "contact": ParagraphStyle("contact", fontName="Helvetica", fontSize=9.5, leading=13, textColor=DIM, spaceAfter=4),
    "section": ParagraphStyle("section", fontName="Helvetica-Bold", fontSize=12, leading=14, textColor=ACCENT, spaceBefore=16, spaceAfter=2, tracking=0.5),
    "summary": ParagraphStyle("summary", fontName="Helvetica", fontSize=9.5, textColor=INK, leading=13.5, spaceAfter=4),
    "role_title": ParagraphStyle("role_title", fontName="Helvetica-Bold", fontSize=10.5, leading=13, textColor=INK, spaceAfter=1),
    "role_meta": ParagraphStyle("role_meta", fontName="Helvetica-Oblique", fontSize=9, leading=12, textColor=DIM, spaceAfter=4),
    "bullet": ParagraphStyle("bullet", fontName="Helvetica", fontSize=9.5, textColor=INK, leading=13, leftIndent=12, bulletIndent=0, spaceAfter=3),
    "edu": ParagraphStyle("edu", fontName="Helvetica", fontSize=9.5, textColor=INK, leading=13, spaceAfter=3),
    "small": ParagraphStyle("small", fontName="Helvetica", fontSize=9, textColor=INK, leading=13, spaceAfter=2),
    "project": ParagraphStyle("project", fontName="Helvetica", fontSize=9, textColor=INK, leading=13, spaceAfter=5),
}
LINK_COLOR = "#b8560a"


def rule(color=RULE, thickness=0.75, space_before=2, space_after=10):
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


def build_story(data, profile):
    story = []
    basics = data["basics"]

    story.append(Paragraph(basics["name"], styles["name"]))
    label = profile.get("label_override", basics["label"])
    story.append(Paragraph(label, styles["label"]))

    profile_map = {p["network"]: p["url"] for p in basics.get("profiles", [])}
    contact_bits = [
        basics["email"],
        basics["location"],
        basics["website"].replace("https://", ""),
    ]
    if "LinkedIn" in profile_map:
        contact_bits.append(profile_map["LinkedIn"].replace("https://www.", "").replace("https://", ""))
    if "GitHub" in profile_map:
        contact_bits.append(profile_map["GitHub"].replace("https://", ""))
    story.append(Paragraph(" &nbsp;·&nbsp; ".join(contact_bits), styles["contact"]))
    story.append(rule(color=ACCENT_LINE, thickness=1.5, space_before=6, space_after=12))

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
        story.append(Paragraph(f"{job['title']} — {job['company']}", styles["role_title"]))
        story.append(Paragraph(f"{fmt_date(job['startDate'])} – {fmt_date(job['endDate'])}", styles["role_meta"]))
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
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
        leftMargin=0.65 * inch,
        rightMargin=0.65 * inch,
        title=f"{data['basics']['name']} — Resume",
    )
    doc.build(build_story(data, profile))
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
