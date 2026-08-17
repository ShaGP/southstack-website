#!/usr/bin/env python3
"""
One-time un-bundler: turns the single-file SPA (site.html) into a clean, editable
multi-page static site in ../southstack-site/ — plain HTML files, shared CSS/JS,
real (optimized) image files. No ongoing build needed after this: edit the .html directly.
"""
import re, os, shutil, io as _io, json
from datetime import datetime, date
from PIL import Image

SITE = "https://www.southstackstudios.com"
BUILD_DATE = date.today().isoformat()

SRC = "site.html"
OUT = "../southstack-site"
A = "assets"

# ---------- folders ----------
for d in ["", "assets/css", "assets/js", "assets/img", "assets/img/team",
          "assets/img/advisors", "assets/img/films", "assets/img/news", "assets/video"]:
    os.makedirs(os.path.join(OUT, d), exist_ok=True)

# ---------- image optimization (save real files, not data URIs) ----------
def save_jpg(src, dst, w=None, h=None, q=80):
    im = Image.open(src).convert("RGB")
    if h: r = h / im.height; im = im.resize((int(im.width * r), h), Image.LANCZOS)
    elif w: r = w / im.width; im = im.resize((w, int(im.height * r)), Image.LANCZOS)
    im.save(os.path.join(OUT, dst), "JPEG", quality=q, optimize=True, progressive=True)

def save_png(src, dst, h=None):
    im = Image.open(src).convert("RGBA")
    bb = im.getbbox()
    if bb: im = im.crop(bb)
    if h: r = h / im.height; im = im.resize((int(im.width * r), h), Image.LANCZOS)
    im.save(os.path.join(OUT, dst), "PNG", optimize=True)

# logo (light-theme lockup, dark wordmark) + favicon (icon only)
save_png(f"{A}/logo.png", "assets/img/logo.png", h=72)
_logo = Image.open(f"{A}/logo.png").convert("RGBA")
_mark = _logo.crop((0, 0, int(_logo.width * 0.165), _logo.height)); _mark = _mark.crop(_mark.getbbox())
_mark.resize((64, 64), Image.LANCZOS).save(os.path.join(OUT, "assets/img/favicon.png"), "PNG")
shutil.copy("og-image.jpg", os.path.join(OUT, "assets/img/og-image.jpg"))
shutil.copy(f"{A}/hero.mp4", os.path.join(OUT, "assets/video/hero.mp4"))

# team + advisors + films + news
for src, dst in [("shalini.jpeg", "team/shalini.jpg"), ("reena.png", "team/reena.jpg"),
                 ("anjana.png", "team/anjana.jpg"), ("raj.png", "team/raj.jpg"), ("lata.jpeg", "team/lata.jpg")]:
    save_jpg(f"{A}/{src}", f"assets/img/{dst}", h=560)
for src, dst in [("adv_atul.jpeg", "atul"), ("adv_datta.jpeg", "datta"), ("adv_mo.jpg", "mo"),
                 ("adv_meghna.jpg", "meghna"), ("adv_sean.jpeg", "sean"), ("adv_shilpa.jpeg", "shilpa")]:
    save_jpg(f"{A}/{src}", f"assets/img/advisors/{dst}.jpg", h=300)
for src, dst in [("film_hbaw.jpg", "hanging-by-a-wire"), ("film_hitl.jpg", "humans-in-the-loop"),
                 ("film_holy.jpg", "holy-curse"), ("film_breakingcode.jpg", "breaking-the-code")]:
    save_jpg(f"{A}/{src}", f"assets/img/films/{dst}.jpg", w=520, q=82)
NEWS_IMG = {"jun11": "news_jun11.jpg", "may19": "news_may19.png", "may1": "news_may1.png",
            "apr24": "news_apr24.png", "dec19": "news_dec19.png", "nov12": "news_nov12.png",
            "oct11": "news_oct11.webp", "oct8": "news_oct8.png", "oct3": "news_oct3.png", "feb6": "news_feb6.jpg"}
for key, src in NEWS_IMG.items():
    save_jpg(f"{A}/{src}", f"assets/img/news/{key}.jpg", w=760, q=76)

