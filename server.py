#!/usr/bin/env python3
"""
Story Bible MCP Server — shared multi-agent fiction authoring store.

Purpose:
    One SQLite-backed store that multiple AI clients (Claude, ChatGPT, anything
    MCP) read and write over HTTP MCP. Designed for an author/editor split:
    author-role keys have full write access; editor-role keys can read, comment,
    and file edit PROPOSALS but can never overwrite content directly.

Data model (schema.sql):
    projects → entities (arc/narrative/character/faction/lore/event/research/note)
             → chapters (prose, ordered, statused)
    revisions — immutable history; every content write bumps rev
    links     — typed edges between any two records (arc→character, ...)
    comments  — threaded, quote-anchored, open/resolved
    proposals — track-changes: editor proposes against a base rev; author
                accepts (creates new revision, stale-base guarded) or rejects

Auth:
    STORYBIBLE_KEYS env var: comma-separated "name:role:key" triples, e.g.
        STORYBIBLE_KEYS="joe:author:sk-abc,luna:author:sk-def,chatgpt:editor:sk-ghi"
    Clients send the key via X-API-Key header (or Authorization: Bearer).
    Every write is attributed to the key's name.

Inputs/outputs: JSON over MCP streamable-HTTP (stateless). GET /healthz is open.
Side effects: creates/updates STORYBIBLE_DB (default ~/.story-bible/story.db).
Failure behavior: unknown/missing key → 401 before any tool runs; tool-level
    errors return MCP errors with a human-readable message; the DB is opened
    per-request (WAL) so a crashed request never wedges the store.

Usage:
    STORYBIBLE_KEYS="..." python3 server.py            # serves on :8787
    claude mcp add --transport http story-bible https://host/mcp \
        --header "X-API-Key: sk-..."
"""

import contextvars
import os
import sqlite3
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

DB_PATH = Path(os.environ.get("STORYBIBLE_DB", "~/.story-bible/story.db")).expanduser()
SCHEMA_PATH = Path(__file__).parent / "schema.sql"
# STORYBIBLE_PORT wins; PORT is honored for Railway/Heroku-style platforms that inject it.
PORT = int(os.environ.get("STORYBIBLE_PORT") or os.environ.get("PORT") or "8787")

# On-volume snapshot settings. BACKUP_HOURS <= 0 disables the timer (tools still work).
BACKUP_DIR = DB_PATH.parent / "backups"
BACKUP_HOURS = float(os.environ.get("STORYBIBLE_BACKUP_HOURS", "24"))
BACKUP_KEEP = int(os.environ.get("STORYBIBLE_BACKUP_KEEP", "14"))

ENTITY_KINDS = {"arc", "narrative", "character", "faction", "lore", "event", "research", "note"}
CHAPTER_STATUSES = {"draft", "revised", "final"}

# caller identity for the current request: {"name": ..., "role": "author"|"editor"}
CALLER: contextvars.ContextVar[dict] = contextvars.ContextVar("caller")

# DNS-rebinding protection is for unauthenticated localhost servers; this one is
# API-key-gated and internet-facing (Railway edge sets Host to the public domain,
# which the SDK's default localhost allowlist 421s). Disabled unless
# STORYBIBLE_ALLOWED_HOSTS provides an explicit allowlist.
_allowed_hosts = [h.strip() for h in os.environ.get("STORYBIBLE_ALLOWED_HOSTS", "").split(",") if h.strip()]
_transport_security = (
    TransportSecuritySettings(enable_dns_rebinding_protection=True, allowed_hosts=_allowed_hosts)
    if _allowed_hosts
    else TransportSecuritySettings(enable_dns_rebinding_protection=False)
)

mcp = FastMCP("story-bible", stateless_http=True, json_response=True,
              transport_security=_transport_security)


# ---------------------------------------------------------------- helpers

def _load_keys() -> dict:
    """Parse STORYBIBLE_KEYS into {key: {"name":..., "role":...}}."""
    raw = os.environ.get("STORYBIBLE_KEYS", "")
    keys = {}
    for triple in filter(None, (t.strip() for t in raw.split(","))):
        try:
            name, role, key = triple.split(":", 2)
        except ValueError:
            print(f"[story-bible] bad key entry (want name:role:key): {triple!r}", file=sys.stderr)
            continue
        if role not in ("author", "editor"):
            print(f"[story-bible] bad role {role!r} for {name!r}", file=sys.stderr)
            continue
        keys[key] = {"name": name, "role": role}
    return keys


