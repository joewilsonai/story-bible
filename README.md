# Story Bible MCP

Shared fiction-authoring store for multiple AI clients. Claude authors, ChatGPT
edits, Joe drives by voice — all against one SQLite database over HTTP MCP.

## Why this exists

Off-the-shelf tools (Bookly/yokoi, Notion, Google Docs) either impose their own
structure, lack arcs/narratives as first-class objects, or let any connected
agent silently overwrite content. This server fixes all three:

- **Your schema:** arcs, narratives, characters, factions, lore, events,
  research, notes — plus prose chapters. Typed links between everything.
- **Real versioning:** every content write is an immutable, attributed revision.
  History is listable, readable, and restorable via MCP.
- **Author/editor roles:** editor keys (ChatGPT) cannot write content — they
  comment and file proposals. An author key accepts a proposal to make it a
  revision. Stale proposals (target moved underneath) are refused unless forced.

## Roles

| Capability                                 | author | editor |
| ------------------------------------------ | ------ | ------ |
| Read everything, search                    | yes    | yes    |
| Comment / resolve                          | yes    | yes    |
| Create proposals                           | yes    | yes    |
| Create/update/delete content               | yes    | no     |
| Accept/reject proposals, restore revisions | yes    | no     |

## Run

```bash
pip install -r requirements.txt
export STORYBIBLE_KEYS="joe:author:$(openssl rand -hex 24)"
export STORYBIBLE_KEYS="$STORYBIBLE_KEYS,luna:author:$(openssl rand -hex 24)"
export STORYBIBLE_KEYS="$STORYBIBLE_KEYS,chatgpt:editor:$(openssl rand -hex 24)"
python3 server.py   # port 8787, db at ~/.story-bible/story.db
```

Env vars: `STORYBIBLE_KEYS` (required, `name:role:key` comma-separated),
`STORYBIBLE_DB`, `STORYBIBLE_PORT`.

The server refuses to start with no keys configured. `GET /healthz` is the only
unauthenticated route.

## Deploy on Railway (recommended)

Railway gives instant HTTPS (required by ChatGPT's connector) with no
domain/Caddy setup:

1. New service → deploy from this repo (files are at the root;
   (Dockerfile is picked up automatically).
2. Attach a **volume** mounted at `/data` — the Dockerfile defaults
   `STORYBIBLE_DB=/data/story.db` so the database survives redeploys.
3. Set `STORYBIBLE_KEYS` in the service variables (three keys: two author, one
   editor — generate with `openssl rand -hex 24`).
4. Use the generated `https://<service>.up.railway.app/mcp` URL in both clients.

## Or self-host with TLS

ChatGPT requires HTTPS. On a box with a domain, put Caddy in front:

```text
story.yourdomain.com {
    reverse_proxy 127.0.0.1:8787
}
```

## Connect clients

**Claude Code** (author key):

```bash
claude mcp add --scope user --transport http story-bible \
  https://story.yourdomain.com/mcp \
  --header "X-API-Key: <luna-author-key>"
```

**ChatGPT** (editor key): Settings → Apps & Connectors → Advanced → Developer
mode → add custom MCP connector with URL `https://story.yourdomain.com/mcp` and
header `X-API-Key: <chatgpt-editor-key>`.

## Workflow

1. Author (Claude) writes: `chapter_create`, `entity_create` for arcs/characters,
   `link_create` to wire them together.
2. Editor (ChatGPT) reviews: `chapter_get`, then `comment_create` (quote-anchored
   notes) and `proposal_create` (full rewritten content + rationale).
3. Author reviews `proposal_list` / `proposal_get` (returns proposed and current
   content side by side), then `proposal_accept` or `proposal_reject`.
4. Anything can be undone: `revision_list` → `revision_restore` (restores by
   copying forward — history is never rewritten).

## Tool inventory (49)

- Projects: `project_create` `project_list` `project_get` `project_update` `project_delete`
  `project_stats`
- Entities: `entity_create` `entity_get` `entity_list` `entity_update` `entity_delete`
  `entity_appearances` — kinds: arc, narrative, character, faction, lore, event,
  research, note, location, item, theme, thread, style
- Links: `link_create` (typed + directional + optional `attrs` payload) `link_list` `link_delete`
- Chapters: `chapter_create` `chapter_get` `chapter_list` `chapter_update` `chapter_delete`
- Scenes: `scene_create` `scene_get` `scene_list` `scene_update` `scene_move` `scene_delete`
  — the atomic prose/metadata unit under a chapter (synopsis, status, POV pointer);
  scene-less chapters keep working unchanged
- Metadata: `meta_set` `meta_get` — typed key/values on any project/entity/chapter/scene
- Revisions: `revision_list` `revision_get` `revision_restore` (scenes included)
- Comments: `comment_create` `comment_list` `comment_resolve` (scenes included)
- Proposals: `proposal_create` `proposal_list` `proposal_get` `proposal_accept`
  `proposal_reject` (scenes included)
- Search: `search` — FTS5 ranked full-text (stemmed) with type filters + substring fallback
- Mentions: `mentions_rebuild` — name/alias mention index, auto-maintained on every
  content write (aliases via meta key `aliases`, comma-separated)
- Timeline: `timeline_list` — event entities ordered by `story_date` meta (story-time
  vs. manuscript order, deliberately independent)
- Structure: `template_list` `template_apply` — three_act, save_the_cat, heros_journey,
  story_circle beat scaffolds
- Context: `context_bundle` — one call assembling everything an AI co-writer needs
  before drafting a chapter/scene: style guides, POV sheet, entities on stage,
  prior-story synopses, open threads
- Export: `export_manuscript` (markdown | html | docx | epub) `export_list` — download
  via authed `GET /export/<file>`
- Backups: `backup_now` `backup_list` — timed on-volume `VACUUM INTO` snapshots +
  authed `GET /backup/latest?fresh=1` pull route (author keys)

## Meta-key conventions (read by context_bundle and friends)

| Key | On | Meaning |
| --- | --- | --- |
| `aliases` | entity | Comma-separated alternate names for mention detection |
| `ai_context` | entity | `always` / `detected` (default) / `never` — context inclusion |
| `reveal_after_chapter` | entity | Content withheld from bundles before chapter N (spoiler gate) |
| `story_date` | event entity | ISO-style sortable story-time stamp for `timeline_list` |
| `status` | thread entity | `planted` / `developing` / `paid_off` / `abandoned` |
| `target_words`, `deadline` | project | Drive `project_stats` progress/pace math |

Extra env vars: `STORYBIBLE_BACKUP_HOURS` (default 24; <=0 disables the timer),
`STORYBIBLE_BACKUP_KEEP` (default 14).

## Notes

- SQLite WAL, one connection per request — a crashed request can't wedge the DB.
- Deletes are soft; revisions and comments survive them.
- Attribution comes from the API key name, so every revision, comment, and
  proposal records who did it (joe / luna / chatgpt).