# token -> real path
TOK = {
    "__LOGO__": "assets/img/logo.png",
    "__HEROVID__": "assets/video/hero.mp4",
    "__SHALINI__": "assets/img/team/shalini.jpg", "__REENA__": "assets/img/team/reena.jpg",
    "__ANJANA__": "assets/img/team/anjana.jpg", "__RAJ__": "assets/img/team/raj.jpg",
    "__LATA__": "assets/img/team/lata.jpg",
    "__ADV_ATUL__": "assets/img/advisors/atul.jpg", "__ADV_DATTA__": "assets/img/advisors/datta.jpg",
    "__ADV_MO__": "assets/img/advisors/mo.jpg", "__ADV_MEGHNA__": "assets/img/advisors/meghna.jpg",
    "__ADV_SEAN__": "assets/img/advisors/sean.jpg", "__ADV_SHILPA__": "assets/img/advisors/shilpa.jpg",
    "__FILM_HBAW__": "assets/img/films/hanging-by-a-wire.jpg", "__FILM_HITL__": "assets/img/films/humans-in-the-loop.jpg",
    "__FILM_HOLY__": "assets/img/films/holy-curse.jpg", "__FILM_BTC__": "assets/img/films/breaking-the-code.jpg",
    "__N_JUN11__": "assets/img/news/jun11.jpg", "__N_MAY19__": "assets/img/news/may19.jpg",
    "__N_MAY1__": "assets/img/news/may1.jpg", "__N_APR24__": "assets/img/news/apr24.jpg",
    "__N_DEC19__": "assets/img/news/dec19.jpg", "__N_NOV12__": "assets/img/news/nov12.jpg",
    "__N_OCT11__": "assets/img/news/oct11.jpg", "__N_OCT8__": "assets/img/news/oct8.jpg",
    "__N_OCT3__": "assets/img/news/oct3.jpg", "__N_FEB6__": "assets/img/news/feb6.jpg",
}
# brand logo strip -> inline svgs (recolored via CSS)
def _svg(slug):
    s = open(f"{A}/logos/{slug}.svg", encoding="utf-8").read().strip()
    return s.replace("<svg ", '<svg class="bi" ', 1)
_brand = [("l", "google"), ("l", "youtube"), ("t", "Pixar"), ("l", "netflix"),
          ("l", "hbo"), ("t", "Disney"), ("l", "nasa"), ("l", "snapchat")]
TOK["__BRANDLOGOS__"] = "".join(_svg(v) if k == "l" else f'<span class="bw">{v}</span>' for k, v in _brand)

# ---------- read source ----------
html = open(SRC, encoding="utf-8").read()

# extract <style>...</style>
style = re.search(r"<style>(.*?)</style>", html, re.S).group(1)
# hero animation ran on .view.active; make it run on plain page load
style = style.replace(".view.active ", "").replace(".view{display:none}.view.active{display:block}", ".view{display:block}")
# progressive enhancement: only hide .reveal when JS is present (content always visible without JS)
style = style.replace(".reveal{opacity:0", ".js .reveal{opacity:0")
style = style.replace(".reveal.in{opacity:1", ".js .reveal.in{opacity:1")
style = style.replace("prefers-reduced-motion:reduce){.reveal{", "prefers-reduced-motion:reduce){.js .reveal{")
style = style.replace(".stat[data-go]", ".stat[href]")  # clickable impact tiles use href now
style += """
  /* news article pages */
  .article-hero{width:100%;max-height:540px;object-fit:cover;border:1px solid var(--line);margin-top:10px}
  .article-body{max-width:68ch;margin:36px auto 0;color:var(--dim);font-size:1.1rem;line-height:1.85}
  .article-body p{margin:0 0 22px}
  .article-body a{color:var(--crimson)}
  /* FAQ (donate page) */
  .faq{display:flex;flex-direction:column;gap:1px;background:var(--line);border:1px solid var(--line);margin-top:44px}
  .faq-item{background:var(--ink);padding:clamp(22px,3vw,32px)}
  .faq-item h3{font-size:clamp(1.15rem,2vw,1.4rem);color:var(--ivory)}
  .faq-item p{color:var(--dim);margin-top:10px;line-height:1.65;max-width:74ch;font-size:1rem}
"""
open(os.path.join(OUT, "assets/css/style.css"), "w", encoding="utf-8").write(style.strip() + "\n")

