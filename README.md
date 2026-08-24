# dbishal13.github.io

Source for my personal portfolio site: **https://dbishal13.github.io**

A single static page (`index.html`) — plain HTML/CSS/JS, no build step, no framework. Hosted on GitHub Pages. Visitor analytics via [GoatCounter](https://gisus.goatcounter.com).

## Running locally

Serve the directory rather than opening `index.html` directly via `file://`, so relative paths and scripts behave the same as in production:

```
python3 -m http.server 8000
```

Then open http://localhost:8000.

## Structure

- `index.html` — the live site.
- `assets/resume.json` — single, ever-growing source of truth for resume content (summary, work history, education, certifications, skills). New bootcamps/certs/skills get added here first. Mirrored by hand into the Experience/Skills/Credentials sections of `index.html`.
- `assets/projects-curated.json` — single source of truth for the Builds section: flagship (full cards), shipped (compact grid), and working (private, generic teaser) projects. Edit this to add/reorder/re-tier projects; `index.html` renders it client-side. Also consumed by `scripts/generate_resume.py`'s Projects section and by `DBishal13/dbishal13`'s profile-README script.
- `assets/projects.json` — auto-generated daily by `.github/workflows/update-projects.yml`; a fallback feed for public repos not yet added to `projects-curated.json`.
- `scripts/generate_resume.py` — renders `resume.json` (+ a profile) into a resume PDF. Needs `pip install -r scripts/requirements.txt` (a local `.venv` is recommended).
- `scripts/profiles/*.json` — per-role-family tailoring configs (which skill groups, which work-highlight bullets by index, which projects) for the 2-page application resumes kept in `DBishal13/dbishal13`'s `Resume/` folder.

## Running the resume generator

```
python3 -m venv .venv
.venv/bin/pip install -r scripts/requirements.txt

# The comprehensive "portfolio resume" — every skill, every highlight, every
# public project, no page limit. This is what the portfolio site links to.
.venv/bin/python scripts/generate_resume.py --profile full

# A tailored ~2-page resume for one role family, output wherever you like:
.venv/bin/python scripts/generate_resume.py --profile ai --out /path/to/Bishal_Dhungana_AI.pdf
# other profiles: general, dataengineer, ge, geo
```

To add a new tailored profile, drop a new `scripts/profiles/<name>.json` (see the existing ones for the shape) and run with `--profile <name>`.

## License

MIT — see [LICENSE](LICENSE).
