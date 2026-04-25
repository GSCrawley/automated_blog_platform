# PR #6 — Human-in-the-loop publish + edit UI (handoff for Claude Code)

## Why this PR exists

Automated generation + QA will get articles close to publishable. But the
user wants to review, edit, and click-to-publish every article, and also
be able to edit articles that are already live on Ghost. This PR adds that
surface and makes it the *only* path from the pipeline to the live blog.

This PR depends on PR #1 (Ghost publisher shipped), PR #2 (verdict schema),
PR #3 (durable state), and PR #4 (CRUD + dashboard wiring). Do PR #6 last.

## Guiding principles

- **No autonomous publish.** Remove any code path that calls
  `POST /api/publisher/publish/<id>` from the pipeline itself. Only a
  signed-in user click can trigger it. The pipeline's terminal state is
  `editorial_verdict == "PUBLISH"` + `current_stage == "awaiting_human_review"`.
- **Local DB is the source of truth.** On publish and on post-publish
  update, the app writes to its own `articles` row first, then pushes to
  Ghost, then stores `ghost_post_id` + `published_url` + a new
  `ghost_updated_at` + `last_ghost_sync_hash`. On pull-from-Ghost the
  local row is overwritten with whatever Ghost currently has.
- **Drift-safe.** If a post is edited directly in Ghost Admin (bypassing
  our UI), the next pull detects the divergence and asks the user which
  side wins.
- **Explicit preview.** "What Ghost will receive" is always visible as the
  final HTML payload, not just the editor draft.

## Scope

### 6.1 Backend — new routes

Add `automated-blog-system/src/routes/review.py` and register at
`/api/review` in `main.py`.
```
GET  /api/review/queue
  Articles with editorial_verdict='PUBLISH' and status != 'published'.
  Returns the same fields as /api/articles plus
  editorial_report (latest EditorialReport row), section_count, word_count.

GET  /api/review/<article_id>
  Full article payload + latest editorial report + Ghost preview payload.
  Preview is produced by GhostService._article_to_post() without sending.

PATCH /api/review/<article_id>
  User edits before publish. Accepts any subset of:
  title, slug, content, sections, summary, meta_description, keywords,
  calls_to_action, meta.feature_image, meta.meta_title.
  Writes to the Article row; bumps updated_at; re-derives
  Article.to_headless_contract() lazily.

POST /api/review/<article_id>/publish
  The one human-triggered publish path. Internally calls the existing
  POST /api/publisher/publish/<id>. Returns { url, post_id, ghost_status }.

POST /api/review/<article_id>/unpublish
  Calls Ghost to set status='draft'. Local Article.status='draft'.

GET  /api/review/<article_id>/ghost
  Pulls the live post from Ghost by ghost_post_id. Returns the Ghost JSON
  alongside the local row. Includes a drift_detected boolean and a diff
  summary (which fields differ).

POST /api/review/<article_id>/pull-from-ghost
  Overwrites local row with Ghost's version. Records the previous local
  state as an `article_revisions` row (create the table in PR #3 if not
  already present; otherwise add here with a minimal migration).

POST /api/review/<article_id>/push-to-ghost
  Pushes the current local row to Ghost via
  GhostService.update_article(ghost_post_id, ...).
  Requires the article to already have a ghost_post_id.
```

All routes require `editorial_verdict == "PUBLISH"` for
`publish` / `push-to-ghost`, matching the PR #1 refusal pattern.

### 6.2 Backend — drift detection

In `GhostService` add:
```python
def fetch_post(self, post_id: str) -> dict:
    return self._get(f"/ghost/api/admin/posts/{post_id}/")["posts"][0]
```

`/api/review/<id>/ghost` computes drift by hashing the normalized
(title + html + meta_description + tags) from both sides and comparing.
Store `last_ghost_sync_hash` on the Article so cheap "is this in sync?"
checks don't need a network call.

### 6.3 Frontend — pre-publish review screen

`blog-frontend/src/components/ReviewQueue.jsx` — lists articles with
verdict `PUBLISH` that haven't been published yet. Sortable by
`updated_at`, filterable by niche.

`blog-frontend/src/components/ArticleReview.jsx` — the main workhorse.
Layout:
```
┌──────────────────────────────────────────────────────────────────┐
│  [Back to queue]     Title: ____________________________ [Save]  │
│  Slug: ___________       Niche: __________    Verdict: PUBLISH ●  │
├──────────────────────────────────────────────────────────────────┤
│ Left column (55%)                   Right column (45%)            │
│ ─────────────────                   ────────────────────          │
│ Tabs: [Editor][Sections][CTAs][SEO] │  Editorial Report           │
│                                     │  Content    8.2  ✓          │
│ Rich-text editor (Tiptap / SimpleMDE│  SEO/UX     7.9  ✓          │
│ / Lexical — pick smallest footprint)│  Monetize   7.1  ✓          │
│                                     │  Compliance 10   ✓          │
│ Sections tab: drag-reorderable list │  [checklist items below]    │
│ of {heading, content} — matches     │                             │
│ Headless Article Contract           │  Ghost Preview              │
│                                     │  (iframe srcdoc = final     │
│ CTAs tab: table of calls_to_action  │   HTML payload from         │
│   type | target | anchor | [delete] │   GhostService preview)     │
│   [+ Add CTA]                       │                             │
│                                     │  Cost so far: $0.47         │
│ SEO tab: meta_title, meta_desc      │  Attempts: 1                │
│   (char counts + warnings), tags,   │                             │
│   feature_image URL                 │                             │
├──────────────────────────────────────────────────────────────────┤
│  [Save Draft]   [Publish to Ghost ▶]   [Unpublish]   [Discard]    │
└──────────────────────────────────────────────────────────────────┘
```

