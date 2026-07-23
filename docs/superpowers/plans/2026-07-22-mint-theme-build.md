# MINT by Nana Kofi — Theme Build Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the approved demo into a real, self-hosted-font, dark-mode Micro.blog custom theme (Arabica-based) in `hankmint/blog`, validated on a Micro.blog test blog before touching the live site.

**Architecture:** Fork the official Arabica Hugo theme (`microdotblog/theme-arabica`, MIT) into the repo, then replace its stylesheet, fonts, homepage, post, category, gallery, and about templates with the editorial design from the demo. Keep every Micro.blog integration point (`microblog_head.html`, `custom_footer.html`, post/reply types, categories taxonomy, Bigfoot footnotes). Verify rendering with a local Hugo scratch site where possible, and on a Micro.blog test blog for the Micro.blog-specific behavior.

**Tech Stack:** Hugo (Micro.blog's renderer), HTML templates, hand-written CSS (ported from the demo), vanilla JS (dark-mode toggle + gallery lightbox), self-hosted Fraunces + Newsreader woff2.

**Reference files (source of truth):**
- Design demo (all CSS, JS, layout, copy): `/Users/mint/Documents/GitHub/blog/docs/` demo published at artifact; local copy in scratchpad `mint-blog-demo.html`.
- Design spec: `docs/superpowers/specs/2026-07-22-mint-blog-redesign-design.md`.
- Upstream theme (already cloned): scratchpad `theme-arabica/`.

## Global Constraints

- Platform: Micro.blog custom theme. Repo must be a valid theme root (theme.toml, plugin.json, config.json, layouts/, static/), NOT a full Hugo site.
- Keep MIT license and Arabica attribution (`LICENSE`, footer credit, theme.toml `[original]`).
- Keep `{{ partial "microblog_head.html" . }}` in head and `{{ partial "custom_footer.html" . }}` in base. These are Micro.blog-supplied; never remove.
- No external network calls in the rendered page: self-host fonts (woff2 in `static/fonts/`), no Google Fonts link, no CDN jQuery (replace Bigfoot dependency or vendor it locally).
- Copy rule (author preference): no em dashes or en dashes anywhere in templates or copy. Use commas, colons, periods, or "to".
- Palette, type, and layout must match the approved demo exactly (light + dark tokens as specified in the spec).
- Rollout: nothing is applied to live `nanakofiwrites.com` until reviewed. Test blog first.
- Do not push to `hankmint/blog` until the author approves (per the author's git rules).

---

### Task 1: Seed the repo with the upstream Arabica theme

**Files:**
- Create (copy from scratchpad `theme-arabica/`, excluding `.git`): `theme.toml`, `plugin.json`, `config.json`, `LICENSE`, `README.md`, `layouts/**`, `static/**`, `images/**` into `/Users/mint/Documents/GitHub/blog/`.

**Interfaces:**
- Produces: a valid, unmodified Arabica theme in the repo as the baseline to restyle.

- [ ] **Step 1: Copy upstream files (not .git) into the repo**

```bash
SRC="/private/tmp/claude-501/-Users-mint/fca8ca0b-4fa5-4f33-9013-476042b9e5d4/scratchpad/theme-arabica"
DST="/Users/mint/Documents/GitHub/blog"
rsync -a --exclude='.git' "$SRC"/ "$DST"/
```

- [ ] **Step 2: Verify structure**

Run: `cd /Users/mint/Documents/GitHub/blog && ls theme.toml plugin.json config.json layouts static images LICENSE`
Expected: all listed, no error. `docs/` (spec + this plan) still present.

- [ ] **Step 3: Commit baseline**

```bash
git add -A && git commit -m "chore: vendor official Arabica theme as MINT baseline (MIT, credit retained)"
```

---

### Task 2: Theme identity (theme.toml, plugin.json, config.json, README)

**Files:**
- Modify: `theme.toml`, `plugin.json`, `config.json`, `README.md`

**Interfaces:**
- Produces: theme name "MINT", author Nana Kofi, config params consumed by templates: `logoTitle`, `description`, `dateFormatToUse`, plus MINT params `mint_accent`, `mint_tagline`.

- [ ] **Step 1: Rewrite `plugin.json`**

```json
{
	"version": "1.0.0",
	"title": "MINT by Nana Kofi",
	"description": "Editorial long-form theme for Nana Kofi: latest-blurb + year index homepage, Tech/Business/Creative topics, gallery with lightbox, dark mode. Based on Arabica."
}
```

- [ ] **Step 2: Rewrite `theme.toml`** (keep MIT + `[original]` Arabica credit; set name "MINT", author Nana Kofi).

- [ ] **Step 3: Set `config.json` defaults** consumed by templates:

```json
{
  "params": {
    "dateFormatToUse": "January 02, 2006",
    "logoTitle": "<span class=\"mark\">MINT</span><span class=\"by\">by Nana Kofi</span>",
    "description": "Writing on tech, business, and the creative.",
    "archive-paginate": 100
  }
}
```

- [ ] **Step 4: Rewrite `README.md`**: what MINT is, that it is based on Arabica (MIT, credit), the edit-then-resync workflow (edit here, push, Update Theme in Micro.blog), and the test-blog-first rollout rule.

- [ ] **Step 5: Commit**

```bash
git add theme.toml plugin.json config.json README.md && git commit -m "feat: MINT theme identity and config params"
```

---

### Task 3: Self-hosted fonts

**Files:**
- Create: `static/fonts/fraunces-*.woff2`, `static/fonts/newsreader-*.woff2`, `static/css/fonts.css`

**Interfaces:**
- Produces: `--serif-display` (Fraunces), `--serif-body` (Newsreader) available with no network call. `fonts.css` defines `@font-face` with `font-display: swap` pointing at local woff2.

- [ ] **Step 1: Fetch woff2 files** for Fraunces (display, ~2 weights: 400, 600) and Newsreader (body: 400, 400italic, 600). Download the woff2 binaries into `static/fonts/` (from Google Fonts' woff2 URLs or the fonts' GitHub releases). Verify each file is a real woff2 (`file static/fonts/*.woff2` shows "Web Open Font Format").

- [ ] **Step 2: Write `static/css/fonts.css`** with `@font-face` blocks referencing `/fonts/<file>.woff2` via `url()`, `font-display: swap`.

- [ ] **Step 3: Verify** the files are non-empty and the paths resolve (they will be served from theme static root at `/fonts/...`).

- [ ] **Step 4: Commit**

```bash
git add static/fonts static/css/fonts.css && git commit -m "feat: self-host Fraunces + Newsreader (no external font calls)"
```

---

### Task 4: The stylesheet (port the demo design)

**Files:**
- Create: `static/css/mint.css` (the full editorial stylesheet, ported from `mint-blog-demo.html`'s `<style>` block, adapted from demo class names to Arabica's markup classes where they differ).
- Modify: `static/assets/css/screen.css` -> leave upstream file but stop loading it (see Task 5), OR blank it. Decision: keep `normalize.css` for reset, drop `icons.css`/`screen.css`, load `fonts.css` + `mint.css`.

**Interfaces:**
- Consumes: tokens and component styles from the demo; font families from `fonts.css`.
- Produces: `mint.css` styling Arabica's real classes: `.main-header`, `.blog-title`, `.nav`, `.content`, `.post`, `.post-title`, `.post-content`, `.post-meta`, `.pagination`, plus MINT-new classes for the year index and gallery.

- [ ] **Step 1: Port tokens + base + typography** from demo into `static/css/mint.css` (light/dark via `:root`, `@media (prefers-color-scheme: dark)`, and `:root[data-theme=...]` overrides exactly as in the demo).

- [ ] **Step 2: Map demo components to Arabica classes.** Style `.main-header`/`.blog-title`/`.nav` as the demo masthead; `.post`/`.post-title`/`.post-content` as the demo article; `.post-meta` as meta rows. Add `.mint-index`, `.mint-year`, `.mint-entry` for the homepage index and `.mint-gallery`, `.mint-shot`, `.mint-lightbox` for the gallery.

- [ ] **Step 3: Verify locally** (see Task 10 harness). Expected: a rendered post page matches the demo article visually (serif, oxblood links, measure ~39rem, dark mode works).

- [ ] **Step 4: Commit**

```bash
git add static/css/mint.css && git commit -m "feat: editorial MINT stylesheet ported from approved demo"
```

---

### Task 5: Head, base, and footer partials

**Files:**
- Modify: `layouts/partials/head.html`, `layouts/_default/baseof.html`, `layouts/partials/footer.html`

**Interfaces:**
- Consumes: `fonts.css`, `mint.css`, `microblog_head.html` (Micro.blog-supplied).
- Produces: pages that load only local CSS, keep Bigfoot footnotes working without CDN jQuery, keep `microblog_head.html`, and include the theme toggle + lightbox markup once per page.

- [ ] **Step 1: Rewrite `head.html`** to load `normalize.css`, `fonts.css`, `mint.css`; remove Google Fonts link and `screen.css`/`icons.css`; keep `{{ partial "microblog_head.html" . }}`; keep custom CSS loop.

- [ ] **Step 2: Replace CDN jQuery + Bigfoot** with the vendored `assets/bigfoot/dist/bigfoot.js`. If Bigfoot needs jQuery, vendor `jquery.min.js` into `static/assets/` and reference locally; otherwise keep Bigfoot but load locally. Verify no `https://cdn` or `https://fonts.googleapis` remains in `head.html`.

- [ ] **Step 3: Add theme toggle + lightbox scaffolding** into `baseof.html` (a `<button class="mint-theme-toggle">` in header handled by Task 8's JS, and the `.mint-lightbox` overlay container used by the gallery). Keep `custom_footer.html` and `microblog_head.html` partials.

- [ ] **Step 4: Rewrite `footer.html`** to the demo footer (MINT by Nana Kofi, nanakofiwrites.com, Arabica credit retained, RSS link `/feed.xml`). Keep customJS loop.

- [ ] **Step 5: Verify + commit**

```bash
grep -RE "cdn\.|fonts\.googleapis" layouts/ ; echo "should be empty"
git add layouts/partials/head.html layouts/_default/baseof.html layouts/partials/footer.html && git commit -m "feat: local-only head/base/footer, keep Micro.blog + Bigfoot integration"
```

---

### Task 6: Masthead / navigation

**Files:**
- Modify: `layouts/partials/header.html`

**Interfaces:**
- Consumes: `.Site.Params.logoTitle`, `.Site.Menus.main`.
- Produces: the demo masthead: MINT wordmark + "by Nana Kofi", nav to Tech / Business / Creative / Gallery / About, theme toggle button. Nav highlights current section.

- [ ] **Step 1: Rewrite `header.html`** with the demo lockup and nav. Topics link to category pages (`/categories/tech/` etc. once verified in Task 9). Add `nav-current` on active section. Include the theme-toggle button.

- [ ] **Step 2: Verify + commit**

```bash
git add layouts/partials/header.html && git commit -m "feat: MINT masthead and topic nav"
```

---

### Task 7: Homepage — latest blurb + year index

**Files:**
- Modify: `layouts/index.html`, `layouts/post/summary.html`

**Interfaces:**
- Consumes: `where .Site.Pages "Type" "post"`.
- Produces: homepage that shows the newest N posts (default 2) as title + standfirst (first paragraph / `.Summary`), then all remaining posts as a year-grouped index (`.mint-year` headings, `.mint-entry` rows with date + title + category dot).

- [ ] **Step 1: Rewrite `index.html`.** Sort posts by date desc. First 2 -> "featured" block (title link + `.Summary` standfirst + meta). Remaining -> group by `.Date.Format "2006"`, render `.mint-year` + `.mint-entry` rows. Year grouping in Hugo: iterate posts, track current year in a `$year` variable via comparison, emit a heading when it changes.

```go-html-template
{{ define "main" }}
<main class="content h-feed mint-home" role="main">
  {{ $posts := where .Site.RegularPages "Type" "post" }}
  {{ $featuredN := 2 }}
  <section class="mint-lede">
    {{ range first $featuredN $posts }}{{ .Render "featured" }}{{ end }}
  </section>
  <section class="mint-index">
    <div class="mint-index-head"><h3>The Index</h3></div>
    {{ $rest := after $featuredN $posts }}
    {{ $year := "" }}
    {{ range $rest }}
      {{ $y := .Date.Format "2006" }}
      {{ if ne $y $year }}{{ if ne $year "" }}</ul>{{ end }}<div class="mint-year">{{ $y }}</div><ul class="mint-entries">{{ $year = $y }}{{ end }}
      <li><a class="mint-entry" href="{{ .Permalink }}">
        <span class="date">{{ .Date.Format "Jan 02" }}</span>
        <span class="ttl">{{ .Title | default "Untitled" }}</span>
        <span class="topic">{{ with .Params.categories }}<span class="dot"></span>{{ index . 0 }}{{ end }}</span>
      </a></li>
    {{ end }}
    {{ if ne $year "" }}</ul>{{ end }}
  </section>
</main>
{{ end }}
```

- [ ] **Step 2: Add `layouts/post/featured.html`** rendering the title + `.Summary` standfirst + meta used by the lede.

- [ ] **Step 3: Verify locally** with sample posts (Task 10). Expected: 2 featured on top, then "2026"/"2025" groups with date+title rows.

- [ ] **Step 4: Commit**

```bash
git add layouts/index.html layouts/post/featured.html layouts/post/summary.html && git commit -m "feat: homepage latest-blurb + year index"
```

---

### Task 8: Post reading view + dark-mode toggle JS + lightbox JS

**Files:**
- Modify: `layouts/post/single.html`
- Create: `static/js/mint.js`

**Interfaces:**
- Consumes: `.Content`, `.Title`, `.Date`, `.Params.categories`, `.ReadingTime`.
- Produces: editorial article (eyebrow category, big serif title, standfirst, meta with reading time, wide image, Bigfoot footnotes retained, prev/next). `mint.js` provides `toggleTheme()` (sets `data-theme` on `<html>`, persists to `localStorage`) and the gallery lightbox (`openLB/stepLB/closeLB`, keyboard support), ported from the demo.

- [ ] **Step 1: Rewrite `post/single.html`** to the demo article structure using Arabica classes, keeping `.Content`, tags/categories footer, and the Micro.blog `conversation.js` block guarded by `.Site.Params.include_conversation`.

- [ ] **Step 2: Write `static/js/mint.js`** with the theme toggle (reads `localStorage.mint-theme`, falls back to `prefers-color-scheme`) and the lightbox logic from the demo. Load it in `baseof.html`.

- [ ] **Step 3: Verify** dark toggle persists across reloads; footnotes pop; images render wide.

- [ ] **Step 4: Commit**

```bash
git add layouts/post/single.html static/js/mint.js && git commit -m "feat: editorial post view, dark-mode toggle, lightbox"
```

---

### Task 9: Category (topic) pages — VERIFY Micro.blog conventions

**Files:**
- Modify: `layouts/_default/list.html`; possibly add `layouts/category/list.html`.

**Interfaces:**
- Produces: Tech/Business/Creative archive pages styled as the year index, each with its own RSS.

- [ ] **Step 1: VERIFY** on the Micro.blog test blog (or Micro.blog docs) the exact taxonomy for categories: URL pattern (`/categories/<slug>/` expected), the param name on posts (`.Params.categories` expected), and that per-category RSS exists. Record findings in the plan.
- [ ] **Step 2: Rewrite `list.html`** to render the matching posts as the year index (reuse Task 7's grouping), with the category title as an `<h1>`.
- [ ] **Step 3: Verify** each topic page lists only its posts and links resolve.
- [ ] **Step 4: Commit**

```bash
git add layouts/_default/list.html && git commit -m "feat: topic archive pages as year index"
```

---

### Task 10: Gallery page — VERIFY photo data source

**Files:**
- Create: `layouts/gallery/single.html` (or `layouts/_default/gallery.html`), styled with `.mint-gallery` grid + lightbox.

**Interfaces:**
- Consumes: photo posts (posts with images / a "Photos" category / Sunlit output).
- Produces: a masonry grid of photos with working lightbox, fed automatically from photo posts.

- [ ] **Step 1: VERIFY** how this account's Sunlit photo posts appear in Hugo: do they carry `.Params.images` / a `photo` category / land in a section? Check a real photo post on the test blog. Decide the data source (recommended: a `Photos` category, or posts where `.Params.images` is non-empty).
- [ ] **Step 2: Build the gallery template** iterating the chosen photo set, emitting `.mint-shot` tiles with real `<img>` (from `.Params.images`) and captions, wired to the lightbox from `mint.js`.
- [ ] **Step 3: Create the Gallery page** on the test blog (a Micro.blog Page with the gallery layout, or a category page) and confirm it renders.
- [ ] **Step 4: Commit**

```bash
git add layouts/gallery && git commit -m "feat: gallery page with lightbox fed by photo posts"
```

---

### Task 11: About page + local render harness

**Files:**
- Modify: `layouts/_default/single.html` (About uses the page template, styled editorially).
- Create (scratch, not committed): a minimal Hugo test site under scratchpad that mounts this theme with sample posts, so tasks 4-10 can be viewed with `hugo server` locally where Micro.blog-independent.

**Interfaces:**
- Produces: styled About page; a local preview path for fast iteration.

- [ ] **Step 1: Build the scratch Hugo site**: `scratchpad/mint-testsite/` with `hugo.toml`, a stub `layouts/partials/microblog_head.html` (empty) and `custom_footer.html` (empty) via theme fallback, 6 sample posts (2026/2025, categories Tech/Business/Creative), and the theme symlinked/copied as `themes/mint`. Run `hugo server` and screenshot home + a post.
- [ ] **Step 2: Style `single.html`** (About / pages) to the demo About look.
- [ ] **Step 3: Verify + commit** (`single.html` only; scratch site stays out of the repo).

```bash
git add layouts/_default/single.html && git commit -m "feat: editorial About/page template"
```

---

### Task 12: Push + connect to Micro.blog test blog (GATED on author approval)

- [ ] **Step 1: Final local review** of the whole theme against the demo (light + dark, home, post, topic, gallery, about, mobile).
- [ ] **Step 2: Get author approval to push** (per git rules).
- [ ] **Step 3: Push** `hankmint/blog` main.
- [ ] **Step 4: Guide author** through Micro.blog: Design -> Edit Custom Themes -> New Theme -> Clone URL `https://github.com/hankmint/blog.git`; select it on a **test blog**; create Gallery/About pages; assign Tech/Business/Creative categories to sample posts; verify.
- [ ] **Step 5: Only after author sign-off**, apply to live `nanakofiwrites.com` and click Update Theme.

---

## Self-Review

**Spec coverage:** platform (Task 1,12), identity/masthead (Task 2,6), aesthetic/palette/type (Task 3,4), homepage latest+index (Task 7), topics (Task 6,9), reading experience + footnotes + reading time (Task 8), gallery + lightbox (Task 8,10), about (Task 11), dark mode (Task 4,8), technical structure + license + Micro.blog integration + self-hosted fonts (Tasks 1-5), rollout test-blog-first (Task 12). All spec sections mapped.

**Placeholder scan:** The two "VERIFY" steps (Tasks 9, 10) are genuine external unknowns about Micro.blog/Sunlit conventions, gated with the exact thing to check and a recommended default, not hidden work. All template/CSS/JS deliverables are concrete and sourced from the approved demo.

**Type consistency:** template param names (`.Params.categories`, `.Params.images`, `.Summary`, `.ReadingTime`) and new CSS classes (`.mint-index`, `.mint-year`, `.mint-entry`, `.mint-gallery`, `.mint-shot`, `.mint-lightbox`) are used consistently across tasks. Homepage year-grouping logic in Task 7 is reused by Task 9.

**Testing adaptation:** This is a Hugo/Micro.blog theme with no unit-test harness; TDD's red/green is replaced by build-and-view verification (local Hugo scratch site in Task 11 for Micro.blog-independent parts, test blog for Micro.blog-specific parts). This is the honest, correct verification for template work.