def _db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _init_db():
    with _db() as conn:
        conn.executescript(SCHEMA_PATH.read_text())


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id() -> str:
    return str(uuid.uuid4())


def _caller() -> dict:
    return CALLER.get({"name": "unknown", "role": "editor"})


def _require_author():
    c = _caller()
    if c["role"] != "author":
        raise PermissionError(
            f"'{c['name']}' has editor role: read, comment, and propose only. "
            "Use proposal_create to suggest this change."
        )


def _row(r: sqlite3.Row | None) -> dict | None:
    return dict(r) if r is not None else None


def _rows(rs) -> list[dict]:
    return [dict(r) for r in rs]


def _get_target(conn, target_type: str, target_id: str) -> sqlite3.Row:
    if target_type not in ("entity", "chapter"):
        raise ValueError("target_type must be 'entity' or 'chapter'")
    table = "entities" if target_type == "entity" else "chapters"
    row = conn.execute(f"SELECT * FROM {table} WHERE id=? AND deleted=0", (target_id,)).fetchone()
    if row is None:
        raise ValueError(f"{target_type} {target_id} not found")
    return row


def _write_revision(conn, target_type: str, target_id: str, content_md: str,
                    note: str, created_by: str) -> int:
    """Bump rev on the target row and record an immutable revision. Returns new rev."""
    table = "entities" if target_type == "entity" else "chapters"
    cur = conn.execute(f"SELECT rev FROM {table} WHERE id=?", (target_id,)).fetchone()
    new_rev = cur["rev"] + 1
    conn.execute(
        f"UPDATE {table} SET content_md=?, rev=?, updated_at=? WHERE id=?",
        (content_md, new_rev, _now(), target_id),
    )
    conn.execute(
        "INSERT INTO revisions (id, target_type, target_id, rev, content_md, note, created_by, created_at) "
        "VALUES (?,?,?,?,?,?,?,?)",
        (_id(), target_type, target_id, new_rev, content_md, note, created_by, _now()),
    )
    return new_rev


def _record_initial_revision(conn, target_type: str, target_id: str, content_md: str, created_by: str):
    conn.execute(
        "INSERT INTO revisions (id, target_type, target_id, rev, content_md, note, created_by, created_at) "
        "VALUES (?,?,?,1,?,'initial',?,?)",
        (_id(), target_type, target_id, content_md, created_by, _now()),
    )


# ---------------------------------------------------------------- projects

@mcp.tool()
def project_create(name: str, description: str = "") -> dict:
    """Create a project (a book or series). Author role required."""
    _require_author()
    with _db() as conn:
        pid = _id()
        conn.execute(
            "INSERT INTO projects (id, name, description, created_at, updated_at) VALUES (?,?,?,?,?)",
            (pid, name, description, _now(), _now()),
        )
        return _row(conn.execute("SELECT * FROM projects WHERE id=?", (pid,)).fetchone())


@mcp.tool()
def project_list() -> list[dict]:
    """List all projects."""
    with _db() as conn:
        return _rows(conn.execute("SELECT * FROM projects ORDER BY created_at"))


@mcp.tool()
def project_get(project_id: str) -> dict:
    """Get a project with entity/chapter counts by kind."""
    with _db() as conn:
        proj = _row(conn.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone())
        if proj is None:
            raise ValueError(f"project {project_id} not found")
        proj["entity_counts"] = {
            r["kind"]: r["n"]
            for r in conn.execute(
                "SELECT kind, COUNT(*) n FROM entities WHERE project_id=? AND deleted=0 GROUP BY kind",
                (project_id,),
            )
        }
        proj["chapter_count"] = conn.execute(
            "SELECT COUNT(*) n FROM chapters WHERE project_id=? AND deleted=0", (project_id,)
        ).fetchone()["n"]
        return proj