# extract header + footer + jsonld
header = re.search(r"<header>.*?</header>", html, re.S).group(0)
footer = re.search(r"<footer>.*?</footer>", html, re.S).group(0)
# the logo/brand was a <div> (SPA relied on JS to navigate) -> make it a real <a> link
def brand_to_anchor(s):
    return re.sub(r'<div class="brand"([^>]*)>((?:(?!</div>).)*)</div>',
                  r'<a class="brand"\1>\2</a>', s, flags=re.S)
header = brand_to_anchor(header)
footer = brand_to_anchor(footer)
# ---------- structured data (JSON-LD) for Google + AI answer engines ----------
ORG = {
    "@type": ["NGO", "Organization"], "@id": SITE + "/#org",
    "name": "South Stack Studios", "legalName": "Haldi Hub",
    "url": SITE + "/", "logo": SITE + "/assets/img/logo.png", "image": SITE + "/assets/img/og-image.jpg",
    "slogan": "Create. Curate. Connect. Cultivate.",
    "description": "South Stack Studios (legal name Haldi Hub) is a registered 501(c)(3) nonprofit that funds, mentors, and champions emerging South Asian filmmakers, writers, and artists, bringing authentic stories to global audiences.",
    "nonprofitStatus": "Nonprofit501c3", "taxID": "83-3636419", "areaServed": "Worldwide",
    "email": "info@southstackstudios.com",
    "founder": [{"@type": "Person", "name": "Shalini Govil-Pai", "jobTitle": "Co-Founder & Board Member"},
                {"@type": "Person", "name": "Reena Mehta", "jobTitle": "Co-Founder & President"},
                {"@type": "Person", "name": "Anjana Gopakumar", "jobTitle": "Co-Founder & Operations"},
                {"@type": "Person", "name": "Raj Pai", "jobTitle": "Co-Founder & Board Member"}],
    "knowsAbout": ["South Asian cinema", "Film grants", "Filmmaker mentorship", "Storytelling", "Media technology", "South Asian diaspora"],
    "sameAs": ["https://www.instagram.com/southstackstudios", "https://www.linkedin.com/company/southstackstudios/"],
}
WEBSITE = {"@type": "WebSite", "@id": SITE + "/#website", "name": "South Stack Studios",
           "url": SITE + "/", "publisher": {"@id": SITE + "/#org"}, "inLanguage": "en"}
CRUMB_NAME = {"about": "About", "programs": "Programs", "films": "Films", "impact": "Impact",
              "team": "Team & Advisors", "news": "In the News", "involved": "Donate & Get Involved"}
FILMS_LD = [
    {"name": "Hanging by a Wire", "director": "Mohamed Naqvi", "genre": ["Documentary"], "tt": "tt37405791", "img": "hanging-by-a-wire"},
    {"name": "Humans in the Loop", "director": "Aranya Sahay", "genre": ["Drama"], "tt": "tt33581992", "img": "humans-in-the-loop"},
    {"name": "Holy Curse", "genre": ["Short", "Drama"], "tt": "tt31778421", "img": "holy-curse"},
    {"name": "Breaking the Code", "director": "Ben Rekhi", "genre": ["Documentary", "Biography"], "tt": "tt40868336", "img": "breaking-the-code"},
]
def _movie(f):
    m = {"@type": "Movie", "name": f["name"], "genre": f["genre"],
         "image": SITE + "/assets/img/films/" + f["img"] + ".jpg",
         "sameAs": "https://www.imdb.com/title/" + f["tt"] + "/", "productionCompany": {"@id": SITE + "/#org"}}
    if f.get("director"): m["director"] = {"@type": "Person", "name": f["director"]}
    return m
