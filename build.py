#!/usr/bin/env python3
"""
South Stack Studios — site build script.
Edit `site.html` (the template with __TOKEN__ placeholders), then run:  python3 build.py
Outputs (all self-contained, images/video embedded as data URIs):
  - site_staging.html     -> publish as the claude.ai staging Artifact (no <head>; the artifact wrapper adds it)
  - site_production.html   -> deploy to southstackstudios.com (full <head> with SEO meta/OG/Twitter)
  - mobile_preview.html    -> phone-frame preview artifact (embeds the site in an iframe at 390px)
  - og-image.jpg, robots.txt, sitemap.xml -> deploy alongside site_production.html at the domain root
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import base64, io, re

A = "assets"
DESC = "A nonprofit championing authentic South Asian stories in film and media — funding, mentoring, and amplifying the storytellers reshaping global film."
TITLE = "South Stack Studios — South Asian Stories in Film & Media"

def uri(img, fmt="JPEG", q=78):
    b = io.BytesIO()
    if fmt == "PNG":
        img.save(b, "PNG", optimize=True); m = "image/png"
    else:
        img.convert("RGB").save(b, "JPEG", quality=q, optimize=True, progressive=True); m = "image/jpeg"
    return f"data:{m};base64,{base64.b64encode(b.getvalue()).decode()}"

def portrait(p, h=560):
    im = Image.open(p); r = h / im.height
    return uri(im.resize((int(im.width * r), h), Image.LANCZOS))

def square(p, s=240):
    im = Image.open(p).convert("RGB"); sc = s / min(im.size)
    im = im.resize((int(im.width * sc), int(im.height * sc)), Image.LANCZOS)
    l = (im.width - s) // 2; t = (im.height - s) // 2
    return uri(im.crop((l, t, l + s, t + s)), "JPEG", 80)

def landscape(p, w=760):
    im = Image.open(p); r = w / im.width
    return uri(im.resize((w, int(im.height * r)), Image.LANCZOS), "JPEG", 74)

def video(p):
    return f"data:video/mp4;base64,{base64.b64encode(open(p, 'rb').read()).decode()}"

# --- logo mark (cropped from the wordmark) + favicon ---
logo = Image.open(f"{A}/logo.png").convert("RGBA")
mark = logo.crop((0, 0, int(logo.width * 0.165), logo.height)); mark = mark.crop(mark.getbbox())
scc = 120 / mark.height
markS = mark.resize((int(mark.width * scc), 120), Image.LANCZOS)
mark_uri = uri(markS, "PNG")
fav = mark.resize((int(mark.width * (64 / mark.height)), 64), Image.LANCZOS)
fb = io.BytesIO(); fav.save(fb, "PNG")
fav_uri = "data:image/png;base64," + base64.b64encode(fb.getvalue()).decode()

# --- full logo lockup for nav/footer (original dark wordmark, suits the light theme) ---
logo_full = Image.open(f"{A}/logo.png").convert("RGBA")
_bb = logo_full.getbbox()
if _bb: logo_full = logo_full.crop(_bb)
logo_full = logo_full.resize((int(logo_full.width * (72 / logo_full.height)), 72), Image.LANCZOS)
logo_uri = uri(logo_full, "PNG")

# --- token -> data URI map ---
toks = {"__MARK__": mark_uri, "__LOGO__": logo_uri, "__HEROVID__": video(f"{A}/hero.mp4")}
for t, f in [("__SHALINI__", "shalini.jpeg"), ("__REENA__", "reena.png"), ("__ANJANA__", "anjana.png"), ("__RAJ__", "raj.png"), ("__LATA__", "lata.jpeg")]:
    toks[t] = portrait(f"{A}/{f}")
for t, f in [("__ADV_ATUL__", "adv_atul.jpeg"), ("__ADV_COLIN__", "adv_colin.jpeg"), ("__ADV_DATTA__", "adv_datta.jpeg"),
             ("__ADV_MO__", "adv_mo.jpg"), ("__ADV_MEGHNA__", "adv_meghna.jpg"), ("__ADV_SEAN__", "adv_sean.jpeg"),
             ("__ADV_SHILPA__", "adv_shilpa.jpeg")]:
    toks[t] = square(f"{A}/{f}")
for t, f in [("__N_JUN11__", "news_jun11.jpg"), ("__N_MAY19__", "news_may19.png"), ("__N_MAY1__", "news_may1.png"),
             ("__N_APR24__", "news_apr24.png"), ("__N_DEC19__", "news_dec19.png"), ("__N_NOV12__", "news_nov12.png"),
             ("__N_OCT11__", "news_oct11.webp"), ("__N_OCT8__", "news_oct8.png"), ("__N_OCT3__", "news_oct3.png"),
             ("__N_FEB6__", "news_feb6.jpg")]:
    toks[t] = landscape(f"{A}/{f}")
for t, f in [("__FILM_HBAW__", "film_hbaw.jpg"), ("__FILM_HITL__", "film_hitl.jpg"),
             ("__FILM_HOLY__", "film_holy.jpg"), ("__FILM_BTC__", "film_breakingcode.jpg")]:
    _im = Image.open(f"{A}/{f}"); _r = 520 / _im.width
    toks[t] = uri(_im.resize((520, int(_im.height * _r)), Image.LANCZOS), "JPEG", 82)

# --- team experience logo strip (inline monochrome SVGs; Disney/Pixar as text) ---
def _svg(slug):
    s = open(f"{A}/logos/{slug}.svg", encoding="utf-8").read().strip()
    return s.replace("<svg ", '<svg class="bi" ', 1)
_brand = [("l", "google"), ("l", "youtube"), ("t", "Pixar"), ("l", "netflix"),
          ("l", "hbo"), ("t", "Disney"), ("l", "nasa"), ("l", "snapchat")]
toks["__BRANDLOGOS__"] = "".join(_svg(v) if k == "l" else f'<span class="bw">{v}</span>' for k, v in _brand)

html = open("site.html", encoding="utf-8").read()
for t, u in toks.items():
    html = html.replace(t, u)
open("site_staging.html", "w", encoding="utf-8").write(html)

# --- mobile preview: embed the built site in a phone-frame iframe ---
site_m = html.replace("</title>", "</title>\n<meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">", 1)
esc = site_m.replace("&", "&amp;").replace('"', "&quot;")
mp = open("mobile_preview.html", encoding="utf-8").read()
mp = re.sub(r'srcdoc="(?:.|\n)*?"></iframe>', 'srcdoc="' + esc + '"></iframe>', mp, count=1)
open("mobile_preview.html", "w", encoding="utf-8").write(mp)

# --- production standalone with full SEO head ---
body = re.sub(r'<title>.*?</title>\s*', '', html, count=1, flags=re.S)
body = re.sub(r'<meta name="description"[^>]*>\s*', '', body, count=1)
head = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{TITLE}</title>
<meta name="description" content="{DESC}">
<link rel="canonical" href="https://www.southstackstudios.com/">
<meta name="robots" content="index,follow,max-image-preview:large">
<meta name="theme-color" content="#0C0A0B">
<meta property="og:type" content="website">
<meta property="og:site_name" content="South Stack Studios">
<meta property="og:title" content="{TITLE}">
<meta property="og:description" content="{DESC}">
<meta property="og:url" content="https://www.southstackstudios.com/">
<meta property="og:image" content="https://www.southstackstudios.com/og-image.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{TITLE}">
<meta name="twitter:description" content="{DESC}">
<meta name="twitter:image" content="https://www.southstackstudios.com/og-image.jpg">
<link rel="icon" type="image/png" href="{fav_uri}">
<link rel="apple-touch-icon" href="{mark_uri}">
</head>
<body>
'''
open("site_production.html", "w", encoding="utf-8").write(head + body + "\n</body>\n</html>\n")

# --- robots.txt + sitemap.xml ---
open("robots.txt", "w").write("User-agent: *\nAllow: /\n\nSitemap: https://www.southstackstudios.com/sitemap.xml\n")
open("sitemap.xml", "w").write(
    '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    '  <url>\n    <loc>https://www.southstackstudios.com/</loc>\n    <changefreq>weekly</changefreq>\n    <priority>1.0</priority>\n  </url>\n</urlset>\n')

# --- branded Open Graph social image (1200x630) ---
def load_font(names, size):
    for n in names:
        for base in ["/System/Library/Fonts/Supplemental/", "/System/Library/Fonts/", "/Library/Fonts/"]:
            try: return ImageFont.truetype(base + n, size)
            except: pass
    return ImageFont.load_default()
serif = load_font(["Georgia.ttf", "Times New Roman.ttf"], 96)
serif_it = load_font(["Georgia Italic.ttf", "Georgia.ttf"], 96)
mono = load_font(["Menlo.ttc", "Courier New.ttf"], 26)
W, H = 1200, 630
og = Image.new("RGB", (W, H), (12, 10, 11))
glow = Image.new("L", (W, H), 0); gd = ImageDraw.Draw(glow)
gd.ellipse([W * 0.45, -H * 0.5, W * 1.35, H * 0.9], fill=90)
glow = glow.filter(ImageFilter.GaussianBlur(120))
og = Image.composite(Image.new("RGB", (W, H), (124, 26, 32)), og, glow)
d = ImageDraw.Draw(og)
og.paste(markS.convert("RGBA"), (80, 70), markS.convert("RGBA"))
d.text((175, 86), "SOUTH STACK STUDIOS", font=load_font(["Menlo.ttc"], 28), fill=(243, 236, 228))
d.text((80, 250), "Powering South", font=serif, fill=(243, 236, 228))
d.text((80, 360), "Asian ", font=serif, fill=(243, 236, 228))
d.text((80 + d.textlength("Asian ", font=serif), 360), "Stories", font=serif_it, fill=(233, 88, 91))
d.text((82, 520), "CREATE · CURATE · CONNECT · CULTIVATE", font=mono, fill=(228, 181, 112))
og.save("og-image.jpg", "JPEG", quality=88)

left = re.findall(r'__[A-Z0-9_]+__', html)
print("Built site_staging.html, site_production.html, mobile_preview.html, og-image.jpg, robots.txt, sitemap.xml")
print("Unreplaced tokens:", left or "none")