@mcp.tool()
def project_update(project_id: str, name: str | None = None, description: str | None = None) -> dict:
    """Update project name/description. Author role required."""
    _require_author()
    with _db() as conn:
        if conn.execute("SELECT 1 FROM projects WHERE id=?", (project_id,)).fetchone() is None:
            raise ValueError(f"project {project_id} not found")
        if name is not None:
            conn.execute("UPDATE projects SET name=?, updated_at=? WHERE id=?", (name, _now(), project_id))
        if description is not None:
            conn.execute("UPDATE projects SET description=?, updated_at=? WHERE id=?",
                         (description, _now(), project_id))
        return _row(conn.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone())


# ---------------------------------------------------------------- entities

@mcp.tool()
def entity_create(project_id: str, kind: str, name: str, summary: str = "",
                  content_md: str = "", sort_order: int = 0) -> dict:
    """Create a structural entity. kind: arc | narrative | character | faction |
    lore | event | research | note. Author role required."""
    _require_author()
    if kind not in ENTITY_KINDS:
        raise ValueError(f"kind must be one of {sorted(ENTITY_KINDS)}")
    who = _caller()["name"]
    with _db() as conn:
        if conn.execute("SELECT 1 FROM projects WHERE id=?", (project_id,)).fetchone() is None:
            raise ValueError(f"project {project_id} not found")
        eid = _id()
        conn.execute(
            "INSERT INTO entities (id, project_id, kind, name, summary, content_md, sort_order, "
            "created_by, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (eid, project_id, kind, name, summary, content_md, sort_order, who, _now(), _now()),
        )
        _record_initial_revision(conn, "entity", eid, content_md, who)
        return _row(conn.execute("SELECT * FROM entities WHERE id=?", (eid,)).fetchone())


@mcp.tool()
def entity_get(entity_id: str) -> dict:
    """Get an entity with its links and open comment count."""
    with _db() as conn:
        ent = _row(_get_target(conn, "entity", entity_id))
        ent["links"] = _rows(conn.execute(
            "SELECT * FROM links WHERE from_id=? OR to_id=?", (entity_id, entity_id)))
        ent["open_comments"] = conn.execute(
            "SELECT COUNT(*) n FROM comments WHERE target_type='entity' AND target_id=? AND status='open'",
            (entity_id,),
        ).fetchone()["n"]
        return ent


@mcp.tool()
def entity_list(project_id: str, kind: str | None = None) -> list[dict]:
    """List entities in a project, optionally filtered by kind. Content omitted; use entity_get."""
    with _db() as conn:
        q = ("SELECT id, kind, name, summary, rev, sort_order, created_by, updated_at "
             "FROM entities WHERE project_id=? AND deleted=0")
        args: list = [project_id]
        if kind is not None:
            if kind not in ENTITY_KINDS:
                raise ValueError(f"kind must be one of {sorted(ENTITY_KINDS)}")
            q += " AND kind=?"
            args.append(kind)
        return _rows(conn.execute(q + " ORDER BY kind, sort_order, name", args))


@mcp.tool()
def entity_update(entity_id: str, name: str | None = None, summary: str | None = None,
                  content_md: str | None = None, sort_order: int | None = None,
                  revision_note: str = "") -> dict:
    """Update an entity (partial patch). A content_md change records a new revision.
    Author role required."""
    _require_author()
    who = _caller()["name"]
    with _db() as conn:
        _get_target(conn, "entity", entity_id)
        for field, val in (("name", name), ("summary", summary), ("sort_order", sort_order)):
            if val is not None:
                conn.execute(f"UPDATE entities SET {field}=?, updated_at=? WHERE id=?",
                             (val, _now(), entity_id))
        if content_md is not None:
            _write_revision(conn, "entity", entity_id, content_md, revision_note, who)
        return _row(conn.execute("SELECT * FROM entities WHERE id=?", (entity_id,)).fetchone())


@mcp.tool()
def entity_delete(entity_id: str) -> dict:
    """Soft-delete an entity (revisions and comments are retained). Author role required."""
    _require_author()
    with _db() as conn:
        _get_target(conn, "entity", entity_id)
        conn.execute("UPDATE entities SET deleted=1, updated_at=? WHERE id=?", (_now(), entity_id))
        return {"deleted": entity_id}


