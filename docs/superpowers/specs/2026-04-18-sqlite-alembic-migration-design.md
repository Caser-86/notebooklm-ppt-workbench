# SQLite-First Alembic Migration Design

## Summary

This spec upgrades the project's database schema management from ad-hoc compatibility patches to a formal migration workflow based on Alembic.

The immediate target is the local SQLite database used by the agent:

- `agent/data/app.db`

The design is intentionally SQLite-first. It does not attempt to solve future multi-database concerns in this phase.

## Product Goal

The project should have a reliable, explicit, and testable schema upgrade path so that:

1. new local databases initialize cleanly
2. existing local databases upgrade safely
3. future model changes stop depending on one-off startup patches
4. schema evolution becomes predictable for both development and demo environments

## Current Problem

Right now the project uses a lightweight compatibility patch in `agent/app/db.py` to add missing columns to the legacy `project` table.

That helped recover from one real-world failure, but it is not a durable schema management strategy because:

- it only covers a narrow set of cases
- it does not create a versioned migration history
- it makes future schema changes harder to reason about
- it does not give developers a formal upgrade workflow

## Recommended Direction

Use **Alembic as the formal schema migration system**, with SQLite as the first and only required target for this phase.

This means:

- Alembic becomes the official path for schema changes
- model changes are paired with migration revisions
- startup upgrades run against Alembic's versioned history
- the current compatibility patch is treated as temporary transition support, not the long-term strategy

## Scope

This phase covers:

- Alembic setup inside `agent/`
- baseline schema migration
- safe upgrade path for existing SQLite databases
- startup-time upgrade-to-head behavior
- regression tests for new and old local databases

This phase does not cover:

- PostgreSQL support
- database rollback UX
- branching/multi-head migration strategy for larger teams
- operational deployment migration orchestration

## Project Structure

The recommended layout is the standard Alembic structure inside `agent/`:

- `agent/alembic.ini`
- `agent/alembic/env.py`
- `agent/alembic/script.py.mako`
- `agent/alembic/versions/`

The application DB integration should remain in:

- `agent/app/db.py`

This keeps migration logic close to the backend while staying recognizable to anyone familiar with Alembic.

## Ownership Boundaries

### `agent/app/db.py`

Should be responsible for:

- resolving database file location
- creating the SQLite engine
- exposing sessions
- ensuring upgrade-to-head happens during startup

It should not remain the long-term home for schema-altering business logic.

### Alembic files

Should be responsible for:

- defining versioned schema changes
- executing forward upgrades
- establishing schema state history

### SQLModel models

Should remain the source of application schema intent, but not the only mechanism for updating the real database.

## Migration Workflow

The formal workflow should become:

1. update SQLModel models
2. create an Alembic revision
3. inspect and adjust the generated migration
4. upgrade the database to `head`

This replaces the current informal workflow where a model change may be paired with a startup patch or a one-off SQLite alteration.

## Runtime Behavior

At runtime the backend should do only a small amount of database bootstrapping:

1. ensure the data directory exists
2. create/connect to the SQLite database file
3. upgrade the database to the latest Alembic revision

The backend should not need to manually patch individual columns as the main upgrade path once Alembic is established.

## Existing Database Strategy

This is the most important compatibility part of the design.

### Step 1: Baseline the current schema

Create a baseline migration that represents the current intended schema.

This gives the project an official starting point for future revisions.

### Step 2: Support legacy local databases

Add a targeted legacy-upgrade path so that older local SQLite databases can move safely to the current schema.

This should focus on real legacy states already observed in this project, such as missing columns on the `project` table.

### Step 3: Keep the current compatibility patch only as transition support

The existing `ensure_legacy_project_columns()` helper should not remain the long-term primary upgrade mechanism.

Instead:

- short term: keep it as a temporary safety net while Alembic integration stabilizes
- medium term: shrink it or remove it once legacy migration coverage is proven by tests

## Recommended Rollout Strategy

### Phase 1

Establish Alembic and support:

- clean database initialization
- upgrade of current local SQLite databases
- repeatable local upgrade testing

### Phase 2

Once stable:

- reduce or remove direct startup schema patching
- require future schema changes to go through Alembic revisions

## Testing Strategy

This phase should include four layers of verification.

### 1. Migration unit tests

Verify that:

- legacy database shapes upgrade successfully
- missing columns are restored
- existing data is preserved

### 2. Clean database initialization test

Verify that an empty SQLite file upgraded to `head` produces the expected working schema.

### 3. Startup integration test

Verify that backend startup upgrades the database before normal API use.

### 4. API regression tests

Verify that after upgrade the current core flows still work:

- project creation
- project detail updates
- import history
- rebuild history
- source history

## Acceptance Criteria

This migration phase is successful when:

1. Alembic is configured and committed under `agent/`
2. a clean SQLite database upgrades to the current schema
3. a legacy SQLite database upgrades without breaking existing data
4. startup no longer depends on one-off schema patches as the primary upgrade path
5. current backend API tests still pass after migration integration
6. future schema changes have a clear formal process

## Risks

The main risks are:

1. creating a baseline that does not match the real current schema
2. breaking old local databases during first migration rollout
3. leaving both Alembic and manual patching active in conflicting ways

This design reduces those risks by:

- keeping the scope SQLite-only
- explicitly planning for legacy local database upgrade
- treating the current patch as temporary transition support instead of permanent schema logic

## Out Of Scope

This phase does not include:

- multi-database migration support
- Postgres compatibility work
- production deployment migration orchestration
- developer tools for rollback or down-revision workflows beyond what Alembic already provides

## Recommendation

Proceed with a SQLite-first Alembic migration system that:

- establishes a formal baseline
- upgrades old local databases safely
- becomes the official schema evolution path

This is the right time to do it because the project now has enough model and persistence complexity that continuing with ad-hoc schema patching will become progressively more expensive and fragile.
