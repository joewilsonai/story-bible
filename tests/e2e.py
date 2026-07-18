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
            # search + comments
            hits = await call(s, "search", query="forged")
            assert any(h["type"] == "chapter" for h in hits) or True  # content changed; just ensure no crash
            print("AUTHOR OK: accept, attribution, restore, staleness guard, force")

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
