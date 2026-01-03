# Polling Survey AI Moderator (MVP)
### Programming Plan & Success Benchmarks

Anonymous structured polling with AI-powered neutral follow-ups  
Emerson-style survey moderation

---

## Project Overview

**Goal**
- Build a structured polling MVP with AI-driven probing
- Capture true opinions and policy preferences
- Prioritize simplicity, neutrality, and low cost

**Core Characteristics**
- Single-user MVP
- Anonymous sessions
- Predefined baseline questions
- AI follow-ups (max 3 per question)

**Definition of Success**
- A full survey can be completed end-to-end
- All interactions are persisted and exportable

---

## Phase 0 — Repository & Project Integrity

**Goal**
Ensure the codebase is complete and consistent.

**Key Actions**
- Verify directory structure
- Confirm `.env.example` exists
- Confirm Docker + backend files exist
- Confirm survey JSON files exist

**Benchmark**
- `tree /F` matches expected structure
- No placeholder files blocking startup

**Deliverable**
- Repo is ready for local execution

---

## Phase 1 — Local Boot & Service Health

**Goal**
Confirm the application boots successfully.

**Key Actions**
- Run `docker compose up --build`
- Monitor logs for crashes
- Access API endpoints

**Benchmark**
- Containers remain running
- `/health` returns healthy
- `/docs` loads Swagger UI

**Deliverable**
- Verified running API

---

## Phase 2 — Database & Schema Verification

**Goal**
Ensure database schema is created and writable.

**Key Actions**
- Confirm Alembic migrations run
- Inspect Postgres tables
- Start a session to write data

**Benchmark**
- Tables exist in Postgres
- Session row is written
- No migration errors

**Deliverable**
- Verified DB schema and persistence

---

## Phase 3 — Core Consumer Loop (Baseline Questions)

**Goal**
Prove baseline survey flow works end-to-end.

**Key Actions**
- Start a session
- Render baseline question
- Submit baseline answer

**Benchmark**
- First question returned
- Answer stored in DB
- Next step returned (follow-up or move on)

**Deliverable**
- One completed baseline question cycle

---

## Phase 4 — Follow-Up Agent Behavior (Core IP)

**Goal**
Validate AI probing logic matches polling spec.

**Test Scenarios**
1. Early stop (clear motivation)
2. Full 3-probe sequence
3. Clarification for ambiguous answers

**Benchmark**
- Max 3 follow-ups
- Stops early when policy preference is clear
- Neutral, non-leading questions
- Follow-up reason stored

**Deliverable**
- 3 example transcripts

---

## Phase 5 — Special Case Handling

**Goal**
Ensure guardrails behave correctly.

**Prefer Not To Answer**
- Skips follow-ups
- Moves to next baseline question

**End Interview**
- Stops immediately
- Session marked as ended

**Benchmark**
- No follow-ups after PNA
- End interview halts flow immediately

**Deliverable**
- Transcripts showing PNA and End Interview

---

## Phase 6 — Admin View & Data Export

**Goal**
Confirm data is reviewable and exportable.

**Key Actions**
- List sessions
- View full transcripts
- Export JSON and CSV

**Benchmark**
- Admin endpoints show full transcripts
- Export includes baseline answers, follow-ups, reasons, timestamps
- CSV and JSON usable for analysis

**Deliverable**
- Sample JSON and CSV exports

---

## Phase 7 — Cost & Reliability Controls

**Goal**
Ensure MVP remains cheap and predictable.

**Key Actions**
- Verify summary reduces context size
- Confirm follow-up calls are bounded
- Inspect model call logs

**Benchmark**
- ≤ 3 follow-ups per baseline question
- Summary ≤ 80 words
- Model metadata logged (latency, model)

**Deliverable**
- Cost/telemetry snapshot

---

## Phase 8 — MVP Hardening & Release Readiness

**Goal**
Prepare MVP for demo or deployment.

**Key Actions**
- Add basic tests
- Improve README instructions
- Fresh setup from scratch

**Benchmark**
- Tests pass
- Fresh clone → run → survey completes
- No manual DB intervention

**Deliverable**
- Release Candidate MVP

---

## Final Success Checklist

☑ Docker stack boots cleanly  
☑ Sessions persist correctly  
☑ Follow-ups behave deterministically  
☑ Guardrails work (PNA / End Interview)  
☑ Admin and export functions work  
☑ Cost is bounded and predictable  

**Outcome**
A credible, research-grade polling MVP

---

## Post-MVP Roadmap

**Enhancements**
- Skip logic / branching
- Survey authoring UI
- Multi-user concurrency

**Deployment**
- AWS App Runner or Lightsail
- Managed Postgres (RDS)

**Research Extensions**
- Opinion clustering
- Confidence scoring analysis
- Longitudinal survey comparison
