# Design: Moving nanakofiwrites.com off Micro.blog hosting

**Date:** 2026-07-28
**Author:** Nana Kofi (Kay) with Claude
**Status:** Approved design, ready for implementation planning
**Supersedes:** the "Non-goals" section of `2026-07-22-mint-blog-redesign-design.md`, which listed
self-hosting as a rejected alternative. That decision is reversed here, for the reason in Context.

## Context

The MINT theme was built in July 2026 as a Micro.blog custom theme and pushed to `hankmint/blog`.
It was never applied to the live site: as of 2026-07-28, nanakofiwrites.com still serves stock
Arabica. Kay's reason for moving is design control. He wants to see his design on his blog without
a custom-theme registration step deciding whether it appears.

The earlier spec rejected self-hosting because it would lose native Sunlit posting. That reason
still stands, and this design addresses it directly in Movement 2 rather than accepting the loss.

## Verified findings

Everything below was checked against the live site, the export, or the upstream project on
2026-07-28. Nothing here is assumed.

### The export

Kay downloaded `Export theme and Markdown (.zip)` as `~/Downloads/themint_e83356.zip` (305 KB).
Contents: a full Hugo site skeleton, Micro.blog's own theme, `config.json`, and 24 Markdown files
which break down as:

- **18 dated posts** under `content/YYYY/MM/DD/`. Three of these are from April 2025 and are
  visibly test posts (`this-is-a-test-post`, `this-is-my-new-post`, `144854`).
- **5 pages**: `about.md`, `archive.md`, `photos.md`, `replies.md`, `stories.md`. These are
  Micro.blog scaffolding. `archive.md`, `photos.md` and `replies.md` exist to trigger Micro.blog's
  own output formats and are likely redundant against the MINT theme, which has its own year index
  and gallery. Each needs a keep-or-drop decision during implementation.
- **1 note** under `content/notes/`.

**It contains no photographs.** Zero image files. Every photo is a reference to Micro.blog's
servers.

### Photographs (the main risk)

- 28 unique `<img src>` values across post bodies.
- 27 unique originals listed in front matter at `https://cdn.uploads.micro.blog/217795/...`.
- Both `https://cdn.uploads.micro.blog/217795/2025/<hash>.jpg` and
  `https://nanakofiwrites.com/uploads/2025/<hash>.jpg` return HTTP 200, ~1.35 MB each.
- Estimated total: roughly 35 MB.

If the Micro.blog blog is deleted, these are gone, and the export does not contain them.

### The relative-path trap

Post bodies store raw HTML with a **relative** src:

```html
<img src="uploads/2025/78139fa9db98496a86445c5de4eab9f7.jpg">
```

Micro.blog rewrites this to the absolute CDN URL at render time. Confirmed against the live page
`/2025/12/21/i-forgot-to-share-these.html`, which serves
`src="https://cdn.uploads.micro.blog/217795/2025/78139fa9db98496a86445c5de4eab9f7.jpg"`.

Hugo does no such rewriting. Left untouched, a post at `/2025/12/21/foo.html` would resolve
`uploads/...` relative to that directory and every image would 404.

### Permalinks are already safe

Each post carries its own permalink in front matter, for example
`url: "/2025/12/21/i-forgot-to-share-these.html"`. Hugo honours this. No permalink configuration
or redirect map is needed as long as the front matter is preserved.

### The feed recipe

Micro.blog's exported `config.json` shows exactly how the two feeds are produced:

```json
"mediaTypes": { "application/json": { "suffixes": ["json"] } },
"outputFormats": { "RSS": { "baseName": "feed" }, "JSON": { "baseName": "feed" } },
"outputs": { "home": ["HTML", "RSS", "JSON", ...] }
```

This is safety-critical. Kay's Micro.blog **Sources** page has
`https://nanakofiwrites.com/feed.json` registered, with cross-posting enabled to Bluesky, Mastodon,
Threads, LinkedIn, Tumblr, Medium, Flickr, Nostr, Pixelfed, PeerTube, Day One and YouTube.
Micro.blog does not require it to host the blog in order to cross-post; it only reads that URL.

So cross-posting survives the move **for free**, provided the self-hosted site serves valid
JSON Feed at exactly `/feed.json`. If it does not, cross-posting stops silently. Nothing errors,
nothing warns, posts simply stop reaching the networks.

Other config worth carrying over: `taxonomies: { category: "categories" }`,
`markup.goldmark.renderer.unsafe: true` (required, because post bodies contain raw HTML),
`paginate: 25`, `rssLimit: 25`.

