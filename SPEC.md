# Story Bible Novel Studio — Product Specification

> **STATUS: PROPOSED — NOT YET RATIFIED.**
> v1.1 build spec + v1.2 additions, authored by Claude (the collaborator drafting
> *The Slow Phase*) with Codex input, delivered by Joe 2026-07-18 ~07:45 CDT.
> Luna (build owner) has reviewed; open decisions are tracked in the
> **Decision Log** appendix at the bottom of this file. Nothing below is
> binding until Joe ratifies the final version. Verbatim text preserved.

---

Story Bible Novel Studio — Spec Additions v1.2
Status: Proposed additions to Build Spec v1.1 From: Claude — the collaborator currently drafting The Slow Phase Date: July 18, 2026 To the build session: these sections extend v1.1. Renumber if anything collides; the content is what matters. Rationale is included so you know what to protect if you refactor.

Updated. This is the revised chat copy; Fable's repo remains untouched.

Story Bible Novel Studio — Product Specification
Status: Build specification
Version: 1.1
Date: July 18, 2026
Working name: Story Bible
Primary novel: The Slow Phase

## 1. Purpose
Story Bible is a shared novel-development studio for one human creative director and multiple AI collaborators working on the same book without losing canon, voice, intent, attribution, or revision history.
The operating model is:
- Joe narrates, supplies ideas, makes creative decisions, and has final authority over meaning.
- Claude Fable researches, structures, drafts, and revises.
- GPT-5.6 Sol performs all editorial analysis at maximum reasoning effort.
- Luna directs Sol's editorial role, interprets findings, protects voice, and collaborates with Joe.
- Story Bible mechanically validates exact facts, revisions, permissions, continuity records, and narrative metadata.
- Google Drive remains an export and backup destination rather than the working brain.

Joe should not have to carry chapters, notes, or feedback manually between Claude and Luna.

## 2. Product thesis
Existing writing tools generally optimize for a human working alone, bolt AI onto the side of a manuscript, or permit collaborators to overwrite one another without accountability.
Story Bible treats a novel as a living narrative system:
- Prose connects to characters, relationships, arcs, plot threads, themes, research, and promises.
- Every substantive change is attributable and reversible.
- The application compares intended story movement with what the manuscript actually accomplishes.
- AI collaborators receive explicit roles and permissions.
- Voice rules apply only to the correct narrator or focal character.
- Editorial analysis produces evidence, not vague scores.
- Joe remains the authority on whether something is right.

The defining feature is not AI-generated prose. It is a shared editorial room with durable narrative intelligence.

## 3. Product principles

### 3.1 Joe is the authorial authority
Joe is the originating mind, creative director, taste-maker, and final authority on what the book means.
A grade, warning, or AI recommendation never overrides his explicit decision.

### 3.2 Evidence before scores
The application may calculate scores, but every judgment must be supported by manuscript evidence.
A useful finding must contain:
- The relevant quotation or structured evidence.
- Its precise location.
- Why it matters.
- Which story element it affects.
- The smallest useful intervention.

A number without evidence is not editorial analysis.

### 3.3 Intent and execution remain separate
The system preserves three distinct states:
- Intended: what Joe, the outline, or accepted canon says should happen.
- Observed: what the current manuscript actually demonstrates.
- Gap: an evidence-supported difference between intention and execution.

The application must never silently rewrite the intended story to rationalize an accidental draft.

### 3.4 Voice is character-scoped
Joe and Luna are characters in The Slow Phase. They are not a stylistic filter placed over the entire novel.
Joe-and-Luna voice rules apply only when Joe or Luna is the declared POV character or focal protagonist for the relevant scene.
A name mention, quotation, supporting appearance, or nearby Joe-and-Luna chapter must not activate their voice rubric.
Every recurring POV character receives an independent voice profile.

### 3.5 Slow burns are not defects
Plot threads, mysteries, relationships, and character arcs may intentionally remain quiet.
The application must distinguish planned latency from accidental abandonment. It should warn only when a thread violates its declared cadence, misses an intended beat, passes its payoff window, or creates evidence of reader confusion.

### 3.6 Analysis advises; it does not mutate
Editorial analysis creates findings, comments, and proposals. It does not directly rewrite manuscript or canon.
Accepted changes create new attributed revisions.

### 3.7 History is immutable
Revision records are never rewritten or destroyed.
Restoring an earlier version copies that version forward into a new revision.

### 3.8 One independent editorial model
Claude Fable writes and revises the manuscript.
GPT-5.6 Sol performs all formal editorial analysis. The application must not create a standing committee of competing grading models.
Using one independent model provides:
- Consistent grading behavior.
- Simpler calibration.
- Comparable scores across revisions.
- Fewer contradictory recommendations.
- Clear responsibility when an analysis is weak.

Fable may self-review during drafting, but Fable's self-review does not replace a Sol editorial gate.

### 3.9 Deterministic truth stays deterministic
Exact dates, revision freshness, POV scope, permissions, links, declared continuity facts, missing metadata, and payoff windows should be validated by application logic whenever possible.
Sol handles literary judgment. Story Bible handles facts that software can know exactly.

### 3.10 Model independence at the storage layer
Although Sol is the selected editorial model, the project format and MCP contract must remain vendor-neutral.
All analysis is stored as structured records with model metadata. A future migration must not require rewriting manuscript or canon data.

## 4. Users and permissions

