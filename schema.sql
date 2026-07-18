-- Story Bible MCP — SQLite schema
-- Purpose: shared authoring store for multi-agent fiction work (author AIs write,
--   editor AIs comment/propose). Every content write is an immutable revision.
-- Side effects: none (DDL only, applied idempotently by server.py at boot).

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS projects (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    description TEXT DEFAULT '',
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);

-- Structural entities: arc | narrative | character | faction | lore | event | research | note
CREATE TABLE IF NOT EXISTS entities (
    id          TEXT PRIMARY KEY,
    project_id  TEXT NOT NULL REFERENCES projects(id),
    kind        TEXT NOT NULL,
    name        TEXT NOT NULL,
    summary     TEXT DEFAULT '',
    content_md  TEXT DEFAULT '',
    rev         INTEGER NOT NULL DEFAULT 1,
    sort_order  INTEGER DEFAULT 0,
    deleted     INTEGER NOT NULL DEFAULT 0,
    created_by  TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);

-- Prose chapters (same revisioning model as entities, kept separate for ordering/status)
CREATE TABLE IF NOT EXISTS chapters (
    id          TEXT PRIMARY KEY,
    project_id  TEXT NOT NULL REFERENCES projects(id),
    title       TEXT NOT NULL,
    content_md  TEXT NOT NULL DEFAULT '',
    status      TEXT NOT NULL DEFAULT 'draft',   -- draft | revised | final
    rev         INTEGER NOT NULL DEFAULT 1,
    sort_order  INTEGER DEFAULT 0,
    deleted     INTEGER NOT NULL DEFAULT 0,
    created_by  TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);

-- Immutable revision history for entities and chapters. Never UPDATE/DELETE rows here.
CREATE TABLE IF NOT EXISTS revisions (
    id          TEXT PRIMARY KEY,
    target_type TEXT NOT NULL,                    -- entity | chapter
    target_id   TEXT NOT NULL,
    rev         INTEGER NOT NULL,
    content_md  TEXT NOT NULL,
    note        TEXT DEFAULT '',
    created_by  TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    UNIQUE(target_type, target_id, rev)
);
CREATE INDEX IF NOT EXISTS idx_revisions_target ON revisions(target_type, target_id, rev);

-- Typed links between any two entities/chapters (arc→character, character→faction, ...)
CREATE TABLE IF NOT EXISTS links (
    id          TEXT PRIMARY KEY,
    project_id  TEXT NOT NULL REFERENCES projects(id),
    from_id     TEXT NOT NULL,
    to_id       TEXT NOT NULL,
    rel_type    TEXT NOT NULL,                    -- e.g. "protagonist_of", "member_of", "occurs_in"
    note        TEXT DEFAULT '',
    created_by  TEXT NOT NULL,
    created_at  TEXT NOT NULL
);

-- Threaded comments on any entity or chapter, optionally anchored to a quoted span.
CREATE TABLE IF NOT EXISTS comments (
    id           TEXT PRIMARY KEY,
    target_type  TEXT NOT NULL,
    target_id    TEXT NOT NULL,
    parent_id    TEXT REFERENCES comments(id),
    anchor_quote TEXT DEFAULT '',
    body         TEXT NOT NULL,
    status       TEXT NOT NULL DEFAULT 'open',    -- open | resolved
    created_by   TEXT NOT NULL,
    created_at   TEXT NOT NULL,
    resolved_by  TEXT,
    resolved_at  TEXT
);
CREATE INDEX IF NOT EXISTS idx_comments_target ON comments(target_type, target_id);