# ---------------------------------------------------------------- links

@mcp.tool()
def link_create(project_id: str, from_id: str, to_id: str, rel_type: str, note: str = "") -> dict:
    """Link two records with a typed relationship (e.g. character 'member_of' faction,
    arc 'centers_on' character). Author role required."""
    _require_author()
    with _db() as conn:
        lid = _id()
        conn.execute(
            "INSERT INTO links (id, project_id, from_id, to_id, rel_type, note, created_by, created_at) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (lid, project_id, from_id, to_id, rel_type, note, _caller()["name"], _now()),
        )
        return _row(conn.execute("SELECT * FROM links WHERE id=?", (lid,)).fetchone())


@mcp.tool()
def link_list(project_id: str, record_id: str | None = None) -> list[dict]:
    """List links in a project, optionally only those touching record_id."""
    with _db() as conn:
        if record_id is None:
            return _rows(conn.execute("SELECT * FROM links WHERE project_id=?", (project_id,)))
        return _rows(conn.execute(
            "SELECT * FROM links WHERE project_id=? AND (from_id=? OR to_id=?)",
            (project_id, record_id, record_id)))


@mcp.tool()
def link_delete(link_id: str) -> dict:
    """Delete a link. Author role required."""
    _require_author()
    with _db() as conn:
        if conn.execute("SELECT 1 FROM links WHERE id=?", (link_id,)).fetchone() is None:
            raise ValueError(f"link {link_id} not found")
        conn.execute("DELETE FROM links WHERE id=?", (link_id,))
        return {"deleted": link_id}


# ---------------------------------------------------------------- chapters

@mcp.tool()
def chapter_create(project_id: str, title: str, content_md: str = "", sort_order: int = 0) -> dict:
    """Create a prose chapter. Author role required."""
    _require_author()
    who = _caller()["name"]
    with _db() as conn:
        if conn.execute("SELECT 1 FROM projects WHERE id=?", (project_id,)).fetchone() is None:
            raise ValueError(f"project {project_id} not found")
        cid = _id()
        conn.execute(
            "INSERT INTO chapters (id, project_id, title, content_md, sort_order, "
            "created_by, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
            (cid, project_id, title, content_md, sort_order, who, _now(), _now()),
        )
        _record_initial_revision(conn, "chapter", cid, content_md, who)
        return _row(conn.execute("SELECT * FROM chapters WHERE id=?", (cid,)).fetchone())


@mcp.tool()
def chapter_get(chapter_id: str) -> dict:
    """Get a chapter including current content, open comments count, and pending proposals count."""
    with _db() as conn:
        ch = _row(_get_target(conn, "chapter", chapter_id))
        ch["open_comments"] = conn.execute(
            "SELECT COUNT(*) n FROM comments WHERE target_type='chapter' AND target_id=? AND status='open'",
            (chapter_id,)).fetchone()["n"]
        ch["pending_proposals"] = conn.execute(
            "SELECT COUNT(*) n FROM proposals WHERE target_type='chapter' AND target_id=? AND status='pending'",
            (chapter_id,)).fetchone()["n"]
        return ch


@mcp.tool()
def chapter_list(project_id: str) -> list[dict]:
    """List chapters in order (content omitted; use chapter_get)."""
    with _db() as conn:
        return _rows(conn.execute(
            "SELECT id, title, status, rev, sort_order, created_by, updated_at, length(content_md) AS content_chars "
            "FROM chapters WHERE project_id=? AND deleted=0 ORDER BY sort_order, created_at",
            (project_id,)))


@mcp.tool()
def chapter_update(chapter_id: str, title: str | None = None, content_md: str | None = None,
                   status: str | None = None, sort_order: int | None = None,
                   revision_note: str = "") -> dict:
    """Update a chapter (partial patch). content_md change records a new revision.
    Author role required."""
    _require_author()
    who = _caller()["name"]
    with _db() as conn:
        _get_target(conn, "chapter", chapter_id)
        if status is not None and status not in CHAPTER_STATUSES:
            raise ValueError(f"status must be one of {sorted(CHAPTER_STATUSES)}")
        for field, val in (("title", title), ("status", status), ("sort_order", sort_order)):
            if val is not None:
                conn.execute(f"UPDATE chapters SET {field}=?, updated_at=? WHERE id=?",
                             (val, _now(), chapter_id))
        if content_md is not None:
            _write_revision(conn, "chapter", chapter_id, content_md, revision_note, who)
        return _row(conn.execute("SELECT * FROM chapters WHERE id=?", (chapter_id,)).fetchone())