TEAM_LD = [
    {"name": "Shalini Govil-Pai", "job": "Co-Founder & Board Member", "sameAs": "https://www.linkedin.com/in/shalinigovilpai/"},
    {"name": "Reena Mehta", "job": "Co-Founder & President"},
    {"name": "Anjana Gopakumar", "job": "Co-Founder & Operations"},
    {"name": "Raj Pai", "job": "Co-Founder & Board Member"},
    {"name": "Lata Krishnan", "job": "Board Member", "sameAs": "https://aif.org/people/lata-krishnan/"},
]
def _person(p):
    d = {"@type": "Person", "name": p["name"], "jobTitle": p["job"], "worksFor": {"@id": SITE + "/#org"}}
    if p.get("sameAs"): d["sameAs"] = p["sameAs"]
    return d
FAQ_QA = [
    ("Is my donation to South Stack Studios tax-deductible?",
     "Yes. South Stack Studios (legal name Haldi Hub) is a registered 501(c)(3) nonprofit, EIN 83-3636419. Donations are tax-deductible to the fullest extent allowed by law."),
    ("Where does my gift go?",
     "Gifts fund grants and production, mentorship, festival and distribution pathways, and community programs for emerging South Asian filmmakers, writers, and artists."),
    ("Can I give through a donor-advised fund (DAF)?",
     "Yes. You can recommend a grant to South Stack Studios (Haldi Hub, EIN 83-3636419) directly through your donor-advised fund. For gifts of stock or wire transfers, email info@southstackstudios.com."),
    ("What does South Stack Studios do?",
     "South Stack Studios is a nonprofit that funds, mentors, and champions emerging South Asian storytellers in film and media, bringing authentic, original stories to global audiences."),
]
FAQ_LD = {"@type": "FAQPage", "mainEntity": [
    {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ_QA]}

def jsonld_for(view, url):
    graph = [ORG, WEBSITE]
    if view != "home":
        graph.append({"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": CRUMB_NAME[view], "item": SITE + "/" + url}]})
    if view == "films":
        graph.append({"@type": "ItemList", "name": "South Stack Studios Films",
                      "itemListElement": [{"@type": "ListItem", "position": i + 1, "item": _movie(f)} for i, f in enumerate(FILMS_LD)]})
    if view == "team":
        graph.append({"@type": "ItemList", "name": "South Stack Studios Team & Advisors",
                      "itemListElement": [{"@type": "ListItem", "position": i + 1, "item": _person(p)} for i, p in enumerate(TEAM_LD)]})
    if view == "involved":
        graph.append(FAQ_LD)
    return '<script type="application/ld+json">\n' + json.dumps({"@context": "https://schema.org", "@graph": graph}, indent=2) + '\n</script>'

# visible FAQ block appended to the Get Involved page (matches the FAQ schema)
FAQ_HTML = ('<section class="band"><div class="wrap sec">'
            '<div class="reveal"><span class="eyebrow dim">Frequently asked</span>'
            '<h2 style="font-size:clamp(1.8rem,4vw,2.8rem);max-width:16ch;margin-top:12px">Giving questions, answered.</h2></div>'
            '<div class="faq reveal">'
            + "".join(f'<div class="faq-item"><h3>{q}</h3><p>{a}</p></div>' for q, a in FAQ_QA)
            + '</div></div></section>')

# extract each view's inner content
main_html = re.search(r"<main>(.*?)</main>", html, re.S).group(1)
starts = [(m.group(1), m.end()) for m in re.finditer(r'<section class="view" id="v-(\w+)">', main_html)]
offs = [m.start() for m in re.finditer(r'<section class="view" id="v-\w+">', main_html)] + [len(main_html)]
views = {}
for i, (name, e) in enumerate(starts):
    inner = main_html[e:offs[i + 1]].rstrip()
    inner = re.sub(r"(?:<!--[^<]*?-->\s*)+$", "", inner).rstrip()  # [^<] so a comment can't span across tags
    if inner.endswith("</section>"):
        inner = inner[:-len("</section>")].rstrip()
    views[name] = inner