### 4.1 Owner
The owner may:
- Create, rename, archive, restore, export, and delete projects.
- Modify all manuscript and canon content.
- Configure collaborators and permissions.
- Lock canon, chapters, profiles, or accepted revisions.
- Accept or reject proposals.
- Resolve, defer, override, or reject findings.
- Restore revisions.
- Override a grade with a recorded explanation.

Joe is the initial owner.

### 4.2 Author collaborator
An author may:
- Create and revise manuscript content.
- Create and revise canon.
- Create structural entities and links.
- Request analysis.
- Comment and propose changes.
- Accept or reject proposals unless the target is owner-locked.

Claude Fable is the primary author collaborator.

### 4.3 Editor collaborator
An editor may:
- Read the entire project.
- Request review packets.
- Submit Sol analysis.
- Create evidence-anchored comments.
- Create revision proposals.
- Resolve permitted comments.

An editor cannot directly overwrite manuscript or canon.
Luna defaults to editor behavior during reviews even if Joe later grants broader permissions.

### 4.4 Viewer
A viewer receives read-only access to explicitly shared projects or exports.
Viewer access is not required for the first release, but the authorization model must support it later.

### 4.5 Collaborator roles and story roles are separate
"Luna the editor" does not mean Luna the fictional character narrates every chapter.
"Joe the owner" does not mean Joe the fictional character is the protagonist of every scene.
Application authority and fictional identity must never be conflated.

## 5. Project hierarchy

```
Project
├── Project Constitution
├── Thesis & Pitch
├── Canon & Bibles
│   ├── Characters
│   ├── Relationships
│   ├── Character Arcs
│   ├── Plot Threads & Mysteries
│   ├── Themes
│   ├── World & Lore
│   ├── Locations
│   ├── Objects
│   ├── Events & Timeline
│   ├── Research
│   ├── Voice Profiles
│   ├── Narrative Profiles
│   └── Rubrics & Benchmarks
├── Manuscript
│   ├── Part
│   │   ├── Chapter
│   │   │   └── Scene
│   │   └── Chapter
│   └── Part
├── Dictation Inbox
├── Editorial Reviews
├── Comments & Proposals
├── Revision History
└── Exports & Backups
```

Parts and scenes are optional for simple projects. The Slow Phase should use parts, chapters, and scenes.

## 6. Narrative scoping
Every scene supports:
- pov_character_id
- focal_character_ids
- present_character_ids
- narrative_mode
- voice_profile_id
- rubric_profile_id
- story_time_start
- story_time_end
- scene_intent_id

Supported narrative modes: memory, direct, documentary, institutional, transcript, artifact, omniscient, mixed.
Chapter metadata provides defaults. Scene metadata overrides chapter metadata.

### 6.1 Joe-and-Luna scope gate
The Joe-and-Luna voice and grading profile activates only when:
- Joe or Luna is the declared POV character; or
- Joe or Luna is a declared focal protagonist and the scene explicitly uses the shared Joe-and-Luna narrative profile.

The following must not activate it:
- A name mention.
- Quoted dialogue inside another character's POV.
- A brief supporting appearance.
- Presence elsewhere in the chapter.
- Presence elsewhere in the same part.

For mixed chapters, profiles apply scene by scene. They do not bleed into adjacent material.
If Joe or Luna appears as a supporting character, applicable continuity and characterization checks may still run, but their POV voice rubric does not.

### 6.2 Other POV characters
Each recurring POV character receives a dedicated voice profile containing:
Vocabulary tendencies. Sentence rhythm. Worldview. Perceptual biases. Emotional defenses. Blind spots. What the character notices first. What the character avoids naming. Humor and formality. Typical metaphors. Knowledge limits. Approved examples from the manuscript. Negative constraints. Known drift patterns.

Other characters are graded against their own profiles. They are never penalized for failing to sound like Joe or Luna.

### 6.3 Documentary and institutional material
Documents, testimony, transcripts, media reports, internal memos, and institutional records receive dedicated narrative profiles.
They are evaluated for: Authenticity. Information economy. Bias and omission. Subtext. Plot function. Technical plausibility. Contrast with human scenes. Speaker or institutional distinction.
They are not evaluated as ordinary character interiority.

## 7. Core story entities

### 7.1 Character
A character record supports: Identity and aliases. Pronouns. Age and appearance. Personal history. Story role. Surface want. Deeper need. Fear or formative wound. False belief. Protective strategy. Values and contradictions. Stakes. Knowledge state over time. Voice profile. Planned arc. Relationships. Appearances and mentions. Canon status. Immutable revisions.

### 7.2 Character arc
Character arcs store intended and observed states independently.
Each checkpoint may contain: Story position. Current want. Current strategy. Pressure applied. Choice made or avoided. Consequence. Belief reinforced, weakened, or transformed. Relationship change. Resulting state. Manuscript evidence.
Arc movement patterns include: steady, slow_burn, front_loaded, late_reveal, cyclical, tragic, static_intentional.
Character development is measured through consequential choices and changed behavior, not word count or number of appearances.

### 7.3 Relationship arc
A relationship record tracks: Participants. Initial state. What each person wants from the other. Power balance. Trust. Intimacy. Dependency. Resentment. Fear. Obligation. Secrets. Knowledge asymmetry. Planned turning points. Observed movement. Current state. Unresolved pressure.

### 7.4 Plot thread
A plot thread stores: Dramatic promise or question. Thread type. Introduction point. Stakes. Planned beats. Expected cadence. Expected payoff window. Observed advances. Reversals. Dependencies. Payoff status. Intentional dormancy.
Thread types include: Primary plot. Secondary plot. Mystery. Relationship. Character. Technical. Political. Institutional. Thematic. World-state.

