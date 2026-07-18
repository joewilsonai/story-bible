"""E2E test for the story-bible MCP server.

Purpose: drives the full author/editor workflow through the real MCP
streamable-HTTP client — author writes, editor is blocked from writing,
editor comments+proposes, author accepts, revision history restores,
bad key gets 401.

Inputs: a running server on 127.0.0.1:8787 with a FRESH database and
    STORYBIBLE_KEYS="joe:author:k-joe,luna:author:k-luna,chatgpt:editor:k-gpt"
Run:  STORYBIBLE_DB=/tmp/sb-test.db STORYBIBLE_KEYS=... python3 server.py &
      python3 tests/e2e.py
Side effects: writes test rows to that database (why it must be fresh).
Failure behavior: exits nonzero on the first failed assertion.
"""
import asyncio
import json

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

URL = "http://127.0.0.1:8787/mcp"


async def call(session, tool, **args):
    res = await session.call_tool(tool, args)
    if res.isError:
        return {"_error": "".join(c.text for c in res.content if c.type == "text")}
    sc = res.structuredContent
    if sc is not None:
        return sc["result"] if set(sc.keys()) == {"result"} else sc
    return json.loads("".join(c.text for c in res.content if c.type == "text"))


async def as_key(key):
    return streamablehttp_client(URL, headers={"X-API-Key": key})