# ---------- static news cards (were JS-injected) ----------
# date, headline, tag, imgkey, slug(local page) OR None, external_url OR None, lead paragraph
NEWS = [
    ("Jun 11, 2026", "South Stack Studios celebrates Tribeca success while exploring the future of storytelling and innovation", "Tribeca", "jun11", "news-tribeca-2026", None,
     "South Stack Studios marked a milestone at the Tribeca Festival, celebrating the storytellers we champion while convening conversations on where South Asian storytelling and technology go next."),
    ("May 19, 2026", "Co-founder Anjana Gopakumar joins a main-stage panel at the Cannes Film Festival", "Cannes", "may19", "news-cannes-2026", None,
     "At the Cannes Film Festival, co-founder Anjana Gopakumar took the main stage to discuss the global appetite for authentic South Asian stories and the role of nonprofits in getting them made."),
    ("May 1, 2026", "“Storytelling in the Age of AI” — the Media &amp; Entertainment track at TIECon 2026", "TIECon", "may1", "news-tiecon-2026", None,
     "South Stack Studios led the Media &amp; Entertainment track at TIECon 2026 with a session on “Storytelling in the Age of AI,” exploring how new tools expand access for emerging creators."),
    ("Apr 24, 2026", "“From Pitch to Premiere” masterclass at the Indian Film Festival of Los Angeles", "IFFLA", "apr24", "news-iffla-masterclass", None,
     "Our “From Pitch to Premiere” masterclass at the Indian Film Festival of Los Angeles gave emerging South Asian filmmakers a practical roadmap — from developing a pitch to landing on a festival stage."),
    ("Dec 19, 2025", "“Hanging By a Wire” premieres in the Competition category at Sundance 2026", "Sundance", "dec19", "news-hanging-by-a-wire-sundance", None,
     "A film we championed, “Hanging by a Wire,” was selected for the Competition category at Sundance 2026 — a significant milestone on its journey to global audiences."),
    ("Nov 12, 2025", "South Stack Studios joins Oscar-qualified short “Holy Curse” as Executive Producers", "Executive Producers", "nov12", "news-holy-curse-ep", None,
     "South Stack Studios came aboard the Oscar-qualified short “Holy Curse” as Executive Producers, backing a bold South Asian voice through its awards run."),
    ("Oct 11, 2025", "Principal Founders represent South Stack Studios at the All That Glitters Diwali Ball in NYC", "New York Times", "oct11", None, "https://www.nytimes.com/2025/10/12/style/diwali-ball-new-york-priyanka-chopra-nora-fatehi.html", None),
    ("Oct 8, 2025", "Reena Mehta joins as a panelist at the Tasveer Festival in Seattle", "Tasveer", "oct8", "news-tasveer-seattle", None,
     "Co-founder Reena Mehta joined a panel at the Tasveer Festival in Seattle, connecting with the South Asian creative community and the festival partners who help our storytellers find audiences."),
    ("Oct 3, 2025", "Tasveer Film Market: connecting South Asian stories with global executives", "Deadline", "oct3", None, "https://deadline.com/2025/10/tasveer-film-market-2025-selected-projects-1236569026/", None),
    ("Feb 6, 2025", "South Stack Studios celebrates the Sundance Film Festival premiere of “Hanging by a Wire”", "Sundance", "feb6", "news-hanging-by-a-wire-premiere", None,
     "South Stack Studios celebrated the Sundance Film Festival premiere of “Hanging by a Wire,” a proud moment for a project and a team we backed from early on."),
]
def news_link(n):
    d, t, tag, key, slug, ext, lead = n
    return (ext, "") if ext else (f"{slug}.html", "")  # (href, target/rel) built in card
def news_card(n):
    d, t, tag, key, slug, ext, lead = n
    if ext:
        href, attrs = ext, ' target="_blank" rel="noopener"'; go = "Read ↗"
    else:
        href, attrs = f"{slug}.html", ""; go = "Read more →"
    return (f'<a class="ncard" href="{href}"{attrs}>'
            f'<div class="thumb"><img src="assets/img/news/{key}.jpg" alt="{t}" loading="lazy"></div>'
            f'<div class="body"><span class="date">{d}</span><span class="headline">{t}</span><span class="go">{go}</span></div></a>')
all_news = "".join(news_card(n) for n in NEWS)
feat_news = "".join(news_card(n) for n in NEWS[:3])

