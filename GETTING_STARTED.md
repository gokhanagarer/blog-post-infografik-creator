# Getting started

A step-by-step guide. Aim: render three branded infographics for a blog post in your terminal within 5 minutes, with zero API keys.

If anything breaks, jump to [Troubleshooting](#troubleshooting).

---

## 0. Prerequisites

You need:
- **Python 3.10+** (`python3 --version`)
- **git** (`git --version`)
- A Unix-like shell (macOS Terminal, Linux, WSL on Windows)

That's it. The placeholder backend uses only Pillow — no extra system libraries.

---

## 1. Clone and run the demo

```bash
git clone https://github.com/gokhanagarer/blog-post-infografik-creator.git
cd blog-post-infografik-creator
make demo
```

What just happened:
- `make demo` created `.venv/`, installed `Pillow`, `requests`, `python-dotenv`
- Loaded the bundled `assets/demo-brand/` (Acme demo brand: blue/orange palette + simple SVG logo)
- Rendered 3 placeholder infographics from `examples/prompts.json` (hero / info / photo)
- Applied brand post-processing (colour boost, vignette by image type, logo overlay top-right)
- Wrote `.jpg` artifacts to `output/`

Open the three files in `output/` — you'll see the same prompt text rendered as a placeholder image, branded with the Acme palette and logo:
- `open-science-hero.jpg`
- `data-pipeline-info.jpg`
- `analytics-photo.jpg`

---

## 2. Use a real image generator

The placeholder backend is fine for testing the pipeline, but you'll want real AI-generated images for production. Two options.

### Option A — Pollinations.ai (free, no key, ~1 image / 5 s)

```bash
cp .env.example .env
# In .env, set:
#   IMAGE_BACKEND=pollinations
```

Re-run:

```bash
make demo
```

The same three prompts now produce real Flux-generated images instead of placeholders.

### Option B — Google Gemini (paid, faster, higher quality)

1. Get a key at https://aistudio.google.com/app/apikey
2. In `.env`:
   ```
   IMAGE_BACKEND=gemini
   GEMINI_API_KEY=AIza...
   ```
3. Install the Google client:
   ```bash
   .venv/bin/pip install google-genai
   ```
4. Re-run `make demo`.

---

## 3. Bring your own brand

The bundled demo brand is the **Acme** placeholder. To use your own:

1. Create a folder somewhere — say `~/my-brand/`
2. Drop in your brand colors and logo:
   ```
   ~/my-brand/
   ├── brand.json
   └── logo.png   (or logo.svg, see below)
   ```
3. `brand.json` looks like:
   ```json
   {
     "name": "YourBrand",
     "colors": {
       "primary_blue":      [0, 96, 217],
       "growth_green":      [154, 202, 60],
       "tech_cyan":         [109, 207, 246],
       "background_grey":   [246, 246, 246],
       "highlight_orange":  [255, 175, 0],
       "pure_white":        [255, 255, 255]
     },
     "logo": "logo.png"
   }
   ```
4. Run with your brand:
   ```bash
   .venv/bin/python -m src.main \
     --brand ~/my-brand/brand.json \
     --batch examples/prompts.json \
     --outdir output/
   ```

### SVG vs PNG logos

PNG logos work out of the box. SVG logos give crisper output at any size but require the native `libcairo` library:

```bash
# macOS
brew install cairo
# Debian/Ubuntu
sudo apt install libcairo2
```

Then `pip install cairosvg` (it's in `requirements-dev.txt`).

The pipeline degrades gracefully: if `logo: "logo.svg"` is set but `libcairo` is missing, it looks for a sibling `logo.png` instead.

---

## 4. Generate from your own prompts

Single image:

```bash
.venv/bin/python -m src.main \
  "your prompt here" \
  output/my-image.jpg \
  --type hero
```

`--type` controls post-processing intensity:
- `hero` — heavy colour boost + vignette (most dramatic)
- `info` — minimal processing (preserves infographic clarity)
- `photo` — natural boost + soft vignette

Batch mode — write a JSON list:

```json
[
  { "prompt": "first image prompt", "filename": "first.jpg",  "type": "hero" },
  { "prompt": "second prompt",      "filename": "second.jpg", "type": "info" }
]
```

Then:

```bash
.venv/bin/python -m src.main --batch your-prompts.json --outdir output/
```

---

## 5. Tuning post-processing

The defaults are in `src/postprocess.py`:

```python
_PROFILES = {
    "hero":  {"color_boost": 1.30, "contrast_boost": 1.10, "vignette": 0.20},
    "info":  {"color_boost": 1.10, "contrast_boost": 1.05, "vignette": 0.00},
    "photo": {"color_boost": 1.15, "contrast_boost": 1.05, "vignette": 0.15},
}
```

Edit those numbers to taste. `make test` keeps a regression suite that exercises the pipeline against the demo fixtures.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `make: command not found` | `make` not installed | macOS: `xcode-select --install`. Linux: `sudo apt install build-essential` |
| `OSError: no library called "cairo-2" was found` | SVG logo set, `libcairo` not installed | Switch logo to PNG, or `brew install cairo` |
| Pollinations returns `tiny response (X bytes)` | Free-tier rate limit hit | The backend retries 3× with backoff; if persistent, drop concurrency |
| Gemini returns no image part | Prompt rejected (safety filter) | Rephrase the prompt; remove anything that might trigger Google's filters |
| Logo too big / too small on output | Default size is 12% of image width | Pass `--logo-size 8` (smaller) or `--logo-size 16` (bigger) when running `src.main` directly |
| Vignette too dark | `intensity` too high for your image | Edit `_PROFILES` in `src/postprocess.py` |

---

## Where to look next

- `n8n/` — the same pipeline as an importable n8n workflow with a node-by-node walkthrough
- `src/postprocess.py` — colour boost, vignette, logo overlay; pure-Pillow, no external deps
- `src/generators.py` — pluggable backends; add a new one by implementing `Generator.generate(prompt, output_path, *, width, height)`
