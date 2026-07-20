# Final Defense Presentation

Two ways to view the same 14-slide deck: an in-browser Streamlit viewer for rehearsal, and a
downloadable PowerPoint for the actual defense (20 July 2026).

## PowerPoint

The built deck lives at [`output/Airline-Data-Platform-Final-Defense.pptx`](output/Airline-Data-Platform-Final-Defense.pptx) —
download it directly from the repo.

To regenerate it after editing content or styling:

```bash
cd presentation
npm install
node build_deck.js
```

Content and styling both live in `build_deck.js` — slide text, the color palette, and layout
helpers are all in one file. Icons are rasterized from `react-icons` on each build.

## Streamlit viewer

A navigable on-screen version of the same 14 slides, for rehearsing without opening PowerPoint:

```bash
cd presentation
pip install -r requirements.txt
streamlit run app.py
```

Or run it containerized:

```bash
cd presentation
docker compose up --build
```

Then open http://localhost:8501. The dashboard screenshot on the "Gold" slide is loaded from
`../docs/images/dashboard-screenshot.jpg`, which isn't in the container's build context — it's
skipped gracefully in the containerized version (logged as a warning), same as running `app.py`
from a checkout without that file.

Slide content lives in `app.py` as one function per slide, returning an HTML/CSS block styled
to match the PPTX palette (`0B1F3A` navy / `4CC9F0` cyan). There's no download button in the
app itself — grab the `.pptx` from `output/` directly.

## Source of truth

Both files were built from the repo's own docs: `docs/architecture/`, `docs/adr/`,
`docs/requirements/`, the root `README.md`, and `ml/README.md`. If those change, the deck
should be regenerated to match — it's not meant to drift into its own narrative.