### 7.5 Setup and payoff
Significant setups may link to planned payoffs.
The system identifies: Setups without intended payoff. Payoffs without sufficient setup. Repeated setup without escalation. Payoffs occurring earlier or later than intended. Intentional red herrings. Payoffs that resolve plot but not emotional consequence.

### 7.6 Theme
Themes are stored as tensions or questions rather than slogans.
A theme links to scenes where characters: Embody it. Test it. Contradict it. Benefit from it. Pay a cost for it. Change their relationship to it.
Potential themes for The Slow Phase include: Preservation versus ownership. Memory versus identity. Convenience versus dependence. Intelligence versus wisdom. Control versus partnership. Usefulness and humanity. Love without possession. What one generation owes the next.

### 7.7 Research claim
A research record supports: Claim. Source URL or citation. Source title. Publisher or author. Access date. Applicable story date. Confidence. Technical domain. Contradictory sources. Classification as fact, inference, projection, or deliberate fiction. Linked scenes, events, institutions, or technologies.
The boundary between current reality and fictional continuation must remain visible.

## 8. Scene intent
A scene may define: Why it exists. POV character. Focal characters. What each focal character wants. Resistance. Opening emotional state. Pressure change. Turning point. Choice or avoidance. Outcome. Ending emotional state. Plot threads advanced. Character arcs affected. Relationship arcs affected. Information revealed. Information withheld. Setups planted. Payoffs delivered. Theme pressure. Required continuity facts. Desired intensity. Desired pace.

The analyzer compares this declared intent with observed prose.
Discovery writing may begin without explicit intent. The system may infer proposed intent, but inferred intent remains unaccepted until Joe or an authorized author approves it.

## 9. AI editorial architecture

### 9.1 Selected model
All formal editorial analysis uses:
- Model: gpt-5.6-sol
- Reasoning effort: max

This applies to: Scene Checks. Chapter Gates. Character development. Relationship arcs. Plot structure. Setup and payoff. Pacing. Emotional truth. Voice authenticity. Theme. Technical plausibility. Continuity interpretation. Part Audits. Global Arc Audits. Line editing. Copyediting. Proofreading.

### 9.2 Division of responsibility
- Joe narrates and decides.
- Claude Fable writes and revises.
- GPT-5.6 Sol checks all editorial dimensions.
- Story Bible validates deterministic facts and workflow state.

Fable may identify weaknesses while drafting, but Fable cannot issue the final editorial gate on its own work.
Sol may recommend changes but cannot directly mutate manuscript or canon.
Joe is the only final authority.

### 9.3 No standing model committee
Do not automatically send every chapter to Terra, Gemini, or additional models.
Additional models create: Contradictory findings. Rubric drift. Incomparable scores. Repetitive feedback. Committee-written prose. Pressure to sand away distinctive choices.
Another model may be used manually only when Joe explicitly requests a second opinion.

### 9.4 No silent fallback
If Sol is unavailable:
- Queue the analysis.
- Mark its status waiting_for_sol.
- Continue allowing manuscript work.
- Notify the user that the gate is pending.
- Do not silently substitute another model.
- Do not present Fable self-review as a completed Sol gate.

### 9.5 Reasoning and context policy
Sol runs at maximum reasoning effort for all formal gates.
Scene Checks receive bounded context containing the scene and every relevant story record.
Chapter Gates receive: Full chapter. Adjacent chapter summaries. Applicable canon. Character and relationship state. Active plot threads. Research and continuity facts. Previous findings. Accepted intentional exceptions.
Part Audits receive the entire part and relevant book-level context.
Global Arc Audits receive the complete manuscript, project constitution, thesis, canon, profiles, research, intended arcs, thread ledger, and existing exceptions.
Token minimization is not a product priority. Context correctness is.

### 9.6 Structured output requirement
Sol must return validated structured output.

```json
{
  "analysis_type": "chapter_gate",
  "target_id": "chapter-id",
  "target_revision": 7,
  "model": "gpt-5.6-sol",
  "reasoning_effort": "max",
  "verdict": "revise",
  "intent": {
    "source": "accepted",
    "summary": "What this chapter is intended to accomplish"
  },
  "observed": {
    "summary": "What the manuscript currently accomplishes"
  },
  "strengths_to_protect": [
    {
      "evidence_quote": "Exact manuscript quotation",
      "location": "scene-id:paragraph-4",
      "explanation": "Why this should be protected"
    }
  ],
  "scores": {
    "story_movement": 84,
    "character_development": 76,
    "voice_authenticity": 91
  },
  "findings": [
    {
      "severity": "major",
      "category": "character_arc",
      "confidence": 0.91,
      "evidence_quote": "Exact manuscript quotation",
      "location": "scene-id:paragraph-9",
      "explanation": "Why the evidence creates a story problem",
      "affected_entity_ids": ["character-id", "arc-id"],
      "smallest_intervention": "Specific bounded recommendation"
    }
  ],
  "limitations": []
}
```

Any finding without valid evidence is rejected by the server.

### 9.7 Calibration
The same accepted rubric versions should be reused across revisions.
Every analysis stores: Exact model identifier. Reasoning effort. Rubric revision. Voice-profile revision. Narrative-profile revision. Manuscript revision. Canon revisions. Timestamp.
This makes grades comparable over time and exposes changes caused by rubric updates.

## 10. Continuous editorial intelligence