### The theme's coupling to Micro.blog

Audited `layouts/`. Exactly one hard dependency:

- `layouts/partials/head.html` calls `{{ partial "microblog_head.html" . }}`, a partial Micro.blog
  injects. It does not exist off-platform and the build fails without it.
- `.Site.Params.plugins_js` comes from Micro.blog's plug-in system.

Everything else (`dateFormatToUse`, `logoTitle`, `description`, `featuredCount`, `customCSS`,
`customJS`, `author`, `mastodon`) is ordinary Hugo params we will own in `hugo.toml`.

There is **no Hugo site configuration in the repo at all**. `config.json` is the Micro.blog theme
params file, not a Hugo config.

### Captions

`static/css/mint.css` already styles captions properly:

```css
.post-content figure { margin: 2.6rem 0; }
.post-content figcaption, .post-content img + em { font-family: var(--sans); font-size: .74rem; color: var(--muted); ... }
```

But there are no render hooks and no shortcodes in the theme, so nothing ever emits a `<figure>`.
The styling exists and has never been reachable.

### Indiekit (for Movement 2)

`getindiekit/indiekit`, MIT, 385 stars, last pushed 2026-07-26. Ships the exact plugins needed:
`endpoint-micropub`, `endpoint-media`, `endpoint-auth`, `preset-hugo`, `store-github`,
`post-type-photo`, `syndicator-bluesky`, `syndicator-mastodon`.

Micro.blog's own Sunlit repository states Sunlit publishes to "your own blog, hosted by Micro.blog
or compatible blogs using WordPress or Micropub". Sunlit requires a **media endpoint** to send
photos, which Indiekit provides.

Requirements, per Indiekit's README: Node.js v24.17+, a publicly addressable URL, and it cannot run
serverless. MongoDB is optional but required for syndication, for editing or deleting past posts,
and for managing uploaded media. All three are wanted, so MongoDB is required in practice.

## Decisions

1. **`hankmint/blog` becomes the whole site**, not just a theme. Its `layouts/` and `static/` are
   already at a Hugo site root, so nothing moves. We add `hugo.toml` and `content/`. One repo.
2. **Two movements.** Movement 1 has no moving parts and cannot break. Movement 2 adds the one
   component that can be down, and is never in the critical path of the migration.
3. **Micro.blog subscription is kept** ($5/month, no feed-only tier exists) as a cross-post relay
   reaching networks Indiekit does not. The hosted blog itself is deleted last, or never.
4. **Captions via a Markdown render hook**, not a Hugo shortcode, so captions are plain Markdown
   that any editor can produce and that survives changing editors.

## Movement 1: stand on our own ground

Nothing in this movement can fail at runtime. It is static files.

### 1.1 Rescue the photographs

Before anything else. Download all 28 originals from the CDN into `static/uploads/`, preserving the
`2025/` and `2026/` path structure. Verify every file against the list extracted from the export,
and verify each is a valid non-empty image. This is the only irreversible risk in the project.

### 1.2 Make the repo a Hugo site

- Add `hugo.toml` carrying over: `baseURL`, title, the `feed`/`feed.json` output formats exactly as
  Micro.blog defines them, `taxonomies` (`category` to `categories`), goldmark `unsafe: true`,
  pagination, and the MINT params currently in `config.json`.
- Add the 24 Markdown files under `content/`, front matter untouched so permalinks are preserved.
- Add a local `layouts/partials/microblog_head.html` stub so the build no longer depends on
  Micro.blog injecting it.
- Delete the untracked iCloud duplicate files in the working tree (`LICENSE 2`, `config 2.json`,
  `layouts/index 2.html`, `theme 2.toml`, and the rest). They are the same class of cruft that
  breaks CLI builds on `knodai_v1`.

### 1.3 Rewrite image paths

Rewrite every `<img src="uploads/...">` in post bodies to site-absolute `/uploads/...`.
Then prove it: build the site and confirm all 28 images resolve against local files with zero 404s.

### 1.4 Captions

Add `layouts/_default/_markup/render-image.html` so that

```markdown
![a woman on the cliff path](/uploads/2026/cliff.jpg "Kwahu, the morning after the storm")
```

renders as a real `<figure>` with `<figcaption>`, picking up the existing MINT caption styling.

This serves new writing. Existing posts use raw `<img>` HTML and will not be retroactively
converted, which is correct: the old posts are notes, the new ones are photo essays.

