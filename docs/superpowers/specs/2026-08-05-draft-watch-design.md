# Design: Making an unpublished draft impossible to miss

**Date:** 2026-08-05
**Author:** Nana Kofi (Kay) with Claude
**Status:** Implemented, then **partly reversed on 2026-08-07**. See the amendment at the end
before trusting anything below about the default.
**Relates to:** `2026-07-28-selfhost-migration-design.md`, which introduced the Sveltia editor and
the `draft` switch this design is about.

## Context

On 2026-08-02, Kay wrote a full weekend post on his phone: seven photographs, the boat coming off
the beach, Lewandowski at Soldier Field, the ride home through Lollapalooza. He saved it. It never
appeared on the site. He did not find out for three days, and when he did, the symptom he reported
was "it just spun and nothing happened."

Nothing spun. Nothing failed. The system did exactly what it was built to do, and told him nothing.

This design does not change what the system does. It changes what it says.

## What actually happened

Reconstructed from the commit history on `main`, not from memory.

| Time (UTC) | Commit | What it did |
|---|---|---|
| 15:21:01 | `05a2caf` | `Create Post "59a634c47f58" +7`. The post plus seven photographs. `draft: true`. |
| 15:21:38 | `3e1115e` | `Update Post`. Set `share_image` to `IMG_2851.jpeg`. Still `draft: true`. |
| 15:22:48 | `fd6bd01` | `Update Post`. **Zero files changed. An empty commit.** |

That third commit is the moment Kay describes. He saved again, the editor committed successfully,
and the commit contained nothing, because the draft switch had never been moved and there was
therefore nothing to save. The editor reported success. The site did not change. Both were correct
and the combination was indistinguishable from a hang.

The post remains at `content/2026/08/02/59a634c47f58/index.md` with `draft: true`. Hugo excludes
drafts, so `https://nanakofiwrites.com/2026/08/02/59a634c47f58/` returns 404 as of 2026-08-05.

**The deploy pipeline was never at fault.** The 2026-07-31 phone layout fix (`2d20a93`) is live:
`mint-index-first` is present in the HTML served at `/posts/`. Cloudflare has been building and
deploying normally throughout.

## Verified findings

Checked against the vendored bundle at `static/admin/sveltia-cms.js`, pinned to 0.176.0 in
`static/admin/VERSION`. Not taken from documentation, which does not cover this.

### The draft switch is the last thing you see, not the first

Fields render in the order they are declared. In the current `config.yml` the `draft` field is
declared third, after `title` and before `date`. On a phone that puts the single most consequential
control below the fold at the moment you open a post to write in it.

### `view_filters` and `view_groups` cannot currently have a default

The bundle resolves both through one helper:

```js
M6 = (e, t) => {
  if (Array.isArray(e)) return { options: e };          // array form: NO default possible
  if (g(e)) {
    let n = e[t], r = e.default;                        // object form: e.groups / e.filters
    if (Array.isArray(n)) {
      let e = r ? n.find(({ name }) => name === r) : undefined;
      return { options: n, default: e ? { field: e.field, pattern: e.pattern } : undefined };
    }
  }
  return { options: [] };
}
```

Two consequences, both currently biting:

1. Written as a **plain array**, as `config.yml` does today, the helper returns `{options}` with no
   `default` at all. The grouping exists but is never applied on open.
2. The `default` value is matched against each option's **`name`** key. The existing options declare
   only `label`. Even converted to object form, a default would match nothing without adding `name`.

So the Draft/Published grouping already in the config has never once been active. It was written,
committed, and silently did nothing. This is the same class of failure as the post itself.

### Where the safety work belongs

`.github/workflows/optimise-images.yml` establishes the pattern and states the reason in its own
header: the editor commits straight to GitHub, so nothing on Kay's machine runs on the way in, and
making the editor wait is not acceptable on a phone. Safety work therefore runs *after the fact*, in
Actions, and commits or reports back. This design follows that precedent rather than inventing a
second one.

## Design

Three layers. Two are one workflow with two triggers; the third is configuration only.

### Layer 1 and 3: `draft-watch`, one workflow, two triggers

`.github/workflows/draft-watch.yml`

**Triggers**
- `push` to `main` on paths `content/**`. This is the within-a-minute signal, fired by the same
  commit the editor just made.
- `schedule`, daily. This is the nudge for anything left sitting.
- `workflow_dispatch`, so it can be run by hand during implementation and testing.

**Permissions:** `issues: write`, `contents: read`. Nothing more.

**Behaviour.** Scan every `content/**/*.md` for `draft: true` in the YAML frontmatter, then maintain
**exactly one** issue carrying the label `draft-watch`:

| Drafts found | Open `draft-watch` issue | Action |
|---|---|---|
| one or more | none | Open one |
| one or more | exists | Edit that issue's title and body in place |
| none | exists | Close it with a comment |
| none | none | Do nothing, exit 0 |

Reusing a single issue is deliberate. A notification system that accumulates is one you learn to
dismiss without reading, and this one has to still work in six months.

**Issue content.** The title states the count and the plain fact, for example
`1 post written and NOT live`. The body lists, per draft: its date, its title or `(untitled)`, the
first line of its body as a reminder of which post this is, its file path, and a direct link that
opens it in the editor.