# ---------- pages ----------
PAGES = {  # view-name : (filename, url-path, <title>, meta description)
    "home": ("index.html", "", "South Stack Studios — South Asian Stories in Film & Media",
             "A 501(c)(3) nonprofit that funds, mentors, and champions emerging South Asian filmmakers, writers, and artists — bringing authentic stories to the world."),
    "about": ("about.html", "about.html", "About — 501(c)(3) Nonprofit — South Stack Studios",
              "South Stack Studios (Haldi Hub) is a registered 501(c)(3) nonprofit opening doors for emerging South Asian storytellers in film and media."),
    "programs": ("programs.html", "programs.html", "Programs — Grants, Mentorship & More — South Stack Studios",
                 "How South Stack Studios invests in South Asian storytellers: funding, mentorship, distribution, and community programs."),
    "films": ("films.html", "films.html", "Our Films — South Stack Studios",
              "The South Asian films South Stack Studios has funded and championed — from Sundance and Tribeca to Oscar qualification."),
    "impact": ("impact.html", "impact.html", "Our Impact — South Stack Studios",
               "What your support makes possible: the storytellers and projects South Stack Studios has lifted onto the world's stages."),
    "team": ("team.html", "team.html", "Our Team & Advisors — South Stack Studios",
             "The people behind South Stack Studios — a founding team and advisory circle across film, media, and Silicon Valley."),
    "news": ("news.html", "news.html", "In the News — South Stack Studios",
             "South Stack Studios in the news — festival milestones and press coverage from Sundance, Cannes, Tribeca, and beyond."),
    "involved": ("get-involved.html", "get-involved.html", "Donate & Get Involved — South Stack Studios",
                 "Support South Asian storytellers. Your tax-deductible gift to South Stack Studios (501(c)(3), EIN 83-3636419) funds grants, mentorship, and festival pathways."),
}
GO2FILE = {v: PAGES[v][0] for v in PAGES}
GO2FILE["involved"] = "get-involved.html"

def resolve(fragment, current=None):
    # data-go="x" -> href="file.html"; mark current nav link active
    def repl(m):
        go = m.group(1)
        f = GO2FILE.get(go, "index.html")
        on = ' class="on"' if go == current else ""
        return f'href="{f}"{on}'
    frag = re.sub(r'data-go="(\w+)"', repl, fragment)
    for tok, path in TOK.items():
        frag = frag.replace(tok, path)
    return frag