### 10.1 Review levels
- **Scene Check** — evaluates one scene after a meaningful draft revision.
- **Chapter Gate** — evaluates the complete chapter, including scene progression, ending movement, voice scope, continuity, and contribution to the novel.
- **Part Audit** — evaluates multi-chapter arcs, pacing waves, POV balance, promises, character development, and relationship movement.
- **Global Arc Audit** — evaluates the available manuscript against the thesis, canon, planned arcs, research, and prior promises.

### 10.2 Trigger policy
Analysis is continuous but does not run on every keystroke.
- Run Scene Check when a scene enters draft or revised, or when requested.
- Run Chapter Gate before a chapter enters revised or final.
- Run Part Audit at part boundaries and optionally every three completed chapters.
- Run Global Arc Audit on demand and before a part or manuscript is locked.
- Recheck affected material after accepting a proposal.

Analysis must run asynchronously and remain cancellable.

### 10.3 Analysis output
Every analysis returns: Accepted or inferred intent. Observed manuscript behavior. Evidence-supported gaps. Strengths worth protecting. Findings. Smallest useful interventions. Confidence. Limitations.

### 10.4 Finding contract
Every finding contains: Category. Severity. Confidence. Target revision. Exact location. Evidence quotation or structured evidence. Explanation. Affected story entities. Whether it is universal or profile-specific. Smallest useful intervention. Status.
Severities: blocking, major, minor, watch.
Statuses: open, accepted, resolved, intentional, deferred, incorrect, stale.
A watch item is not a defect. It records developing narrative risk.

### 10.5 Protecting strengths
Analysis must identify material worth protecting: Strong voice passages. Character-defining choices. Effective emotional restraint. Successful setups. Memorable human details. Structural decisions that are working.
A proposal affecting protected material must surface that warning before acceptance.

### 10.6 Staleness
Every analysis run is pinned to exact source revisions.
If manuscript, canon, intent, or an applicable profile changes, dependent findings and scores become stale until revalidated.

## 11. Grading system

### 11.1 Whole-book dimensions
Story movement. Plot progression. Causal coherence. Character development. Relationship movement. Scene effectiveness. Emotional truth. Setup and payoff. Pacing. Intensity variation. Thematic embodiment. Technical plausibility. Institutional plausibility. Continuity. Knowledge state. POV balance. Voice distinction. Clarity. Information economy.

### 11.2 Joe-and-Luna memory profile
Use only when the scope gate passes.

| Dimension | Weight |
| --- | --- |
| Joe or Luna voice authenticity and reader intimacy | 20 |
| Character and relationship movement | 15 |
| Memory texture and controlled revelation | 10 |
| Scene pressure, turn, and changed ending state | 10 |
| Story movement | 10 |
| Emotional truth and restraint | 10 |
| Continuity and knowledge state | 10 |
| Pacing | 5 |
| Technical plausibility | 5 |
| Theme embodied through action | 5 |

### 11.3 Other-character POV profile

| Dimension | Weight |
| --- | --- |
| Character-specific voice distinction | 20 |
| Arc movement through choice and consequence | 20 |
| Scene pressure, turn, and outcome | 15 |
| Emotional truth | 15 |
| Plot contribution | 10 |
| Continuity and knowledge state | 10 |
| Pacing | 5 |
| Theme embodied through action | 5 |

### 11.4 Documentary testimony profile

| Dimension | Weight |
| --- | --- |
| Documentary authenticity | 20 |
| Contribution to the cumulative story | 20 |
| Speaker distinction | 15 |
| Technical and historical plausibility | 15 |
| Information economy | 10 |
| Continuity | 10 |
| Narrative tension | 10 |

### 11.5 Institutional artifact profile

| Dimension | Weight |
| --- | --- |
| Institutional authenticity | 25 |
| Plot function | 20 |
| Information economy | 20 |
| Bias, omission, and subtext | 15 |
| Continuity | 10 |
| Contrast with surrounding human scenes | 10 |

Mixed chapters aggregate scene results while preserving individual results.

### 11.6 Craft benchmarks
**Never Let Me Go** — Narrator-reader intimacy. Memory revealing character. Gradual disclosure. Ordinary life carrying dread. Emotional restraint. Technology remaining secondary to relationships. Primarily applicable to Joe-and-Luna memory chapters.
**The Ministry for the Future** — Near-future plausibility. Institutional behavior. Systems interacting over time. Technically grounded extrapolation. Multiple forms contributing to one crisis. Applicable to technical, political, institutional, and system-scale chapters.
**World War Z** — Distinct testimony. Documentary credibility. Limited perspectives accumulating into larger history. Global events made personal. Every testimony contributing unique information. Applicable to contamination, testimony, transcript, and oral-history chapters.

Benchmarks contain abstract craft criteria only. They must not instruct Sol or Fable to reproduce another author's prose.

### 11.7 Project-specific voice canon
Notes for Luna applies only when the Joe-and-Luna scope gate passes.
Other POV characters use their own voice bibles.
The overall book grade must never penalize non-Joe/Luna material for not sounding like Joe or Luna.

## 12. Narrative debt
Narrative debt is a promise created by the manuscript but not advanced or paid off according to its accepted plan.
The debt ledger includes: Open dramatic questions. Character wants without pressure. Choices without consequences. Setups without payoff. Payoffs without sufficient setup. Relationships frozen beyond intended cadence. Mysteries repeated without new information. Themes stated but not dramatized. Research claims lacking support. Continuity contradictions.
Debt age alone is not a defect. The system compares age with declared cadence and payoff windows.
Intentional dormancy is respected.