**Closing is publishing.** Nothing has to be dismissed by hand. Turning the switch off and saving
pushes a commit, the workflow runs, no drafts are found, and the issue closes itself.

### Layer 2: configuration only, in `static/admin/config.yml`

1. **Move `draft` to the top of `fields`**, above `title`, so it is the first control on screen.
2. **Relabel it.** From `Draft — keep this to myself` to a label that states the current condition
   rather than an intention, for example `NOT LIVE. Turn off to publish.` The existing hint text is
   accurate and stays.
3. **Rewrite `view_filters` and `view_groups` into object form** with `name` keys on every option
   and a `default`, so grouping by status is active when the list opens rather than merely declared.

Grouping is chosen over filtering deliberately. A default *filter* of Drafts would hide published
posts and make ordinary editing require clearing it first. Grouping separates drafts to their own
heading while leaving everything reachable.

### Explicitly not built

- **No Resend, no Telegram, no Slack.** GitHub's own notification carries this. Every additional
  channel is another credential to rotate and another thing that can fail quietly, which is the
  exact failure mode being fixed.
- **No change to the safe default.** `draft` still defaults to `true`. Save still keeps things
  private. The door stays locked; this design only puts the key at eye level and hangs a bell on it.
- **No issue per draft.** One issue, reused.
- **No touching `crosspost`.** It remains `false` by default and is Kay's decision alone.

## Success criteria

Verified against the real August 2nd post, which is a genuine draft sitting in the repository. No
fixture is invented.

1. Running the workflow by hand, with the August 2nd post still in draft, opens exactly one issue
   labelled `draft-watch`, naming that post with its date and opening line.
2. Running it a second time with no change edits that same issue and does **not** open a second one.
3. Opening the editor on a phone shows the NOT LIVE switch without scrolling.
4. Opening the Posts list shows drafts under their own heading, on open, with no interaction.
5. Turning the switch off and saving closes the issue automatically, and the post appears on the
   live site at a real URL.
6. `scripts/verify-site.sh` still passes.

## Open decisions, deferred

- **The August 2nd post has an empty title and the slug `59a634c47f58`.** By the config's own rule
  an empty title makes it a Micro post, a short note. The body is **353 words** with seven
  photographs, which also clears the 300 word threshold at which a titled Post is featured on the
  front page. It almost certainly wants a title and a readable slug. Decided separately, with Kay,
  at publish time. It is not part of this design.
- **The post contains four typos** (`Pueto Rican`, `Lewandoski`, `solder field`, and
  `stuck on the beach for a couple of weeks not had finally been moved`). Kay's words, Kay's call.

---

## Amendment, 2026-08-07: the default was wrong

Two days after this shipped, Kay opened the same post, saw the switch, and it still had not gone
live. His words: "i cant come here and fix things i need to complete all in my cms, i need a simple
button for publish or post."

**The design above treated visibility as the fix. It was not.** Moving the switch to the top of the
form and relabelling it "NOT LIVE" made the state legible, and legible was still not enough, because
the failure is not that he cannot see the switch. It is that publishing was a second, separate act
after finishing the writing, and a second act performed on a phone at the end of a weekend is an act
that does not happen.

**What changed.** `draft` now defaults to **false**. Save publishes. The switch stays, first in the
form, for the rare case of deliberately holding something back.

**Why this is not simply reintroducing the risk.** The two failure modes do not cost the same:

- A finished post silently invisible costs days, and is only ever found by accident.
- A half-written post briefly visible on a personal blog costs nothing, and is undone by turning the
  switch on and saving again.

Nothing is broadcast either way. `crosspost` is a separate field, still defaults to `false`, and
sending genuinely cannot be undone. **That switch stays locked. This one does not need to be.**

`draft-watch.yml` and `find-drafts.py` are unchanged and still correct: anything left switched on
still opens an issue. The bell stays on the door. The door is simply unlocked now.

## Also fixed on 2026-08-07: the title lie, and what it had infected

Kay's second correction was "no title shouldnt make it a microblog," and he was right.
`split-posts.html` sorts on `.WordCount` against `featuredMinWords` (300) and says so in its own
comment. **A title has never decided Posts versus Micro.** But the editor's own hint claimed it did,
and that false belief had been copied into two other places, both of which broke on the untitled
353-word post:

| Place | What it did | Fixed to |
|---|---|---|
| `config.yml` title hint | Claimed an empty title makes it a Micro post | States that length decides |
| `head.html` `<title>` | Rendered the browser tab as `M I N T -`, separator dangling | Falls back to the site title, matching `og:title`, which already did |
| `post/single.html` older/newer | Filtered the chain on `Title != ""`, so an untitled post had no neighbours and was skipped in everyone else's | Walks `(partial "split-posts.html" .).long`, one definition of a Post |
| `post/single.html` pager label | Printed an empty `<span class="nxt">` under "Next" | Falls back to the opening line, as the index and share button already do |

**One definition of a Post, in one file.** Anything that needs to know what a Post is asks
`split-posts.html`. Nothing else is allowed a private opinion about it.