Behaviors:

- Save Draft → `PATCH /api/review/<id>` with the edited fields.
  Autosave every 30s while the tab is focused.
- Publish to Ghost → confirmation modal showing the exact Ghost payload
  (title, slug, HTML first 500 chars, tags, meta) with **Confirm publish**
  and **Cancel**. On confirm → `POST /api/review/<id>/publish`. On
  success show toast + live URL as a clickable link; row moves out of
  the queue.
- Publish button is disabled if verdict !== `PUBLISH` or if there are
  unsaved edits (force Save first).
- Discard → revert to server state without saving.

### 6.4 Frontend — post-publish edit screen

`blog-frontend/src/components/PublishedArticles.jsx` — lists articles
with `status === "published"`. Columns: title, niche, published_url (link),
ghost_updated_at, drift indicator (● green / ● yellow / ● red).

Clicking a row opens a re-use of `ArticleReview.jsx` with three differences:

- A **Pull from Ghost** button that calls
  `POST /api/review/<id>/pull-from-ghost` and repopulates the editor.
  Shows a confirm modal if local has unsaved edits.
- The primary action button becomes **Push to Ghost** (calls
  `/api/review/<id>/push-to-ghost`).
- A **Drift** panel in the right column: if `drift_detected`, lists the
  diverging fields and offers **Keep local** / **Keep Ghost** / **Manual
  merge** (which loads the Ghost version into a side-by-side diff view).

### 6.5 Frontend — remove the old direct-publish button

In PR #4 the article row has a "Publish to Ghost" button. In PR #6 that
button becomes "Review & Publish" and routes to `ArticleReview.jsx`.
There is no longer a one-click publish from the list.

### 6.6 Drift detection details

On dashboard load, for each `status === "published"` article:

- If `last_ghost_sync_hash` is `None` or older than 24h, fire
  `GET /api/review/<id>/ghost` in the background (rate-limited, parallel
  fan-out capped at 4) and update the indicator.
- On explicit click, always fetch fresh.

### 6.7 Permissions note

Assumption: single-user system for now. Leave a `TODO(multi-user)` near
the `publish` route noting that in a multi-tenant future, only users with
role `publisher` may trigger that endpoint.

## Acceptance tests

Backend (`automated-blog-system/test_review_routes.py`):

1. **Verdict gate.** `POST /api/review/<id>/publish` returns 409 for
   articles with `editorial_verdict != "PUBLISH"`.
2. **PATCH round-trip.** PATCH updates title + sections; subsequent GET
   reflects the change; `Article.to_headless_contract()` returns the
   updated payload.
3. **Publish path.** With Ghost mocked via `responses`, a PUBLISH-verdict
   article PATCHed and then published lands on Ghost with the edited
   content (assert the mock's received request body).
4. **Pull-from-Ghost.** Mock Ghost returning a post with a changed title;
   calling pull-from-Ghost overwrites local title and stores a revision
   record of the prior state.
5. **Drift.** Mock Ghost returning divergent HTML → `drift_detected: true`
   + a non-empty diff.
6. **Push-to-Ghost.** Local edits since last sync are pushed via
   `GhostService.update_article`, and `last_ghost_sync_hash` updates.
7. **No autonomous publish.** Grep the `core/` directory; nothing calls
   `/api/publisher/publish` or `GhostService.publish_article` outside
   `routes/review.py` and `routes/publisher.py`. (Add a test that fails if
   a new call site appears.)

Frontend (Playwright or Vitest + RTL — one test per flow):

1. Open review queue → open article → edit title → Save → confirm
   persisted.
2. Attempt publish without saving edits → button disabled, warning shown.
3. Confirm publish flow shows the exact Ghost payload in the modal.
4. Published list shows drift indicator when Ghost mock returns
   divergent data.

Manual end-to-end (must be performed, notes in PR description):

1. Generate an article via the pipeline → lands in Review Queue.
2. Edit the monetization CTA inline → Save → Publish.
3. Live URL opens the Ghost post with the edit visible.
4. Edit the Ghost post directly in Ghost Admin (title change).
5. Return to dashboard → drift indicator red on that row.
6. Pull from Ghost → local matches → Push a new local edit → Ghost
   reflects it.

## Out of scope for PR #6

- Realtime collaboration / multiplayer editing.
- Scheduled publish (easy to add later — Ghost supports `status=scheduled`
  with a `published_at` in the future).
- Rich media upload to Ghost (images still referenced by URL; image upload
  can come as PR #7 if needed).
- Multi-author workflow / role-based permissions (TODO marker only).

## Libraries suggestion

- Rich text editor: **Tiptap** (React-native, headless, easy HTML in/out,
  ~80KB gzipped). Avoid full Lexical unless you want its complexity.
- Diff view for drift manual-merge: **react-diff-viewer-continued**.
- Toasts: whatever the existing dashboard uses (likely Radix +
  `sonner` or similar — check `blog-frontend/package.json` first).

## Acceptance command
```
pytest -q test_ghost_publisher.py -k "not live" \
  && pytest -q test_editor_verdict.py \
  && pytest -q test_pipeline_state.py \
  && pytest -q test_article_crud.py \
  && pytest -q test_knowledge_base.py \
  && pytest -q test_review_routes.py
```

All green, plus the frontend test suite, plus the manual end-to-end
documented above.