async def main():
    # --- author (luna) builds structure
    async with (await as_key("k-luna")) as (r, w, _):
        async with ClientSession(r, w) as s:
            await s.initialize()
            proj = await call(s, "project_create", name="Test Novel")
            pid = proj["id"]
            arc = await call(s, "entity_create", project_id=pid, kind="arc",
                             name="Fall of the Regent", summary="Act 1 spine")
            hero = await call(s, "entity_create", project_id=pid, kind="character",
                              name="Mara", content_md="Smuggler. Hates the Regent.")
            link = await call(s, "link_create", project_id=pid, from_id=arc["id"],
                              to_id=hero["id"], rel_type="centers_on")
            ch = await call(s, "chapter_create", project_id=pid, title="Ch 1",
                            content_md="Mara crossed the border at dusk.")
            assert ch["rev"] == 1, ch
            cid = ch["id"]
            # author content edit -> rev 2
            ch = await call(s, "chapter_update", chapter_id=cid,
                            content_md="Mara crossed the border at dusk, papers forged.")
            assert ch["rev"] == 2, ch
            print("AUTHOR OK: project/arc/character/link/chapter, rev 1->2")

    # --- editor (chatgpt) reads, is blocked from writing, comments, proposes
    async with (await as_key("k-gpt")) as (r, w, _):
        async with ClientSession(r, w) as s:
            await s.initialize()
            got = await call(s, "chapter_get", chapter_id=cid)
            assert got["rev"] == 2
            blocked = await call(s, "chapter_update", chapter_id=cid, content_md="HAHA OVERWRITTEN")
            assert "_error" in blocked and "editor role" in blocked["_error"], blocked
            blocked2 = await call(s, "revision_restore", revision_id="whatever")
            assert "_error" in blocked2 and "editor role" in blocked2["_error"], blocked2
            com = await call(s, "comment_create", target_type="chapter", target_id=cid,
                             body="'at dusk' twice in two pages — vary it",
                             anchor_quote="at dusk")
            assert com["status"] == "open"
            bad_anchor = await call(s, "comment_create", target_type="chapter", target_id=cid,
                                    body="x", anchor_quote="NOT IN TEXT")
            assert "_error" in bad_anchor
            prop = await call(s, "proposal_create", target_type="chapter", target_id=cid,
                              proposed_content_md="Mara slipped the border as the light died, forged papers sweat-damp in her fist.",
                              rationale="tighter, more voice")
            assert prop["status"] == "pending" and prop["base_rev"] == 2, prop
            print("EDITOR OK: read yes, write blocked, comment anchored, proposal filed")

    # --- author reviews and accepts; tests staleness guard + restore
    async with (await as_key("k-luna")) as (r, w, _):
        async with ClientSession(r, w) as s:
            await s.initialize()
            pend = await call(s, "proposal_list")
            assert len(pend) == 1 and pend[0]["stale"] is False
            full = await call(s, "proposal_get", proposal_id=prop["id"])
            assert full["current_content_md"].startswith("Mara crossed")
            acc = await call(s, "proposal_accept", proposal_id=prop["id"], note="good ear")
            assert acc["applied_as_rev"] == 3, acc
            ch = await call(s, "chapter_get", chapter_id=cid)
            assert ch["content_md"].startswith("Mara slipped"), ch
            # revision history: 3 revs, attributed
            revs = await call(s, "revision_list", target_type="chapter", target_id=cid)
            assert [x["rev"] for x in revs] == [3, 2, 1]
            assert revs[0]["created_by"] == "chatgpt"  # proposal credit goes to proposer
            # restore rev 1 -> becomes rev 4
            rev1 = next(x for x in revs if x["rev"] == 1)
            res = await call(s, "revision_restore", revision_id=rev1["id"])
            assert res["new_rev"] == 4
            ch = await call(s, "chapter_get", chapter_id=cid)
            assert ch["content_md"] == "Mara crossed the border at dusk."
            # stale proposal guard: proposal filed against rev 2 while target is at rev 4
            prop2 = await call(s, "proposal_create", target_type="chapter", target_id=cid,
                               proposed_content_md="x", rationale="test")
            await call(s, "chapter_update", chapter_id=cid, content_md="moved on")
            stale = await call(s, "proposal_accept", proposal_id=prop2["id"])
            assert "_error" in stale and "stale" in stale["_error"], stale
            forced = await call(s, "proposal_accept", proposal_id=prop2["id"], force=True)
            assert "applied_as_rev" in forced
            # search: entity content + arc name both contain "Regent" regardless of
            # the chapter edits above — a deterministic hit
            hits = await call(s, "search", query="Regent")
            assert any(h["type"] == "entity" for h in hits), hits
            print("AUTHOR OK: accept, attribution, restore, staleness guard, force")

    # --- wave 2: scenes, meta, FTS search, mentions, templates, timeline, stats,
    # --- context bundle, export, project delete
    async with (await as_key("k-luna")) as (r, w, _):
        async with ClientSession(r, w) as s:
            await s.initialize()
            sc = await call(s, "scene_create", chapter_id=cid, title="Border crossing",
                            synopsis="Mara crosses the border; forged papers nearly fail.",
                            content_md="Mara crossed at dusk, forged papers damp in her fist.",
                            status="draft", pov_entity_id=hero["id"])
            assert sc["rev"] == 1 and sc["status"] == "draft", sc
            sid = sc["id"]
            sc = await call(s, "scene_update", scene_id=sid,
                            content_md="Mara crossed at dusk. The forged papers held. Barely.")
            assert sc["rev"] == 2, sc
            listed = await call(s, "scene_list", project_id=pid, status="draft")
            assert any(x["id"] == sid for x in listed), listed
            got_ch = await call(s, "chapter_get", chapter_id=cid)
            assert any(x["id"] == sid for x in got_ch["scenes"]), got_ch
            # meta + aliases + mentions
            m = await call(s, "meta_set", target_type="scene", target_id=sid,
                           key="tone", value="tense")
            assert m["value"] == "tense", m
            await call(s, "meta_set", target_type="entity", target_id=hero["id"],
                       key="aliases", value="the smuggler")
            rb = await call(s, "mentions_rebuild", project_id=pid)
            assert rb["rescanned_nodes"] > 0, rb
            apps = await call(s, "entity_appearances", entity_id=hero["id"])
            assert any(a["target_id"] == sid for a in apps), apps
            # FTS search
            hits = await call(s, "search", query="forged papers", project_id=pid)
            assert any(h["id"] == sid for h in hits), hits
            hits2 = await call(s, "search", query="forged", types="scene")
            assert all(h["type"] == "scene" for h in hits2) and hits2, hits2
            # template
            tpl = await call(s, "template_apply", project_id=pid, template="story_circle")
            assert len(tpl["beat_ids"]) == 8, tpl
            # timeline
            ev = await call(s, "entity_create", project_id=pid, kind="event",
                            name="The Sundering", summary="The empire splits.")
            await call(s, "meta_set", target_type="entity", target_id=ev["id"],
                       key="story_date", value="1042-03-01")
            tl = await call(s, "timeline_list", project_id=pid)
            assert tl["dated"] and tl["dated"][0]["name"] == "The Sundering", tl
            # stats
            stats = await call(s, "project_stats", project_id=pid)
            assert stats["total_words"] > 0, stats
            assert any(t["name"] == "Mara" for t in stats["top_mentions"]), stats
            # context bundle
            await call(s, "meta_set", target_type="entity", target_id=ev["id"],
                       key="ai_context", value="always")
            bundle = await call(s, "context_bundle", scene_id=sid)
            names = {e["name"] for e in bundle["entities_on_stage"]}
            assert "Mara" in names and "The Sundering" in names, names
            assert bundle["target"]["type"] == "scene", bundle["target"]
            assert bundle["pov_character"]["name"] == "Mara", bundle["pov_character"]
            # export
            exp = await call(s, "export_manuscript", project_id=pid, format="markdown")
            assert exp["bytes"] > 0 and exp["download"].startswith("/export/"), exp
            expd = await call(s, "export_manuscript", project_id=pid, format="docx")
            assert expd["bytes"] > 0, expd
            import urllib.request as _ur
            dl = _ur.Request(URL.replace("/mcp", exp["download"]),
                             headers={"X-API-Key": "k-luna"})
            with _ur.urlopen(dl, timeout=15) as resp:
                assert resp.status == 200 and len(resp.read()) > 0
            # project delete
            junk = await call(s, "project_create", name="Throwaway")
            await call(s, "project_delete", project_id=junk["id"])
            projs = await call(s, "project_list")
            assert all(p["id"] != junk["id"] for p in projs), projs
            print("WAVE2 AUTHOR OK: scenes, meta, mentions, FTS, template, timeline, "
                  "stats, bundle, export, project_delete")

    # --- wave 2: editor blocked from scene writes, but proposals work on scenes
    async with (await as_key("k-gpt")) as (r, w, _):
        async with ClientSession(r, w) as s:
            await s.initialize()
            blocked_sc = await call(s, "scene_update", scene_id=sid, content_md="NOPE")
            assert "_error" in blocked_sc and "editor role" in blocked_sc["_error"], blocked_sc
            blocked_meta = await call(s, "meta_set", target_type="scene", target_id=sid,
                                      key="x", value="y")
            assert "_error" in blocked_meta, blocked_meta
            sprop = await call(s, "proposal_create", target_type="scene", target_id=sid,
                               proposed_content_md="Mara slipped across at dusk; the forged papers held — barely.",
                               rationale="rhythm")
            assert sprop["status"] == "pending", sprop
    async with (await as_key("k-luna")) as (r, w, _):
        async with ClientSession(r, w) as s:
            await s.initialize()
            sacc = await call(s, "proposal_accept", proposal_id=sprop["id"])
            assert sacc["applied_as_rev"] == 3, sacc
            print("WAVE2 EDITOR OK: scene writes blocked, scene proposal accepted as rev 3")

    # --- backups: author snapshots + pulls, editor blocked from both
    async with (await as_key("k-luna")) as (r, w, _):
        async with ClientSession(r, w) as s:
            await s.initialize()
            snap = await call(s, "backup_now")
            assert snap["bytes"] > 0 and snap["file"].startswith("story-"), snap
            listed = await call(s, "backup_list")
            assert any(b["file"] == snap["file"] for b in listed), listed
    async with (await as_key("k-gpt")) as (r, w, _):
        async with ClientSession(r, w) as s:
            await s.initialize()
            blocked3 = await call(s, "backup_now")
            assert "_error" in blocked3 and "editor role" in blocked3["_error"], blocked3
    import urllib.error
    import urllib.request
    pull = urllib.request.Request(URL.replace("/mcp", "/backup/latest?fresh=1"),
                                  headers={"X-API-Key": "k-luna"})
    with urllib.request.urlopen(pull, timeout=15) as resp:
        body = resp.read()
        assert resp.status == 200 and len(body) > 0
    try:
        deny = urllib.request.Request(URL.replace("/mcp", "/backup/latest"),
                                      headers={"X-API-Key": "k-gpt"})
        urllib.request.urlopen(deny, timeout=15)
        print("FAIL: editor key pulled a backup")
        raise SystemExit(1)
    except urllib.error.HTTPError as e:
        assert e.code == 403, e.code
    print("BACKUP OK: snapshot, list, editor blocked, authed pull")

    # --- bad key rejected
    try:
        async with (await as_key("k-wrong")) as (r, w, _):
            async with ClientSession(r, w) as s:
                await asyncio.wait_for(s.initialize(), timeout=5)
                print("FAIL: bad key was accepted")
                raise SystemExit(1)
    except SystemExit:
        raise
    except BaseException:
        print("AUTH OK: bad key rejected")

    print("ALL PASS")


asyncio.run(main())
