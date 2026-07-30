# MINT — what to take from harper.blog, and what to leave

**Date:** 2026-07-30
**Audited:** harper.blog, every section, plus the markup underneath
**Compared against:** what MINT actually has today, measured not guessed

---

## 1. The audit — everything harper.blog has

**Stack (from his own colophon):** Hugo. Netlify. Markdown. Custom theme based on Bear Cub. System fonts. Custom shortcodes.
**Same generator as MINT**, so all of this is portable, not aspirational.

| Section | What it is | Notable |
|---|---|---|
| **Home** | Intro paragraph, then two lists: Posts (date + title) and Notes (date + full text) | Both forms visible at once, presented differently |
| **Posts** | All long-form. Post count stat. A `<details>` disclosure, "Eras of my blog" | *"1444 posts ~ 1.04 posts/week"* |
| **Notes** | Short form. Date, a `#` permalink, the text, often a photograph | *"Long stuff is in the blog"* — the split stated out loud |
| **Now** | Date-stamped snapshot, `Now @ 01-06-2026`, H2 sections, bullets | Derek Sivers convention |
| **Media** | Books, music and links interleaved by date. Emoji per type | Index only |
| `/media/books` | Books, list **and grid** (cover art). Reading stats in a `<details>` | list ⇄ grid toggle |
| `/media/music` | Music, list **and grid** (album art). *"2026 (144 songs)"*, grouped by month | same toggle |
| `/music/<date>-<slug>-<id>/` | **A page per song**, with the Spotify player | 300×80 compact embed |
| **About** | Stats in prose, photo with italic caption, Contact, sign-off | |
| **Colophon** | How the site is built | |
| **Translations** | Full site trees at `/es/ /ja/ /ko/ /id/` | Real generated translation |
| **Footer** | About · Posts · Translations · Colophon · Harper.lol, "Generated on Jul 28, 2026" | |

**The two structural moves worth naming:**

**Depth behind one door.** The nav is six items and never grows. Books, music, grids, lists and 144+ track pages all sit behind "Media". Complexity lives one level down instead of flattening into the menu.

**Every song is a tiny post.** A listening log became ~144 individual pages a year, each linkable, indexable, with room for one sentence of his own. That is a lot of content from very little writing.

---

## 2. The honest comparison

| | harper.blog | MINT |
|---|---|---|
| Posts | **1,444** since 2000 | **21** |
| Rate | ~1.04/week for 24 years | bursty: 3, then 14, then 1, then 3 |
| Median length | long-form + notes | **17 words** |
| With photographs | some | **19 of 21 — 90%** |
| Long essays | hundreds | **3** |

**Two things follow, and they should drive every decision below.**

**His structure is the output of 24 years, not the input.** He did not launch with Media, Notes, Now and translations. Those accreted because the content demanded them. Building them first produces empty rooms, and an empty room reads as abandonment.

**MINT is not a text blog. It is a photo-note blog.** 90% photographs, median 17 words. Harper's architecture assumes lots of prose. Copying it wholesale would build shelves for a kind of content that is not being made.

### On the seven themes — tech, bikes, dogs, creative, countries, books, music

**Do not make these sections.** 7 themes ÷ 21 posts ≈ 3 posts each, and **18 of the 21 are already uncategorised**. Seven near-empty nav items would make an active blog look dead.

**Make them tags instead.** A tag with two posts is simply a small page. A nav item with two posts looks broken. Tags scale *down* gracefully; sections do not. When a tag reaches roughly 15–20 posts it has earned a nav item, and promoting it later is a template change, not a migration.

**And note the Rooms already exist** — Building, Creative, Life — used on 3 posts out of 21. Fill those in before inventing more.

---

## 3. Do now

Ordered by value per hour. All four suit a photo-led blog with 21 posts.

- [ ] **1. Music log + a page per song.** ⭐ The single best fit.
  - The embed hook already exists. This is the piece that makes it accumulate.
  - Works from n=1: one song is a real page, not an empty section.
  - Turns listening into posting — the cheapest content there is.
  - Structure: content file per track, Spotify ID in frontmatter, `/music/` index. Copy his 300×80 compact embed rather than MINT's full-width one.
- [ ] **2. Categorise the 18 uncategorised posts** into Building / Creative / Life.
  - Zero code. Makes the taxonomy that already exists actually work.
  - Tells us whether Rooms are the right axis before adding any more.
- [ ] **3. A `/now/` page.** One content file. Highest signal-to-effort on the whole list.
- [ ] **4. `<details>` disclosures.** Already works — `unsafe = true` is set. Nothing to build, just start using it.

**Also still open from earlier today, unrelated to Harper:**
- [ ] Delete or re-slug the test post — it is live with a trailing period in the URL
- [ ] **Automate the image optimiser.** Editor uploads arrive at 4–8 MB with no thumbnail. This keeps costing real time

---

## 4. Wait — with the trigger that unlocks each

| Thing | Wait until | Why |
|---|---|---|
| **Posts / Notes split into separate nav** | ~15–20 titled essays | Right now a "Posts" page lists **3**. The data model already supports it, so it is cheap whenever the trigger hits |
| **Books page** | You are actually logging books | The page is trivial; the habit is the hard part |
| **Grid ⇄ list toggles** | A section has 30+ items | Below that a grid is a worse list |
| **Post-count stats** | ~100 posts | *"1,444 posts ~ 1.04/week"* is impressive. *"21 posts"* is not the flex |
| **Translations** | There is an audience asking | Real cost, no current demand |
| **New nav sections for themes** | A tag reaches ~15–20 posts | Promote from tag to section, never the reverse |

---

## 5. The rule to keep

**Structure follows content.** Every section Harper has was earned by writing that already existed. The two things worth copying *now* are the ones that work at small scale: **a page per song**, which is real at n=1, and **tags**, which are invisible until they are populated.

Everything else is a shelf. Build shelves when there are books.

---

## Review

*(fill in as items land)*
