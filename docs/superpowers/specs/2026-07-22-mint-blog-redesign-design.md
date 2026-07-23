# MINT by Nana Kofi — Blog Redesign Design Spec

- **Date:** 2026-07-22
- **Author:** Nana Kofi (Kay Reddington), with Dembe (Claude)
- **Repo:** `hankmint/blog` (custom Micro.blog theme)
- **Live site:** `nanakofiwrites.com` (currently "M I N T", Arabica theme)
- **Status:** Approved design, pending spec review

## 1. Goal

Turn the current minimal photo/reflection microblog into a durable, long-form
**founder's personal blog** with rich images, spanning **Tech, Business, and
Creative**, without adding posting friction. The design must "live on" and be
easy to feed regularly.

## 2. Platform decision (settled)

- **Home stays on Micro.blog.** Posting stays frictionless: the Micro.blog app
  for words, **Sunlit** (native Micropub) for photo stories. Micro.blog provides
  hosting, SSL, RSS, custom domain, and the Micropub endpoint Sunlit needs.
- **The redesign lives as a custom Hugo theme** in `hankmint/blog`, built from
  the official Arabica theme (`github.com/microdotblog/theme-arabica`, MIT) and
  restyled top to bottom.
- **Workflow:** edit theme in Git → push → resync in Micro.blog
  (Design → Edit Custom Themes → Update). Posts and photos are never touched by
  theme changes.
- **Rollout:** build and validate on a Micro.blog **test blog** first. The live
  site `nanakofiwrites.com` does not change until reviewed and explicitly
  approved.

Rejected alternative: full self-host (Hugo/Next on Vercel). Reason: loses native
Sunlit posting (would require building/maintaining a Micropub server) and adds
maintenance burden that works against "post regularly" and "lives on."

## 3. Identity & voice

- Founder's personal blog. One voice, three currents: **Tech · Business · Creative**.
- **Masthead:** "MINT by Nana Kofi" (brand + byline).

## 4. Aesthetic direction

Editorial and literary. Typography-led, generous whitespace, calm reading measure.

### Palette
| Token | Light | Dark |
|---|---|---|
| Ink (text) | `#1A1714` warm near-black | `#EDE6DA` cream |
| Paper (bg) | `#FBF8F3` warm off-white | `#16130F` near-black |
| Accent (links, tags, marks) | `#7A2E28` deep oxblood | `#C6685E` softened oxblood |
| Muted (meta, standfirst) | `#6B655E` | `#9B9488` |
| Rule / border | `#E4DCCF` | `#2A2620` |

Full dark mode via `prefers-color-scheme` plus a manual toggle. Photos provide
the rest of the color.

### Typography (chosen pairing, self-hosted woff2 for speed and no external calls)
- **Headlines:** Fraunces (expressive high-contrast optical serif).
- **Body:** Newsreader (comfortable reading serif).
- **Mono (code):** system mono stack (`ui-monospace, SFMono-Regular, Menlo, monospace`).
- Fonts are self-hosted in `static/fonts/` as woff2 so Micro.blog serves them
  directly (no Google Fonts request).

## 5. Homepage

- Newest **1 to 3 essays** shown as serif title + one-line gray standfirst.
- Below, everything collapses into a **title-first archive grouped by year**
  (date + title, scannable).
- No hero clutter; the words lead.

## 6. Navigation & topics

- Top nav: `Tech · Business · Creative · Gallery · About`.
- **Tech / Business / Creative** are Micro.blog **categories**, each with its own
  filtered archive page and its own RSS feed.
- **Gallery** and **About** are dedicated pages (see below).

## 7. Long-form reading experience (post page)

- Reading measure ~66 characters; restful serif body size (~1.125rem, 1.7 line-height).
- Wide / full-bleed images with italic captions.
- Pull-quotes styled distinctly.
- Footnotes via Arabica's Bigfoot popovers (retained from base theme).
- Post header: topic tag, date, reading time.
- Post footer: quiet prev/next links, topic tag, link back to archive.
- Optional drop-cap on the opening paragraph (tasteful, off by default; decide in build).

## 8. Gallery (Photos room)

- Dedicated page presenting Nana Kofi's photography beautifully.
- Responsive **justified/masonry grid** of images.
- **Full-screen lightbox** on click (keyboard + swipe navigation, captions).
- Optional large full-bleed feature image leading the page.
- Fed by **photo posts / Sunlit stories** (a `Photos` category or photo-type
  posts), so publishing from Sunlit makes an image appear here automatically.
- Lightbox implemented with a small dependency-free JS module in `static/`.

## 9. About page

- Personal: who Nana Kofi is, what MINT is about.
- Links out: Sunlit, socials, RSS.

## 10. Technical structure

Standard Micro.blog custom-theme layout:

```
theme.toml        # theme meta (name "MINT", author, MIT, original: Arabica)
plugin.json       # Micro.blog plugin meta + any user-configurable settings
config.json       # Hugo params referenced by templates (accent, fonts, etc.)
layouts/          # restyled: baseof, index, list, single, post/, section/, partials/, 404
static/
  css/            # custom editorial stylesheet(s)
  fonts/          # self-hosted Fraunces + Newsreader woff2
  js/             # lightbox, dark-mode toggle
images/           # theme screenshot + tn for plugin listing
LICENSE           # MIT, Arabica attribution retained
README.md         # origin, edit-then-resync workflow, credit to Arabica
```

Requirements: fully responsive, dark mode, fast static rendering, valid RSS per
topic, accessible (semantic HTML, alt text surfaced, keyboard-navigable lightbox,
sufficient contrast in both themes). MIT license and Arabica attribution kept.

## 11. Success criteria

1. On the test blog, the theme renders the homepage as latest-blurb + year archive.
2. Tech/Business/Creative nav filters work and each has its own RSS.
3. A long-form post reads comfortably with images, captions, footnotes, and reading time.
4. The Gallery displays photos in a grid with a working lightbox, fed by photo posts.
5. Light and dark modes both pass contrast and look intentional.
6. Nana Kofi can publish a normal post and a Sunlit photo story and both land correctly.
7. Only after review is the theme applied to the live `nanakofiwrites.com`.

## 12. Out of scope (YAGNI)

- Self-hosting / migrating off Micro.blog.
- Comments system, newsletter capture, search (can be follow-ups).
- Custom Micropub server.
- Redesign of existing post *content* (content stays; only presentation changes).

## Open items to resolve in build

- Final drop-cap decision (on/off).
- Exact Gallery data source: dedicated `Photos` category vs Sunlit photo-type
  detection (confirm against how Sunlit tags posts on this account).
