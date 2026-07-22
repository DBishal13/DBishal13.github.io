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
- `assets/` — images, fonts, and vendor CSS/JS.
- `inner-page.html`, `portfolio-details.html`, `old-iportfolio-index.html` — unused leftovers from the original template scaffold; not linked from the live site.

## License

MIT — see [LICENSE](LICENSE).