@mcp.tool()
def chapter_delete(chapter_id: str) -> dict:
    """Soft-delete a chapter (revisions and comments are retained). Author role required."""
    _require_author()
    with _db() as conn:
        _get_target(conn, "chapter", chapter_id)
        conn.execute("UPDATE chapters SET deleted=1, updated_at=? WHERE id=?", (_now(), chapter_id))
        return {"deleted": chapter_id}


# ---------------------------------------------------------------- revisions

@mcp.tool()
def revision_list(target_type: str, target_id: str) -> list[dict]:
    """List all revisions of an entity or chapter, newest first (content omitted)."""
    with _db() as conn:
        _get_target(conn, target_type, target_id)
        return _rows(conn.execute(
            "SELECT id, rev, note, created_by, created_at, length(content_md) AS content_chars "
            "FROM revisions WHERE target_type=? AND target_id=? ORDER BY rev DESC",
            (target_type, target_id)))


@mcp.tool()
def revision_get(revision_id: str) -> dict:
    """Get a specific revision including its full content."""
    with _db() as conn:
        rev = _row(conn.execute("SELECT * FROM revisions WHERE id=?", (revision_id,)).fetchone())
        if rev is None:
            raise ValueError(f"revision {revision_id} not found")
        return rev


@mcp.tool()
def revision_restore(revision_id: str) -> dict:
    """Restore an old revision by copying it forward as a NEW revision (history is never
    rewritten). Author role required."""
    _require_author()
    who = _caller()["name"]
    with _db() as conn:
        old = conn.execute("SELECT * FROM revisions WHERE id=?", (revision_id,)).fetchone()
        if old is None:
            raise ValueError(f"revision {revision_id} not found")
        _get_target(conn, old["target_type"], old["target_id"])
        new_rev = _write_revision(conn, old["target_type"], old["target_id"], old["content_md"],
                                  f"restored from rev {old['rev']}", who)
        return {"target_type": old["target_type"], "target_id": old["target_id"],
                "restored_from_rev": old["rev"], "new_rev": new_rev}


# ---------------------------------------------------------------- comments

@mcp.tool()
def comment_create(target_type: str, target_id: str, body: str,
                   anchor_quote: str = "", parent_id: str | None = None) -> dict:
    """Comment on an entity or chapter. anchor_quote pins the comment to a quoted span of
    the current content; parent_id makes it a threaded reply. Any role."""
    with _db() as conn:
        target = _get_target(conn, target_type, target_id)
        if anchor_quote and anchor_quote not in (target["content_md"] or ""):
            raise ValueError("anchor_quote not found in current content — quote it exactly")
        if parent_id is not None and conn.execute(
                "SELECT 1 FROM comments WHERE id=?", (parent_id,)).fetchone() is None:
            raise ValueError(f"parent comment {parent_id} not found")
        cid = _id()
        conn.execute(
            "INSERT INTO comments (id, target_type, target_id, parent_id, anchor_quote, body, "
            "created_by, created_at) VALUES (?,?,?,?,?,?,?,?)",
            (cid, target_type, target_id, parent_id, anchor_quote, body, _caller()["name"], _now()),
        )
        return _row(conn.execute("SELECT * FROM comments WHERE id=?", (cid,)).fetchone())


@mcp.tool()
def comment_list(target_type: str, target_id: str, status: str | None = None) -> list[dict]:
    """List comments on an entity or chapter, oldest first. status: open | resolved | None for all."""
    with _db() as conn:
        _get_target(conn, target_type, target_id)
        q = "SELECT * FROM comments WHERE target_type=? AND target_id=?"
        args: list = [target_type, target_id]
        if status is not None:
            q += " AND status=?"
            args.append(status)
        return _rows(conn.execute(q + " ORDER BY created_at", args))