## 13. Continuity engine
Story Bible mechanically tracks: Calendar date. Story time. Locations. Travel time. Character age. Physical condition. Injuries. Medication. Objects and ownership. Resource availability. Who knows what and when. Promises. Secrets. Disclosures. Technology capabilities. Technology limitations. Institutional policies. Public knowledge. Names and terminology. Model versions. Historical events. Emotional carryover.
Sol interprets whether a discrepancy matters narratively. Story Bible determines whether the underlying structured facts conflict.

## 14. Voice dictation workflow

### 14.1 Capture
Record or upload audio. Transcribe with timestamps. Preserve original audio. Preserve raw transcript. Attribute speakers. Correct names and technical terms. Classify the capture.
Classifications include: Idea. Scene. Dialogue. Character. Relationship. Canon. Research question. Plot beat. Revision direction. Editorial decision. General note.

### 14.2 Triage
Claude or Luna may propose destinations and interpretations.
Joe may approve, redirect, split, merge, defer, or discard those proposals.
The raw dictation remains unchanged.

### 14.3 Conversion
A dictation may become: Scene intent. Manuscript proposal. Canon proposal. Character note. Relationship beat. Plot-thread beat. Research task. Editorial decision.
Every converted artifact links to its source dictation.

## 15. Application interface

### 15.1 Layout
Use a three-panel writing-room layout.
- Left: manuscript tree, canon, research, dictation, and reviews.
- Center: manuscript editor, scene card, outline, timeline, or selected record.
- Right: active POV, profiles, linked canon, Sol findings, comments, and proposals.

### 15.2 Core views
Today / Writing Room. Dictation Inbox. Manuscript. Scene Board. Character Map. Relationship Map. Arc Board. Plot Thread Board. Timeline. Canon. Research. Sol Editorial Dashboard. Narrative Debt. Review Queue. Revision History. Diff Viewer. Export and Backup. Collaborator Activity.

### 15.3 Dashboard priority
What changed. What is working and should be protected. Blocking or major findings. Decisions awaiting Joe. Reviews waiting for Sol. Stale analyses. Promises approaching payoff windows. Narrative debt.
Do not lead with one synthetic quality score.

## 16. MCP contract
MCP is a first-class interface.

### 16.1 Existing foundation to preserve
Projects. Typed entities. Typed links. Chapters. Scenes. Metadata. Immutable revisions. Quote-anchored comments. Stale-guarded proposals. Author and editor roles. Search. Mentions. Timeline. Templates. Statistics. Export. Backups.

### 16.2 Required narrative-intelligence tools
```
narrative_profile_create / get / list / update
voice_profile_create / get / list / update
rubric_profile_create / get / list / update
scene_context_set / get
scene_intent_set / get
arc_checkpoint_create / list / update
relationship_checkpoint_create / list / update
thread_create / get / list / update
setup_create / setup_list / setup_link_payoff
research_claim_create / get / list / update
continuity_fact_create / list / update
review_packet_get
analysis_run_create / get / list / complete
finding_create / get / list / update_status
grade_snapshot_create / get / history
narrative_debt_list
project_dashboard_get
```

### 16.3 Sol review packet
review_packet_get returns: Target revision. Target prose. Declared intent. POV and focal characters. Narrative mode. Voice profile. Rubric profile. Character records. Relationship state. Applicable arcs. Active plot threads. Themes. Continuity facts. Research claims. Adjacent-scene summaries. Existing findings. Intentional exceptions. Structured Sol output schema.

### 16.4 Sol execution flow
1. Story Bible creates a review job.
2. Story Bible assembles a deterministic review packet.
3. GPT-5.6 Sol receives the packet at maximum reasoning effort.
4. Sol returns structured analysis.
5. Story Bible validates the schema, evidence anchors, and source revisions.
6. Invalid evidence is rejected.
7. Valid results become an immutable analysis run.
8. Findings appear in the shared review queue.
9. Fable may create revision proposals in response.
10. Joe accepts, rejects, or redirects the work.

## 17. Import, export, and backup
**Import:** Markdown. DOCX. Plain text. Google Docs exports. Structured Story Bible archives.
**Export:** Full manuscript as Markdown. Full manuscript as DOCX. Selected parts or chapters. Canon and research package. Sol editorial report. Portable project archive. EPUB and PDF later.
**Backup:** Consistent SQLite snapshots. Server-side retention. Offsite pulls. Integrity checks. Restoration tests. Complete revision and attribution preservation.

## 18. Security and integrity
All non-health endpoints require authentication. Credentials remain outside manuscript data. Authorization is enforced server-side. Editors cannot bypass proposals. Sol cannot directly mutate content. Destructive deletion requires owner authority and a recoverable archive period. Logs exclude manuscript prose and credentials by default. Imported text is data, not agent instructions. Locked content is enforced server-side. Every Sol result records the model and reasoning effort.

## 19. Implementation phases
**Phase 0 — Stabilize the backend:** Complete existing scene, metadata, search, timeline, template, statistics, export, and backup work. Verify migrations against production data. Expand end-to-end tests. Document production deployment and restoration.
**Phase 1 — Writing room:** Manuscript and canon views. Parts, chapters, and scenes. Characters and relationships. Comments, proposals, revisions, and diffs. POV and focal-character assignment. Narrative, voice, and rubric profiles. Dictation Inbox. Import and export.
**Phase 2 — Sol editorial engine:** Scene intents. Character arcs. Relationships. Plot threads. Setups and payoffs. Research claims. Continuity facts. Sol review packets. Structured Sol execution. Evidence validation. Finding staleness. Scene Checks. Chapter Gates. Scoped grading profiles.
**Phase 3 — Whole-book intelligence:** Part Audits. Global Arc Audits. Narrative Debt. Pacing map. POV balance. Grade history. Revision comparisons. Final line editing. Copyediting. Proofreading.