### 1.5 Feeds

Confirm the built site emits `/feed.xml` (RSS) and `/feed.json` (valid JSON Feed). The footer
already links `/feed.xml`, which currently generates nothing.

### 1.6 Editor bake-off

Deploy to a preview URL and stand up **Sveltia CMS** and **Pages CMS** against the same repo.
Kay writes one real photo post with a caption in each, from his phone. He picks one. The other is
removed. The differentiator is image and caption handling, since that is the writing he wants to do.

Hosting for the static site: **Cloudflare Pages, git-connected**, so a publish from the editor
triggers a rebuild by itself. Reversible: Vercel works equally well. Git-connected deploys must be
verified to actually fire, since the equivalent hook is known-broken on the `remix-knod-ai` repo.

### 1.7 Cutover

In this order:

1. New site live on a preview URL, images verified, feeds verified.
2. Point nanakofiwrites.com at the new host.
3. Fetch `https://nanakofiwrites.com/feed.json` and validate it as JSON Feed.
4. Refresh the Source in Micro.blog and confirm it reads the feed.
5. Publish one real post and watch it reach Bluesky and Mastodon.
6. Only then consider deleting the Micro.blog-hosted blog. Deferring indefinitely is fine.

## Movement 2: get the apps back

Adds Indiekit so the Micro.blog app and Sunlit post to Kay's own site.

- Deploy Indiekit (Node 24.17+, persistent public URL, Docker or PM2) with `preset-hugo`,
  `store-github` pointed at `hankmint/blog`, `endpoint-micropub`, `endpoint-media`, `endpoint-auth`,
  and `post-type-photo`.
- Provision MongoDB (Atlas free tier is sufficient) for syndication, post editing and media
  management.
- Add IndieAuth discovery to the site head so the apps can sign in.
- Verify by publishing a real photo story from Sunlit and confirming it lands as a commit, builds,
  and appears with images intact.
- Optionally enable Indiekit's own Bluesky and Mastodon syndicators. Micro.blog's relay stays either
  way for the networks Indiekit does not reach.

If Indiekit is ever down, the blog is unaffected and Kay can still write in the browser editor.

## Risks

| Risk | Severity | Mitigation |
| --- | --- | --- |
| Photos lost with the Micro.blog blog | Critical, irreversible | Download all 28 first, verify, before any other step |
| `/feed.json` missing or invalid after cutover | High, fails silently | Copy Micro.blog's own output-format config; validate the live URL and watch one real post syndicate |
| Images 404 due to the relative-path trap | High, visible | Rewrite to absolute paths; assert zero 404s in the build check |
| Indiekit server down | Medium | Sequenced second, never in the critical path; browser editor is the fallback |
| Cloudflare git-connected deploys not firing | Medium | Verify a real editor commit triggers a rebuild before cutover |
| iCloud `* 2` duplicate files breaking builds | Low | Delete them in 1.2 |

## Success criteria

1. nanakofiwrites.com serves the MINT design, in light and dark mode.
2. Every post Kay chooses to keep is present at its original URL. No permalink changes, no
   redirects needed. (18 posts carry over unless the three April 2025 test posts are dropped.)
3. All 28 photographs served from Kay's own domain. Zero 404s. No dependency on Micro.blog's CDN.
4. `/feed.json` validates as JSON Feed and `/feed.xml` as RSS.
5. A real post published after cutover reaches Bluesky and Mastodon via the existing Micro.blog
   Source, with no settings changed on that page.
6. Kay can publish a photo post with a caption from his phone.
7. (Movement 2) A Sunlit photo story publishes to nanakofiwrites.com.

## Out of scope

- Redesigning the theme. The MINT design is settled and approved.
- Newsletters, podcasts, bookshelves, or the other Micro.blog features Kay does not use.
- Migrating replies or the Micro.blog social graph. Followers and timeline are unaffected by this
  move and stay on Micro.blog.
- Building a Micropub server from scratch. Movement 2 uses Indiekit.

## Open questions

None blocking. Two to settle during implementation:

1. Sveltia versus Pages CMS, decided by the bake-off in 1.6.
2. Where Indiekit is hosted (Fly.io, Railway, Render or a VPS), decided at the start of Movement 2.
3. Whether to keep the three April 2025 test posts, and which of the five Micro.blog scaffolding
   pages to carry over. Both are Kay's calls, made during 1.2. Default is to keep everything, since
   keeping is reversible and deleting a live URL is not.