@mcp.tool()
def comment_resolve(comment_id: str) -> dict:
    """Mark a comment resolved. Any role."""
    with _db() as conn:
        if conn.execute("SELECT 1 FROM comments WHERE id=?", (comment_id,)).fetchone() is None:
            raise ValueError(f"comment {comment_id} not found")
        conn.execute("UPDATE comments SET status='resolved', resolved_by=?, resolved_at=? WHERE id=?",
                     (_caller()["name"], _now(), comment_id))
        return _row(conn.execute("SELECT * FROM comments WHERE id=?", (comment_id,)).fetchone())


# ---------------------------------------------------------------- proposals

@mcp.tool()
def proposal_create(target_type: str, target_id: str, proposed_content_md: str,
                    rationale: str = "") -> dict:
    """Propose replacement content for an entity or chapter (track-changes style).
    Recorded against the target's current revision; an author accepts or rejects it.
    Any role — this is THE write path for editor keys."""
    with _db() as conn:
        target = _get_target(conn, target_type, target_id)
        pid = _id()
        conn.execute(
            "INSERT INTO proposals (id, target_type, target_id, base_rev, proposed_content_md, "
            "rationale, created_by, created_at) VALUES (?,?,?,?,?,?,?,?)",
            (pid, target_type, target_id, target["rev"], proposed_content_md, rationale,
             _caller()["name"], _now()),
        )
        return _row(conn.execute("SELECT * FROM proposals WHERE id=?", (pid,)).fetchone())


@mcp.tool()
def proposal_list(status: str = "pending", target_type: str | None = None,
                  target_id: str | None = None) -> list[dict]:
    """List proposals (default: pending), optionally scoped to one target. Content omitted;
    each row includes 'stale' = base_rev is behind the target's current rev."""
    with _db() as conn:
        q = ("SELECT id, target_type, target_id, base_rev, rationale, status, created_by, "
             "created_at, decided_by, decided_at, length(proposed_content_md) AS content_chars "
             "FROM proposals WHERE 1=1")
        args: list = []
        if status != "all":
            q += " AND status=?"
            args.append(status)
        if target_type is not None and target_id is not None:
            q += " AND target_type=? AND target_id=?"
            args += [target_type, target_id]
        out = _rows(conn.execute(q + " ORDER BY created_at DESC", args))
        for p in out:
            table = "entities" if p["target_type"] == "entity" else "chapters"
            cur = conn.execute(f"SELECT rev FROM {table} WHERE id=?", (p["target_id"],)).fetchone()
            p["stale"] = bool(cur) and cur["rev"] > p["base_rev"]
        return out


@mcp.tool()
def proposal_get(proposal_id: str) -> dict:
    """Get a proposal with full proposed content plus the target's CURRENT content for diffing."""
    with _db() as conn:
        p = _row(conn.execute("SELECT * FROM proposals WHERE id=?", (proposal_id,)).fetchone())
        if p is None:
            raise ValueError(f"proposal {proposal_id} not found")
        target = _get_target(conn, p["target_type"], p["target_id"])
        p["current_rev"] = target["rev"]
        p["current_content_md"] = target["content_md"]
        p["stale"] = target["rev"] > p["base_rev"]
        return p


@mcp.tool()
def proposal_accept(proposal_id: str, force: bool = False, note: str = "") -> dict:
    """Accept a pending proposal: its content becomes a new revision on the target,
    attributed to the proposer. Refuses stale proposals (target moved since base_rev)
    unless force=true. Author role required."""
    _require_author()
    who = _caller()["name"]
    with _db() as conn:
        p = conn.execute("SELECT * FROM proposals WHERE id=?", (proposal_id,)).fetchone()
        if p is None:
            raise ValueError(f"proposal {proposal_id} not found")
        if p["status"] != "pending":
            raise ValueError(f"proposal is already {p['status']}")
        target = _get_target(conn, p["target_type"], p["target_id"])
        if target["rev"] > p["base_rev"] and not force:
            raise ValueError(
                f"stale: proposal was written against rev {p['base_rev']} but target is at "
                f"rev {target['rev']}. Review with proposal_get, then pass force=true to apply anyway."
            )
        new_rev = _write_revision(
            conn, p["target_type"], p["target_id"], p["proposed_content_md"],
            f"proposal {proposal_id} by {p['created_by']}, accepted by {who}"
            + (f": {note}" if note else ""),
            p["created_by"],
        )
        conn.execute(
            "UPDATE proposals SET status='accepted', decided_by=?, decided_at=?, decision_note=? WHERE id=?",
            (who, _now(), note, proposal_id),
        )
        return {"proposal_id": proposal_id, "applied_as_rev": new_rev,
                "target_type": p["target_type"], "target_id": p["target_id"]}