TEMPLATE = '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="https://www.southstackstudios.com/{url}">
<meta name="robots" content="index,follow,max-image-preview:large">
<meta name="theme-color" content="#FBF6EF">
<meta property="og:type" content="website">
<meta property="og:site_name" content="South Stack Studios">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="https://www.southstackstudios.com/{url}">
<meta property="og:image" content="https://www.southstackstudios.com/assets/img/og-image.jpg">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}"><meta name="twitter:description" content="{desc}">
<link rel="icon" type="image/png" href="assets/img/favicon.png">
<link rel="stylesheet" href="assets/css/style.css">
<script>document.documentElement.classList.add('js');</script>
{jsonld}
<!-- Google Analytics 4 — required for Ad Grants conversion tracking. Replace G-XXXXXXXXXX with your Measurement ID and uncomment:
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-XXXXXXXXXX');</script>
-->
</head>
<body>
<div class="glow" aria-hidden="true"></div>
<canvas class="grain" aria-hidden="true"></canvas>
{header}
<main>
{content}
</main>
{footer}
<script src="assets/js/main.js"></script>
</body>
</html>
'''

hdr_tpl = header  # will resolve per-page for active state
ftr = resolve(footer)

for view, (fname, url, title, desc) in PAGES.items():
    content = views[view]
    # inject static news cards where the SPA used JS containers
    content = content.replace('<div class="newsgrid reveal" id="home-news"></div>', f'<div class="newsgrid reveal">{feat_news}</div>')
    content = content.replace('<div class="newsgrid reveal" id="impact-news"></div>', f'<div class="newsgrid reveal">{feat_news}</div>')
    content = content.replace('<div class="newsgrid reveal" id="all-news"></div>', f'<div class="newsgrid reveal">{all_news}</div>')
    if view == "involved":
        content = content + "\n" + FAQ_HTML
    page = TEMPLATE.format(
        title=title, desc=desc, url=url,
        jsonld=jsonld_for(view, url),
        header=resolve(hdr_tpl, current=view),
        content=resolve(content),
        footer=ftr,
    )
    open(os.path.join(OUT, fname), "w", encoding="utf-8").write(page)

# ---------- local news article pages (internal items only) ----------
ART_CONTENT = '''  <div class="wrap page">
    <div class="page-head reveal"><span class="eyebrow">{date} &middot; {tag}</span><h1>{headline}</h1></div>
  </div>
  <div class="wrap">
    <img class="article-hero reveal" src="assets/img/news/{key}.jpg" alt="{alt}">
    <div class="article-body reveal">
      <p>{lead}</p>
      <p style="margin-top:8px"><a href="news.html">&larr; Back to all news</a></p>
    </div>
  </div>'''
n_articles = 0
for n in NEWS:
    d, t, tag, key, slug, ext, lead = n
    if not slug:  # external (NYT/Deadline) — the card links out, no local page
        continue
    alt = t.replace('"', "")
    plain = re.sub(r"<[^>]+>", "", t)
    title = plain + " — South Stack Studios"
    try:
        iso = datetime.strptime(d, "%b %d, %Y").strftime("%Y-%m-%d")
    except ValueError:
        iso = None
    art = {"@type": "NewsArticle", "headline": plain,
           "image": SITE + "/assets/img/news/" + key + ".jpg",
           "description": lead, "articleBody": lead,
           "author": {"@id": SITE + "/#org"}, "publisher": {"@id": SITE + "/#org"},
           "mainEntityOfPage": SITE + "/" + slug + ".html"}
    if iso:
        art["datePublished"] = iso
    art_ld = ('<script type="application/ld+json">\n'
              + json.dumps({"@context": "https://schema.org", "@graph": [ORG, art]}, indent=2)
              + '\n</script>')
    content = ART_CONTENT.format(date=d, tag=tag, headline=t, key=key, alt=alt, lead=lead)
    page = TEMPLATE.format(title=title, desc=lead, url=f"{slug}.html", jsonld=art_ld,
                           header=resolve(hdr_tpl), content=content, footer=ftr)
    open(os.path.join(OUT, f"{slug}.html"), "w", encoding="utf-8").write(page)
    n_articles += 1
print("News article pages:", n_articles)

# ---------- main.js (menu, reveal-on-scroll, grain) ----------
MAIN_JS = '''// South Stack Studios — shared page script
(function(){
  var d=document;
  var header=d.querySelector('header');
  var mt=d.querySelector('.menu-toggle');
  if(mt&&header) mt.addEventListener('click',function(){header.classList.toggle('open');});

  // clickable impact tiles (a <div> carrying an href) navigate on click
  d.addEventListener('click',function(e){
    var s=e.target.closest('.stat[href]');
    if(s){location.href=s.getAttribute('href');}
  });

  // reveal-on-scroll (content is already visible without JS; this just adds a fade)
  var reveals=d.querySelectorAll('.reveal');
  if(!('IntersectionObserver' in window)){
    reveals.forEach(function(el){el.classList.add('in');});
  } else {
    var io=new IntersectionObserver(function(es){es.forEach(function(e){
      if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target);}});},
      {threshold:.12,rootMargin:'0px 0px -8% 0px'});
    reveals.forEach(function(el){io.observe(el);});
    // safety backstop: never leave near/above-the-fold content hidden
    window.addEventListener('load',function(){setTimeout(function(){
      d.querySelectorAll('.reveal:not(.in)').forEach(function(el){
        if(el.getBoundingClientRect().top < window.innerHeight*1.15) el.classList.add('in');
      });},350);});
  }

  // film-grain texture
  var c=d.querySelector('.grain');
  if(c){var x=c.getContext('2d');
    var w=c.width=Math.min(window.innerWidth,900),h=c.height=Math.min(window.innerHeight,900);
    var img=x.createImageData(w,h),dt=img.data;
    for(var i=0;i<dt.length;i+=4){var v=(Math.random()*255)|0;dt[i]=dt[i+1]=dt[i+2]=v;dt[i+3]=255;}
    x.putImageData(img,0,0);c.style.width='100vw';c.style.height='100vh';}
})();
'''
open(os.path.join(OUT, "assets/js/main.js"), "w", encoding="utf-8").write(MAIN_JS)

# ---------- robots.txt (welcome AI answer engines) ----------
open(os.path.join(OUT, "robots.txt"), "w").write(
    "User-agent: *\nAllow: /\n\n"
    "# AI / answer engines are welcome to read and cite this site\n"
    "User-agent: GPTBot\nAllow: /\n"
    "User-agent: OAI-SearchBot\nAllow: /\n"
    "User-agent: ChatGPT-User\nAllow: /\n"
    "User-agent: ClaudeBot\nAllow: /\n"
    "User-agent: Claude-Web\nAllow: /\n"
    "User-agent: Google-Extended\nAllow: /\n"
    "User-agent: PerplexityBot\nAllow: /\n"
    "User-agent: CCBot\nAllow: /\n\n"
    f"Sitemap: {SITE}/sitemap.xml\n")

# ---------- sitemap.xml (all pages + local news articles, with lastmod) ----------
site_urls = [((u if u else ""), "1.0") for (_, u, _, _) in PAGES.values()]
site_urls += [(f"{n[4]}.html", "0.6") for n in NEWS if n[4]]
sm = "".join(
    f'  <url><loc>{SITE}/{u}</loc><lastmod>{BUILD_DATE}</lastmod><changefreq>weekly</changefreq><priority>{pr}</priority></url>\n'
    for u, pr in site_urls)
open(os.path.join(OUT, "sitemap.xml"), "w").write(
    '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + sm + "</urlset>\n")

# ---------- llms.txt (clean summary for AI answer engines) ----------
LLMS = f"""# South Stack Studios

> South Stack Studios (legal name Haldi Hub) is a registered 501(c)(3) nonprofit, EIN 83-3636419, that funds, mentors, and champions emerging South Asian filmmakers, writers, and artists — bringing authentic, original stories to global audiences. Donations are tax-deductible.

## Pages
- [Home]({SITE}/): Mission and overview
- [About]({SITE}/about): Who we are, who we serve, and our 501(c)(3) nonprofit status
- [Programs]({SITE}/programs): Funding & producing, mentorship, distribution, and community
- [Films]({SITE}/films): Films we've funded and championed — Hanging by a Wire, Humans in the Loop, Holy Curse, Breaking the Code
- [Impact]({SITE}/impact): Outcomes and the storytellers we've supported
- [Team]({SITE}/team): Founders (Shalini Govil-Pai, Reena Mehta, Anjana Gopakumar, Raj Pai) and board member Lata Krishnan, plus advisors
- [In the News]({SITE}/news): Press and festival milestones (Sundance, Cannes, Tribeca, Oscar qualification)
- [Donate / Get Involved]({SITE}/get-involved): How to support — donate, partner, or mentor

## Key facts
- Legal name: Haldi Hub. Status: 501(c)(3) nonprofit. EIN: 83-3636419. Gifts are tax-deductible.
- Focus: emerging South Asian storytellers in film and media.
- Contact: info@southstackstudios.com
- Donate: https://www.zeffy.com/en-US/donation-form/help-us-do-more-3
"""
open(os.path.join(OUT, "llms.txt"), "w", encoding="utf-8").write(LLMS)

print("Generated multi-page site in", os.path.abspath(OUT))
print("Pages:", ", ".join(p[0] for p in PAGES.values()))
# sanity: any leftover tokens or data-go?
import glob
leftover = 0
for f in glob.glob(os.path.join(OUT, "*.html")):
    txt = open(f, encoding="utf-8").read()
    t = re.findall(r"__[A-Z0-9_]+__", txt); g = re.findall(r'data-go=', txt)
    if t or g: print("  !", os.path.basename(f), "tokens:", set(t), "data-go:", len(g)); leftover += 1
print("Leftover token/data-go issues:", leftover)
