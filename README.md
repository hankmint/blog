# MINT by Nana Kofi

The custom [Micro.blog](https://micro.blog/) theme behind [nanakofiwrites.com](https://nanakofiwrites.com/).

An editorial, long-form personal blog: one voice across **tech, business, and the creative**. Serif typography, a warm monochrome palette with a deep oxblood accent, full dark mode, a latest-blurb plus year-index homepage, topic archives, and a photo gallery with a lightbox.

Based on the [Arabica theme](https://github.com/slunsford/arabica) (MIT). Attribution retained in `LICENSE`, `theme.toml`, and the site footer.

## How this connects to Micro.blog

The site is hosted on Micro.blog. This repo holds only the **theme** (the look). Posts and photos live in Micro.blog and are never touched by theme changes.

- Words are posted from the Micro.blog app.
- Photo stories are posted from **Sunlit**, which publishes to Micro.blog over Micropub.

## Editing workflow

1. Edit templates in `layouts/`, styles in `static/css/`, or scripts in `static/js/`.
2. Commit and push to `main`.
3. In Micro.blog: **Design → Edit Custom Themes**, then **Update** to resync from GitHub.

To register this theme the first time: **Design → Edit Custom Themes → New Theme**, paste the Clone URL `https://github.com/hankmint/blog.git`, save, and select it.

**Rollout rule:** validate every change on a Micro.blog **test blog** before applying it to the live site.

## Local preview

This is a theme, not a full site. To preview locally, mount it in a small Hugo site as `themes/mint`, add a stub `layouts/partials/microblog_head.html` (Micro.blog supplies the real one), and run `hugo server`.

## Structure

- `layouts/`: templates (home, post, list/topic, gallery, about, partials).
- `static/css/`: `fonts.css` (self-hosted Fraunces + Newsreader) and `mint.css` (the editorial stylesheet).
- `static/js/`: `mint.js` (dark-mode toggle and gallery lightbox).
- `static/fonts/`: self-hosted woff2 (no external font requests).
- `config.json`, `plugin.json`, `theme.toml`: theme metadata and defaults.

## Credits

- [Arabica](https://github.com/slunsford/arabica) by Sean Lunsford, and its Hugo port for Micro.blog.
- [Hugo](https://gohugo.io/) and [Micro.blog](https://micro.blog/).
- Fonts: [Fraunces](https://github.com/undercasetype/Fraunces) and [Newsreader](https://github.com/productiontype/Newsreader), both OFL.

## License

MIT. See [LICENSE](LICENSE).