@mcp.tool()
def proposal_reject(proposal_id: str, note: str = "") -> dict:
    """Reject a pending proposal with an optional note for the proposer. Author role required."""
    _require_author()
    with _db() as conn:
        p = conn.execute("SELECT * FROM proposals WHERE id=?", (proposal_id,)).fetchone()
        if p is None:
            raise ValueError(f"proposal {proposal_id} not found")
        if p["status"] != "pending":
            raise ValueError(f"proposal is already {p['status']}")
        conn.execute(
            "UPDATE proposals SET status='rejected', decided_by=?, decided_at=?, decision_note=? WHERE id=?",
            (_caller()["name"], _now(), note, proposal_id),
        )
        return _row(conn.execute("SELECT * FROM proposals WHERE id=?", (proposal_id,)).fetchone())


# ---------------------------------------------------------------- search

@mcp.tool()
def search(query: str, project_id: str | None = None, limit: int = 20) -> list[dict]:
    """Case-insensitive substring search across entity names/summaries/content and
    chapter titles/content. Returns matches with a short snippet."""
    like = f"%{query}%"
    out: list[dict] = []
    with _db() as conn:
        eq = ("SELECT id, project_id, kind, name, summary, content_md FROM entities "
              "WHERE deleted=0 AND (name LIKE ? OR summary LIKE ? OR content_md LIKE ?)")
        cq = ("SELECT id, project_id, title, content_md FROM chapters "
              "WHERE deleted=0 AND (title LIKE ? OR content_md LIKE ?)")
        eargs: list = [like, like, like]
        cargs: list = [like, like]
        if project_id is not None:
            eq += " AND project_id=?"
            cq += " AND project_id=?"
            eargs.append(project_id)
            cargs.append(project_id)
        for r in conn.execute(eq + " LIMIT ?", eargs + [limit]):
            text = r["content_md"] or r["summary"] or ""
            i = text.lower().find(query.lower())
            snippet = text[max(0, i - 60):i + 120] if i >= 0 else text[:120]
            out.append({"type": "entity", "id": r["id"], "project_id": r["project_id"],
                        "kind": r["kind"], "name": r["name"], "snippet": snippet})
        for r in conn.execute(cq + " LIMIT ?", cargs + [limit]):
            text = r["content_md"] or ""
            i = text.lower().find(query.lower())
            snippet = text[max(0, i - 60):i + 120] if i >= 0 else text[:120]
            out.append({"type": "chapter", "id": r["id"], "project_id": r["project_id"],
                        "name": r["title"], "snippet": snippet})
    return out[:limit]


# ---------------------------------------------------------------- backups