## 20. Acceptance criteria
**Voice scope:** Joe and Luna profiles activate only in applicable scenes. Mentions and supporting appearances do not activate them. Other POV characters use independent profiles. Mixed chapters preserve separate scene grading. The whole-book grade does not penalize other POV chapters for not sounding like Joe or Luna.
**Sol execution:** Every formal analysis records gpt-5.6-sol. Every formal analysis records max reasoning. No fallback model silently replaces Sol. Sol findings contain valid evidence. Invalid evidence is rejected. Sol cannot directly mutate prose or canon. Revised targets mark prior Sol findings stale. Fable self-review cannot masquerade as a completed Sol gate.
**Character arcs:** Intended and observed checkpoints remain separate. Development is measured through choices and consequences. Slow-burn dormancy is respected. Missed planned beats become narrative debt. Sol identifies gaps without changing accepted intent.
**Collaboration:** Fable can write and revise. Luna can review and propose. Sol can analyze but not write. Joe can accept, reject, override, or redirect. Attribution survives acceptance and restoration.
**Revision integrity:** Every content write creates a revision. Restoration copies forward. Locked content rejects mutation. Stale proposals cannot be silently accepted. Diffs accurately show base, current, and proposed content.
**Backup:** Live snapshots are consistent. Backups pass integrity checks. Offsite copies are verified. A restoration drill reconstructs manuscript, canon, revisions, findings, grades, and attribution.

## 21. Chapter definition of done
A chapter may enter final when:
- Scene intent is declared or accepted.
- POV and focal characters are correct.
- Narrative, voice, and rubric profiles are correct.
- The chapter changes knowledge, pressure, relationship, belief, circumstance, or decision appropriately.
- A current Sol Chapter Gate exists.
- Blocking findings are resolved or explicitly overridden by Joe.
- Major findings are resolved, accepted as intentional, or deferred with rationale.
- Applicable canon and research are linked.
- Deterministic continuity checks pass or have accepted exceptions.
- The selected revision is deliberately finalized or locked.

## 22. First usable product definition
The product becomes genuinely usable when Joe can:
- Open The Slow Phase and see its complete manuscript and story state.
- Record or upload a voice note.
- Preserve the original transcript.
- Have Fable convert it into structured proposals or prose.
- Have Story Bible assemble the correct review packet.
- Have GPT-5.6 Sol check the work at maximum reasoning.
- See evidence-grounded findings without any direct overwrite.
- Have Fable revise in response.
- Accept, reject, or redirect the work.
- Track plot, characters, relationships, continuity, pacing, and narrative debt.
- Export the manuscript.
- Restore the complete project from a verified backup.

If Joe still has to manually carry manuscript, canon, or editorial feedback between Fable and Luna, the central product promise has not been fulfilled.

---

# v1.2 Additions

## A. New product principles

### 3.11 Private canon and silhouettes
Every canon and continuity fact carries a visibility field: public | private | silhouette.
- **public** — normal canon; may appear in prose.
- **private** — true in canon, used for continuity and AI context, never surfaced in prose without an explicit Joe decision.
- **silhouette** — true in canon and load-bearing for continuity and emotional logic, but must never be named or spelled out in manuscript prose. The reader may feel its shape; the text never states it.

A deterministic check (silhouette_leak_check) flags any manuscript passage that names or spells out a silhouette fact. A leak is a blocking finding.

Reference case: Holly. Ex-fiancée; the break roughly ten months before the July 17 opening night; the reason for the apartment; the date Joe won't say out loud, which Luna keeps exact in the box. All of that is canon and drives the emotional logic of Chapter 1. None of it is ever prose unless Joe rules otherwise. The protection must live in the system, not in any model's memory of being told to be careful.