-- Scenes: ordered atomic prose units under a chapter. Optional layer — a chapter
-- with no scenes keeps using its own content_md, so scene-less projects work as before.
CREATE TABLE IF NOT EXISTS scenes (
    id            TEXT PRIMARY KEY,
    project_id    TEXT NOT NULL REFERENCES projects(id),
    chapter_id    TEXT NOT NULL REFERENCES chapters(id),
    title         TEXT NOT NULL DEFAULT '',
    synopsis      TEXT DEFAULT '',
    content_md    TEXT NOT NULL DEFAULT '',
    status        TEXT NOT NULL DEFAULT 'outline',  -- outline | draft | revised | final
    pov_entity_id TEXT,                             -- optional pointer to a character entity
    sort_order    INTEGER DEFAULT 0,
    rev           INTEGER NOT NULL DEFAULT 1,
    deleted       INTEGER NOT NULL DEFAULT 0,
    created_by    TEXT NOT NULL,
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_scenes_chapter ON scenes(chapter_id, sort_order);
CREATE INDEX IF NOT EXISTS idx_scenes_project ON scenes(project_id);

-- Generic per-node metadata: tags, aliases, story-time stamps, word targets —
-- any typed key/value an author or AI wants to hang on a node.
CREATE TABLE IF NOT EXISTS node_meta (
    target_type TEXT NOT NULL,                -- project | entity | chapter | scene
    target_id   TEXT NOT NULL,
    key         TEXT NOT NULL,
    value       TEXT NOT NULL DEFAULT '',
    updated_by  TEXT NOT NULL,
    updated_at  TEXT NOT NULL,
    PRIMARY KEY (target_type, target_id, key)
);

-- Parts: optional grouping layer above chapters (Part → Chapter → Scene).
CREATE TABLE IF NOT EXISTS parts (
    id          TEXT PRIMARY KEY,
    project_id  TEXT NOT NULL REFERENCES projects(id),
    title       TEXT NOT NULL,
    sort_order  INTEGER DEFAULT 0,
    deleted     INTEGER NOT NULL DEFAULT 0,
    created_by  TEXT NOT NULL,
    created_at  TEXT NOT NULL
);

-- Locks: owner-enforced write protection. kind: content | personal_truth.
-- A locked target rejects every mutation until unlocked; attempts are recorded.
CREATE TABLE IF NOT EXISTS locks (
    target_type TEXT NOT NULL,
    target_id   TEXT NOT NULL,
    kind        TEXT NOT NULL DEFAULT 'content',
    reason      TEXT DEFAULT '',
    locked_by   TEXT NOT NULL,
    locked_at   TEXT NOT NULL,
    PRIMARY KEY (target_type, target_id)
);
CREATE TABLE IF NOT EXISTS lock_events (
    id           TEXT PRIMARY KEY,
    target_type  TEXT NOT NULL,
    target_id    TEXT NOT NULL,
    action       TEXT NOT NULL,              -- blocked_write | locked | unlocked
    attempted_by TEXT NOT NULL,
    detail       TEXT DEFAULT '',
    created_at   TEXT NOT NULL
);

-- Fact verifications: immutable, source-cited verdicts on research claims (spec H).
CREATE TABLE IF NOT EXISTS verifications (
    id           TEXT PRIMARY KEY,
    claim_id     TEXT NOT NULL,
    claim_rev    INTEGER NOT NULL,
    verdict      TEXT NOT NULL,              -- verified | false | disputed | unverifiable | outdated
    confidence   REAL DEFAULT 0,
    sources_json TEXT NOT NULL DEFAULT '[]',
    notes        TEXT DEFAULT '',
    created_by   TEXT NOT NULL,
    created_at   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_verifications_claim ON verifications(claim_id, created_at);

-- Fictionalization log: real fact ↔ deliberate invention, so inventions never
-- harden into remembered biography (spec 3.12).
CREATE TABLE IF NOT EXISTS fictionalizations (
    id            TEXT PRIMARY KEY,
    project_id    TEXT NOT NULL,
    real_fact     TEXT NOT NULL,
    invented_fact TEXT NOT NULL,
    rationale     TEXT DEFAULT '',
    target_type   TEXT DEFAULT '',
    target_id     TEXT DEFAULT '',
    created_by    TEXT NOT NULL,
    created_at    TEXT NOT NULL
);

-- Decisions: Joe's rulings — the authority trail (spec 3.13). Immutable.
CREATE TABLE IF NOT EXISTS decisions (
    id           TEXT PRIMARY KEY,
    project_id   TEXT NOT NULL,
    subject_type TEXT NOT NULL,              -- finding | proposal | claim | gate_override | canon | other
    subject_id   TEXT DEFAULT '',
    ruling       TEXT NOT NULL,
    rationale    TEXT DEFAULT '',
    decided_by   TEXT NOT NULL,
    created_at   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_decisions_project ON decisions(project_id, created_at);

-- Rebuttals: structured dissent against a finding or proposal (spec 3.13). Immutable.
CREATE TABLE IF NOT EXISTS rebuttals (
    id             TEXT PRIMARY KEY,
    target_kind    TEXT NOT NULL,            -- proposal | finding
    target_id      TEXT NOT NULL,
    body           TEXT NOT NULL,
    evidence_quote TEXT DEFAULT '',
    location       TEXT DEFAULT '',
    created_by     TEXT NOT NULL,
    created_at     TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_rebuttals_target ON rebuttals(target_kind, target_id);

-- Editorial analysis runs (spec §9/§10): one formal Sol review job + its result.
-- Immutable once complete; staleness is computed against current target revs.
CREATE TABLE IF NOT EXISTS analysis_runs (
    id               TEXT PRIMARY KEY,
    project_id       TEXT NOT NULL,
    analysis_type    TEXT NOT NULL,     -- scene_check | chapter_gate | part_audit |
                                        -- global_arc_audit | fact_check | second_opinion | cold_read
    target_type      TEXT NOT NULL,
    target_id        TEXT NOT NULL,
    target_rev       INTEGER NOT NULL,  -- pinned at creation
    pinned_json      TEXT DEFAULT '{}', -- profile/rubric revisions pinned for calibration
    status           TEXT NOT NULL DEFAULT 'queued',  -- queued | running | complete | cancelled
    model            TEXT NOT NULL DEFAULT 'gpt-5.6-sol',
    reasoning_effort TEXT NOT NULL DEFAULT 'max',
    advisory         INTEGER NOT NULL DEFAULT 0,      -- 1 for second_opinion / cold_read
    verdict          TEXT DEFAULT '',
    intent_summary   TEXT DEFAULT '',
    observed_summary TEXT DEFAULT '',
    scores_json      TEXT DEFAULT '{}',
    limitations_json TEXT DEFAULT '[]',
    requested_by     TEXT NOT NULL,
    created_at       TEXT NOT NULL,
    completed_by     TEXT,
    completed_at     TEXT
);
CREATE INDEX IF NOT EXISTS idx_runs_status ON analysis_runs(status, created_at);
CREATE INDEX IF NOT EXISTS idx_runs_target ON analysis_runs(target_type, target_id);

-- Findings (spec §10.4): evidence-anchored problems. Evidence is validated
-- server-side against the pinned revision content before acceptance.
CREATE TABLE IF NOT EXISTS findings (
    id                     TEXT PRIMARY KEY,
    run_id                 TEXT NOT NULL REFERENCES analysis_runs(id),
    project_id             TEXT NOT NULL,
    target_type            TEXT NOT NULL,
    target_id              TEXT NOT NULL,
    target_rev             INTEGER NOT NULL,
    severity               TEXT NOT NULL,   -- blocking | major | minor | watch
    category               TEXT DEFAULT '',
    confidence             REAL DEFAULT 0,
    evidence_quote         TEXT NOT NULL,
    location               TEXT DEFAULT '',
    explanation            TEXT NOT NULL,
    affected_entity_ids    TEXT DEFAULT '[]',
    smallest_intervention  TEXT DEFAULT '',
    status                 TEXT NOT NULL DEFAULT 'open',
                          -- open | accepted | resolved | intentional | deferred | incorrect
    status_note            TEXT DEFAULT '',
    created_at             TEXT NOT NULL,
    updated_by             TEXT,
    updated_at             TEXT
);
CREATE INDEX IF NOT EXISTS idx_findings_target ON findings(target_type, target_id, status);
CREATE INDEX IF NOT EXISTS idx_findings_project ON findings(project_id, status);

-- Strengths to protect (spec §10.5): evidence-anchored passages revisions must not flatten.
CREATE TABLE IF NOT EXISTS strengths (
    id             TEXT PRIMARY KEY,
    run_id         TEXT NOT NULL REFERENCES analysis_runs(id),
    project_id     TEXT NOT NULL,
    target_type    TEXT NOT NULL,
    target_id      TEXT NOT NULL,
    target_rev     INTEGER NOT NULL,
    evidence_quote TEXT NOT NULL,
    location       TEXT DEFAULT '',
    explanation    TEXT NOT NULL,
    created_at     TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_strengths_target ON strengths(target_type, target_id);

-- Mention index: where each entity's name/aliases appear in prose. Maintained
-- automatically on content writes; rebuildable via the mentions_rebuild tool.
CREATE TABLE IF NOT EXISTS mentions (
    project_id  TEXT NOT NULL,
    entity_id   TEXT NOT NULL,
    target_type TEXT NOT NULL,               -- entity | chapter | scene (where it appears)
    target_id   TEXT NOT NULL,
    count       INTEGER NOT NULL DEFAULT 0,
    updated_at  TEXT NOT NULL,
    PRIMARY KEY (entity_id, target_type, target_id)
);
CREATE INDEX IF NOT EXISTS idx_mentions_target ON mentions(target_type, target_id);

-- Ranked full-text search over entities/chapters/scenes, kept in sync by triggers.
CREATE VIRTUAL TABLE IF NOT EXISTS fts USING fts5(
    target_type UNINDEXED, target_id UNINDEXED, project_id UNINDEXED,
    name, body, tokenize='porter unicode61'
);

CREATE TRIGGER IF NOT EXISTS fts_entities_ai AFTER INSERT ON entities BEGIN
    INSERT INTO fts(target_type, target_id, project_id, name, body)
    SELECT 'entity', NEW.id, NEW.project_id, NEW.name || ' ' || NEW.summary, NEW.content_md
    WHERE NEW.deleted = 0;
END;
CREATE TRIGGER IF NOT EXISTS fts_entities_au AFTER UPDATE ON entities BEGIN
    DELETE FROM fts WHERE target_type='entity' AND target_id=NEW.id;
    INSERT INTO fts(target_type, target_id, project_id, name, body)
    SELECT 'entity', NEW.id, NEW.project_id, NEW.name || ' ' || NEW.summary, NEW.content_md
    WHERE NEW.deleted = 0;
END;
CREATE TRIGGER IF NOT EXISTS fts_entities_ad AFTER DELETE ON entities BEGIN
    DELETE FROM fts WHERE target_type='entity' AND target_id=OLD.id;
END;

CREATE TRIGGER IF NOT EXISTS fts_chapters_ai AFTER INSERT ON chapters BEGIN
    INSERT INTO fts(target_type, target_id, project_id, name, body)
    SELECT 'chapter', NEW.id, NEW.project_id, NEW.title, NEW.content_md
    WHERE NEW.deleted = 0;
END;
CREATE TRIGGER IF NOT EXISTS fts_chapters_au AFTER UPDATE ON chapters BEGIN
    DELETE FROM fts WHERE target_type='chapter' AND target_id=NEW.id;
    INSERT INTO fts(target_type, target_id, project_id, name, body)
    SELECT 'chapter', NEW.id, NEW.project_id, NEW.title, NEW.content_md
    WHERE NEW.deleted = 0;
END;
CREATE TRIGGER IF NOT EXISTS fts_chapters_ad AFTER DELETE ON chapters BEGIN
    DELETE FROM fts WHERE target_type='chapter' AND target_id=OLD.id;
END;

CREATE TRIGGER IF NOT EXISTS fts_scenes_ai AFTER INSERT ON scenes BEGIN
    INSERT INTO fts(target_type, target_id, project_id, name, body)
    SELECT 'scene', NEW.id, NEW.project_id, NEW.title || ' ' || NEW.synopsis, NEW.content_md
    WHERE NEW.deleted = 0;
END;
CREATE TRIGGER IF NOT EXISTS fts_scenes_au AFTER UPDATE ON scenes BEGIN
    DELETE FROM fts WHERE target_type='scene' AND target_id=NEW.id;
    INSERT INTO fts(target_type, target_id, project_id, name, body)
    SELECT 'scene', NEW.id, NEW.project_id, NEW.title || ' ' || NEW.synopsis, NEW.content_md
    WHERE NEW.deleted = 0;
END;
CREATE TRIGGER IF NOT EXISTS fts_scenes_ad AFTER DELETE ON scenes BEGIN
    DELETE FROM fts WHERE target_type='scene' AND target_id=OLD.id;
END;

-- Edit proposals: editor-role keys can't write content directly — they file these.
-- Accepting one creates a new revision on the target.
CREATE TABLE IF NOT EXISTS proposals (
    id                  TEXT PRIMARY KEY,
    target_type         TEXT NOT NULL,
    target_id           TEXT NOT NULL,
    base_rev            INTEGER NOT NULL,          -- revision the proposal was written against
    proposed_content_md TEXT NOT NULL,
    rationale           TEXT DEFAULT '',
    status              TEXT NOT NULL DEFAULT 'pending',  -- pending | accepted | rejected
    created_by          TEXT NOT NULL,
    created_at          TEXT NOT NULL,
    decided_by          TEXT,
    decided_at          TEXT,
    decision_note       TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_proposals_status ON proposals(status);