def _do_backup(reason: str = "scheduled") -> dict:
    """Write a consistent point-in-time snapshot via VACUUM INTO and rotate old ones."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    dest = BACKUP_DIR / f"story-{stamp}.db"
    if dest.exists():  # same-second rerun: VACUUM INTO refuses to overwrite
        dest.unlink()
    conn = _db()
    try:
        conn.execute("VACUUM INTO ?", (str(dest),))
    finally:
        conn.close()
    rotated = []
    if BACKUP_KEEP > 0:
        for old in sorted(BACKUP_DIR.glob("story-*.db"))[:-BACKUP_KEEP]:
            old.unlink()
            rotated.append(old.name)
    return {"file": dest.name, "bytes": dest.stat().st_size, "reason": reason,
            "rotated_out": rotated, "created_at": _now()}


def _latest_backup() -> Path | None:
    if not BACKUP_DIR.is_dir():
        return None
    snaps = sorted(BACKUP_DIR.glob("story-*.db"))
    return snaps[-1] if snaps else None


def _backup_loop():
    while True:
        time.sleep(BACKUP_HOURS * 3600)
        try:
            info = _do_backup()
            print(f"[story-bible] backup {info['file']} ({info['bytes']}B)")
        except Exception as e:  # the loop must survive a bad night
            print(f"[story-bible] backup FAILED: {e}", file=sys.stderr)


@mcp.tool()
def backup_now() -> dict:
    """Snapshot the database to the on-volume backups directory immediately.
    Author role required."""
    _require_author()
    return _do_backup("manual")


@mcp.tool()
def backup_list() -> list[dict]:
    """List on-volume database snapshots, oldest first. Any role."""
    if not BACKUP_DIR.is_dir():
        return []
    return [{"file": p.name, "bytes": p.stat().st_size,
             "modified": datetime.fromtimestamp(p.stat().st_mtime, timezone.utc).isoformat()}
            for p in sorted(BACKUP_DIR.glob("story-*.db"))]


# ---------------------------------------------------------------- ASGI app + auth

def build_app():
    """Wrap the MCP streamable-HTTP app with API-key auth. /healthz is unauthenticated."""
    inner = mcp.streamable_http_app()
    keys = _load_keys()
    if not keys:
        print("[story-bible] FATAL: STORYBIBLE_KEYS is empty — refusing to serve unauthenticated",
              file=sys.stderr)
        sys.exit(1)

    async def app(scope, receive, send):
        if scope["type"] != "http":
            return await inner(scope, receive, send)
        if scope["path"] == "/healthz":
            await send({"type": "http.response.start", "status": 200,
                        "headers": [(b"content-type", b"application/json")]})
            await send({"type": "http.response.body", "body": b'{"ok": true}'})
            return
        headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}
        key = headers.get("x-api-key", "")
        if not key and headers.get("authorization", "").lower().startswith("bearer "):
            key = headers["authorization"][7:]
        ident = keys.get(key)
        if ident is None:
            await send({"type": "http.response.start", "status": 401,
                        "headers": [(b"content-type", b"application/json")]})
            await send({"type": "http.response.body",
                        "body": b'{"error": "missing or invalid API key"}'})
            return
        if scope["path"] == "/backup/latest" and scope.get("method", "GET") == "GET":
            # Offsite-pull route: streams the newest snapshot (author keys only).
            if ident["role"] != "author":
                await send({"type": "http.response.start", "status": 403,
                            "headers": [(b"content-type", b"application/json")]})
                await send({"type": "http.response.body",
                            "body": b'{"error": "author key required for backup download"}'})
                return
            if b"fresh=1" in scope.get("query_string", b"") or _latest_backup() is None:
                _do_backup("pull")
            snap = _latest_backup()
            await send({"type": "http.response.start", "status": 200,
                        "headers": [(b"content-type", b"application/octet-stream"),
                                    (b"content-disposition",
                                     f'attachment; filename="{snap.name}"'.encode()),
                                    (b"content-length", str(snap.stat().st_size).encode())]})
            with snap.open("rb") as f:
                while chunk := f.read(1 << 20):
                    await send({"type": "http.response.body", "body": chunk, "more_body": True})
            await send({"type": "http.response.body", "body": b""})
            return
        token = CALLER.set(ident)
        try:
            await inner(scope, receive, send)
        finally:
            CALLER.reset(token)

    return app


if __name__ == "__main__":
    import uvicorn

    _init_db()
    if BACKUP_HOURS > 0:
        try:
            info = _do_backup("boot")
            print(f"[story-bible] boot backup {info['file']} ({info['bytes']}B)")
        except Exception as e:
            print(f"[story-bible] boot backup failed: {e}", file=sys.stderr)
        threading.Thread(target=_backup_loop, daemon=True, name="backup-loop").start()
    print(f"[story-bible] db={DB_PATH} port={PORT} keys={len(_load_keys())}")
    uvicorn.run(build_app(), host="0.0.0.0", port=PORT)