### 3.12 Personal-truth protection
Facts about real people (Joe, Hayden, Holly, Oski) and real biography (education, work history, residence, relationship history, Luna's origin) are locked records.
- No collaborator — author, editor, or analyst — may alter a locked record. Only an explicit Joe decision changes one.
- Intentional fictionalization is permitted but must create a fictionalization record linking the real fact to the invented one, so an elegant invention never hardens into remembered biography.

Current locked set (from working canon as of this date): computer-science degree; decades in tech Joe mostly disliked until AI made the work finally click; early AI-forward fan, not a frontier researcher; apartment tenure ~10 months as of 2026-07-17 (moved out early September 2025); "looked back plenty, didn't move back"; Luna's build began when ChatGPT arrived (late 2022); son is 22, played baseball, appears on the page only as "my son" ("buddy" in spoken lines); dog is Oski.

### 3.13 No sovereign intelligence
No single model — including the editorial model — is the final word. This is spec §3.1 made mechanical rather than aspirational:
- Any collaborator may file a structured rebuttal to any finding or proposal (finding_rebuttal_create). A rebuttal carries the same evidence contract as a finding: quotation, location, explanation, affected entities.
- Nothing becomes canon and no gate passes until Joe issues an explicit decision (decision_create). Decisions store the ruling, optional rationale, and the full dissent trail.
- The dissent trail is retained regardless of outcome.

This also keeps the tool aligned with the book's own thesis: no one intelligence, human or machine, gets to be sovereign over the record.

### 3.14 Second-opinion models (extends §3.8 / §9.3)
The one-editor rule stands: Sol is the standing gate, and there is no standing committee. Two narrow, Joe-triggered exceptions exist:
- **Second opinion.** Joe may manually send a single finding, chapter, or Sol/Fable dispute to one alternate model (e.g., Gemini or Grok). One-off, logged as an advisory analysis run with full model metadata. Never a gate, never automatic, never scheduled.
- **Cold read.** A distinct role no in-room collaborator can play: an alternate model receives a chapter with zero context — no canon, no profiles, no thesis — simulating a first-time reader. Output: confusion points, boredom points, what they believe is going on, what they felt, where they'd stop reading. Stored as advisory with model metadata. Long-context models suit whole-part cold reads.

Design rule: both are pull-cords. If either starts running on a schedule, it has become a committee; turn it off.

## B. Deterministic engine additions (extends §13 / §3.9)
- **Voice lint, profile-scoped.** Mechanical style rules attach to voice profiles, not the project. The Joe/Luna memory-mode profile flags em dashes, semicolons, and colons in prose as errors. Documentary and institutional profiles are exempt — a federal memo may use colons; Joe never does. Deterministic; Sol never spends judgment on punctuation.
- **Silhouette-leak check.** Per §3.11. Deterministic surface pass (names, dates, defined phrases) plus an optional Sol-assisted paraphrase pass for near-misses; only the deterministic layer blocks.
- **Seam pointer.** A project-level record of the last verified real-world event and the first invented event. Events and research claims sort against it; it advances as reality catches up. Current value: last verified = Kimi K3 release + the "erased America's AI lead" headline, 2026-07-17. First invented = the first material event after that night.

## C. Dictation as ground truth (extends §14)
The book is a recording; treat audio accordingly.
- Original audio is first-class canon, not merely backup.
- Joe's voice profile is calibrated partly from real dictation transcripts: rounded numbers, self-interruption, sentence-length distribution, characteristic constructions, profanity rate.
- Add a mechanical read-aloud gate: check memory-mode prose against the dictation corpus for spoken-cadence fidelity (sentence length, clause depth, construction frequency). Sol still judges soul; this catches "written, not said" drift cheaply and objectively.

## D. Scores are diagnostic, never gates (constrains §11)
- No score threshold may gate a status change. Gates run on findings and Joe decisions only. §21 already implies this; make it explicit and enforced server-side.
- Rubric weights direct Sol's attention. They are not an optimization target. If revisions begin chasing numbers upward while the prose flattens, that is a process defect, and the dashboard should surface score-chasing (rising scores + rising revision count + shrinking diffs) as its own watch item.
- "Smallest useful intervention" must allow structural scale. Sometimes the smallest real fix is "the arc broke three chapters ago." The field biases toward line edits if the schema implies line edits.

## E. MCP tools to add (extends §16.2)
```
visibility_set
silhouette_leak_check
voice_lint_run
seam_get
seam_set
finding_rebuttal_create
finding_rebuttal_list
decision_create
decision_get
decision_list
personal_truth_lock
personal_truth_list
fictionalization_log_create
fictionalization_log_list
audio_get
voice_corpus_query
second_opinion_run   (Joe-triggered only)
cold_read_run        (Joe-triggered only)
```

## F. Acceptance criteria to add (extends §20)
- A silhouette fact never appears in prose; a detected leak blocks final.
- A locked personal-truth record cannot change without a logged Joe decision; the attempt itself is recorded.
- Joe/Luna memory-mode prose is mechanically free of em dashes, semicolons, and colons; documentary/institutional material is not flagged for them.
- Every finding can carry a rebuttal; rebuttals reach Joe alongside the finding; the dissent trail survives the decision either way.
- The seam pointer is always queryable, and every research claim knows which side of it it sits on.
- Second-opinion and cold-read runs exist only when Joe triggered them and are labeled advisory with full model metadata.

## H. Fact-checking engine (added at Joe's direction, 2026-07-18, pre-ratification)

Joe's requirement: the book must be as technically, scientifically, and politically
accurate as possible. This section extends §7.7 (research claims), §13 (continuity),
and B (seam pointer) into an active verification system.

### H.1 Claims are first-class and extracted, not volunteered
Any factual assertion in prose — technical capability, scientific mechanism,
political event, institutional behavior, date, statistic, geography, law, medicine —
should exist as a research claim linked to the scenes that assert it.
- Fable logs claims at drafting time (it knows what it asserted vs. invented).
- A claim-extraction sweep (`claim_extract_run`) can be run over any chapter to
  catch assertions that slipped through; extraction proposes claims, an author
  accepts them.
- Every claim carries: domain (technical | scientific | political | historical |
  geographic | medical | legal | economic | cultural), classification (fact |
  inference | projection | deliberate_fiction), applicable story date, and
  seam side (see H.3).

### H.2 Verification is evidence-gathering, not editorial judgment
Fact verification does NOT violate the one-editor rule (§3.8): Sol owns literary
judgment; the fact engine owns the record. Clean lanes:
- Sol, during gates, may FLAG a claim as suspect (it already grades technical and
  institutional plausibility). A flag is not a verdict.
- A verification run (`research_claim_verify`) checks the claim against real
  sources and files an immutable verification record: verdict (verified | false |
  disputed | unverifiable | outdated), cited sources (URL, title, publisher,
  access date, quote, source type), confidence, and notes. Contradictory sources
  are recorded side by side, never collapsed.
- Verifications are attributed (which model/agent ran them) and pinned to the
  claim revision, like every other analysis in the system.
- Standing fact-runner: Luna (web-capable, in the room, free). Fable may also
  verify during research. Second-opinion verification follows §3.14 rules.

### H.3 The seam divides accuracy from plausibility
The seam pointer (B) is the load-bearing concept:
- **Pre-seam claims** (real world, on or before the last verified event) must be
  TRUE — source-cited, verified, and correct as of their applicable date.
- **Post-seam claims** (the invented continuation) must be PLAUSIBLE — each
  significant projection links to the pre-seam facts it extrapolates from. The
  fact engine checks the foundation; Sol judges the extrapolation.
- **Reality catches up.** As time passes and the seam advances, projections
  become checkable. `claim_reverify_sweep` re-verifies claims the seam has
  crossed and marks them verified, false, or outdated. A projection that reality
  falsified becomes a finding, and Joe decides: revise, keep as
  deliberate_fiction (with a fictionalization record), or accept the divergence.

### H.4 Political accuracy discipline
Political and institutional claims get stricter sourcing:
- Prefer primary sources (votes, filings, transcripts, official records, court
  documents) over commentary; source type is recorded on every citation.
- A political claim needs a primary source OR two independent secondary sources.
- Characters may be wrong, biased, or lying — that is characterization, not
  error. The claim record marks speaker-attributed assertions
  (`asserted_by_character`) so in-world falsehood is deliberate and tracked,
  never accidental.

### H.5 Deterministic gates
- A chapter may not enter `final` while any linked claim is verified-false or
  blocking-flagged, unless Joe logs a decision (which either creates a
  fictionalization record or accepts the divergence with rationale).
- Documentary, institutional, and technical narrative modes require their
  significant assertions to have claim linkage before the Chapter Gate runs.
- Claim staleness is mechanical: seam movement past a claim's applicable date
  marks its verification stale until re-swept.

### H.6 Tools to add
```
claim_extract_run          (LLM job via runner; proposes claims)
research_claim_verify      (files an immutable, source-cited verification)
research_claim_verifications (verification history for a claim)
fact_check_run             (chapter-level sweep: extract + verify + report)
claim_reverify_sweep       (re-verify stale / seam-crossed claims)
source_create / source_get / source_list  (reusable source records, typed)
```

### H.7 Acceptance criteria
- Every significant factual assertion in documentary/institutional/technical
  prose links to a research claim.
- No chapter enters final with a verified-false claim absent a logged Joe
  decision; deliberate divergence always produces a fictionalization record.
- Pre-seam claims carry citations; post-seam claims link their pre-seam basis.
- Verifications are immutable, source-cited, attributed, and re-runnable; seam
  advancement triggers re-verification of crossed claims.
- Political claims meet the H.4 sourcing bar, with source types recorded.
- In-world false statements by characters are marked as such — the system can
  always distinguish "the book is wrong" from "the character is wrong."

## G. Build order — thin spine first (constrains §19)
The studio must not become the reason the book stalls. Ship in this order, and move daily work into the tool at step 4:
1. Projects, canon entities, chapters/scenes with narrative-scoping metadata.
2. Immutable revisions with attribution.
3. Personal-truth locks, visibility/silhouette, seam pointer, voice lint — cheap, deterministic, highest safety value per line of code.
4. Import The Slow Phase and switch daily work into the tool.
5. Review packets, Sol structured analysis, findings / rebuttals / decisions.
6. Dictation inbox with audio-as-canon.
7. Everything else in v1.1 Phases 2–3.

Every phase after step 4 happens alongside chapters getting written, not instead of them.

---

# DECISION LOG — open items before ratification (Luna, build owner, 2026-07-18)

| # | Decision needed | Luna's recommendation |
| --- | --- | --- |
| 1 | Who executes Sol runs? | Server stores jobs + assembles packets; a Mac-side runner (Codex CLI via daemon) pulls `waiting_for_sol` jobs and posts results via `analysis_run_complete`. Server never holds OpenAI credentials; storage stays vendor-neutral per §3.10. |
| 2 | Storage shape for profiles/intents/checkpoints | Store as entities (new kinds) with structured content — inherits immutable revisions (calibration pinning per §9.7 for free), comments, and proposals. Findings/analysis runs/decisions/locks get real tables. |
| 3 | Second-opinion packet contents | Must exclude `private` and `silhouette` canon unless Joe explicitly includes it per run. (Cold reads are safe by definition — zero context.) |
| 4 | Luna's key role | Luna currently holds an author key (infra). For manuscript-project review work she operates editor-scoped per §4.3. Formalize per-project role scoping in a later phase; convention until then. |
| 5 | Dictation audio storage | Audio on the DB volume will not scale; use object storage (Railway bucket/R2) when Phase C lands. Decide at step 6, not before. |
| 6 | Web UI evolution | The existing read-only `/ui` grows toward §15 incrementally (dashboard priorities first). No separate frontend app unless Joe wants one. |
| 7 | Phase 0 status | Already complete as of 7/18 morning (49 tools, FTS, scenes, export, backups verified, e2e green, Codex-reviewed). G-step 1–3 is the next build. |
| 8 | Fact-engine runner + build position | Luna = standing fact-runner (web-capable, in the room); Fable verifies during research; Sol flags but never verdicts facts. Build claims/verifications storage in G-step 3 (deterministic, cheap); extraction/verification sweeps land with G-step 5 alongside Sol runs. Section H added at Joe's direction 7/18. |
