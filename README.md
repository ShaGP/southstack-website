# South Stack Studios — Website Redesign

"Elevated cinematic" redesign of southstackstudios.com, rebuilt to read clearly as a **501(c)(3)
nonprofit** (for Google Ad Grants eligibility). Single-page app with hash-routed views:
Home / About / Programs / Films / Impact / Team & Advisors / News / Donate(Get Involved).
Cinematic looping video hero, dark warm palette, editorial serif + mono type. All images/video are
embedded as data URIs (self-contained).

## Live staging links (permanent — republish to the same URL keeps them current)
- Full site:      https://claude.ai/code/artifact/74034bbd-7e2a-4031-8d23-3b1159c10cf0
- Mobile preview: https://claude.ai/code/artifact/1db0c47b-9622-456f-bfc5-cd997384c760

## Files
- `site.html`            — SOURCE TEMPLATE. Edit this. Uses __TOKEN__ placeholders for images/video.
- `build.py`             — run `python3 build.py` after editing site.html to regenerate all outputs.
- `assets/`              — real source images + hero.mp4 (pulled from the live Framer site).
- `site_staging.html`    — built; publish as the claude.ai staging Artifact (no <head>; wrapper adds it).
- `site_production.html` — built; DEPLOY THIS to southstackstudios.com (full <head> + SEO/OG/meta).
- `mobile_preview.html`  — built; the phone-frame preview artifact.
- `og-image.jpg`, `robots.txt`, `sitemap.xml` — deploy at the domain root alongside the production file.

## To edit and re-publish
1. Edit `site.html`.
2. `cd` into this folder, run `python3 build.py` (needs Pillow).
3. Republish `site_staging.html` (and `mobile_preview.html`) to the SAME artifact URLs above
   (Artifact tool: pass the URL as `url` from a new conversation to update in place).

## Org facts baked in
- Legal name: Haldi Hub · 501(c)(3) · EIN 83-3636419
- Donate: https://www.zeffy.com/en-US/donation-form/help-us-do-more-3
- Contact: info@southstackstudios.com · Instagram/LinkedIn: @southstackstudios

## Status (as of 2026-08-13) — RESUME HERE TOMORROW
Nonprofit rebuild + Films page complete and published to the staging links above. Client (Shalini)
is testing and will send more feedback. She is also going to **send the logo + 3 film posters**
(via chat attachment or Google Drive) to embed.

**Done recently:**
- Rebuilt nonprofit-first for Google Ad Grants (site had been rejected for reading like a studio):
  501(c)(3) ribbon + nav tag, mission-first hero, nonprofit callouts, new Programs & Impact pages,
  giving-focused Donate page, news reframed as impact. Full technical SEO (title/desc/OG/JSON-LD/
  robots/sitemap/og-image) done earlier.
- Added a **Films** page + homepage films strip for Hanging by a Wire, Holy Curse, Breaking the Code
  (info from client deck FinalDeck.pptx). Films use designed title-card PLACEHOLDERS — awaiting posters.
- Added founder credentials + real deck-sourced impact numbers.
- Removed the 501(c)(3) callout box from the homepage Our Mission section (per client) — that info
  lives on the Donate page (facts panel + hero tax line).

### NEXT STEPS (pick up here)
1. Receive + embed the **logo** and **3 film posters** (replace title-card placeholders in the Films
   page + homepage films strip; posters go in assets/, add __TOKEN__ img tags, update build.py).
2. Apply any further client/team testing feedback.
3. Optionally add 4th film **"Humans in the Loop"** (Oscar-qualified doc, acquired by Netflix, SSS
   marketing support) — from the deck.
4. Then CUTOVER: host `site_production.html` (+ og-image/robots/sitemap/logo.png) on Netlify or
   Cloudflare Pages, repoint GoDaddy DNS from Framer, cancel Framer. Client does account/DNS steps.

### Open items for cutover
- Confirm team titles (Shalini = Co-Founder & CEO; Reena = Co-Founder; Anjana = Co-Founder & Operations;
  Raj = Co-Founder — per deck; verify).
- Verify advisor name↔photo mapping (matched by page position, not face recognition).
- 8 of 10 news cards link to Framer sub-pages (/jun11, /may19, …) that vanish when Framer is cancelled —
  migrate those press pages or repoint to external coverage.
- Consider converting hash routes (#about) to real page URLs (/about) for full per-page SEO.
- Provide a real `logo.png` at the domain root (referenced by JSON-LD structured data).

### Client's deck (source for films/team/impact)
Google Drive: FinalDeck.pptx, fileId `1bgZi3fgH9lPW57L3pe5CQ0uB4SKheE1c` (read via Drive connector
read_file_content; 4.8MB pptx too large to download as base64 through context — get poster images from
the client directly, not the deck).

## Important implementation notes
- Router `go()` MUST run the reveal step (add `.in` to `.reveal`) BEFORE `history.replaceState`, and wrap
  replaceState in try/catch. claude.ai serves artifacts in a sandboxed iframe where replaceState throws;
  if it ran first, pages rendered blank. (Fixed — keep this ordering.)
- External links (Donate/news/socials) go through a JS handler that calls `window.open` with a fallback,
  so they work on the real site; the claude.ai sandbox may still block new tabs in preview (expected).
- The cinematic dark theme is a deliberate single-theme design (no light-mode inversion).
