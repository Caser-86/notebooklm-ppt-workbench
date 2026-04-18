# Local Job Queue Design

## Summary

This spec upgrades the current synchronous execution model into a local persistent job queue suitable for the project's SQLite-first, single-machine architecture.

The queue is designed to support long-running operations such as:

- source analysis
- PPTX import
- imported rebuild

without forcing the API request itself to stay open until work completes.

## Product Goal

The system should be able to:

1. accept long-running jobs quickly
2. persist job state in the local database
3. execute jobs in a separate local worker process
4. expose job progress and results back to the frontend

This should improve reliability, user experience, and recoverability without introducing external infrastructure.

## Scope

This phase covers:

- a SQLite-backed local job queue
- a worker process that polls and executes jobs
- project-level job listing
- per-job status lookup
- frontend polling for job state

This phase does not cover:

- Redis
- Celery
- external distributed workers
- WebSocket push updates
- complex job priorities

## Recommended Approach

Use a **persistent database-backed local queue** built on the existing `Job` model.

This is the best fit for the current project because:

- the project already uses SQLite
- the agent already persists local state
- the app runs on a single machine
- long-running work is becoming common enough that request-time execution is no longer ideal

## Why Not Background Threads

Background threads inside the API process would be simpler at first, but they have clear weaknesses:

- API and execution lifecycle are tightly coupled
- process restarts can interrupt work badly
- observability and retry control are weaker

For the current product stage, a separate local worker process is a better tradeoff.

## Core Architecture

The design has three pieces:

1. **API process**
2. **database-backed job queue**
3. **worker process**

### API process

Responsibilities:

- create jobs
- return `job_id` immediately
- expose job status and history

### Database-backed queue

Responsibilities:

- persist queued work
- store result and error metadata
- coordinate retries and lock ownership

### Worker process

Responsibilities:

- poll the database for available jobs
- claim one job safely
- execute job handlers
- persist result, failure, and retry state

## Job Model Direction

Reuse the existing `Job` table instead of introducing a second parallel task table.

Add fields such as:

- `payload_json`
- `result_json`
- `error_message`
- `attempt_count`
- `max_attempts`
- `available_at`
- `started_at`
- `finished_at`
- `locked_by`
- `locked_at`

This keeps current project and status relationships intact while making the job system much more useful.

## Recommended Status Model

Use this minimal state machine:

- `queued`
- `running`
- `succeeded`
- `failed`
- `retryable`
- `cancelled`

### Meanings

- `queued`: waiting for worker pickup
- `running`: currently being processed
- `succeeded`: finished successfully
- `failed`: terminal failure
- `retryable`: failed but may run again
- `cancelled`: intentionally stopped

This state set is small enough to stay understandable while still supporting real operational behavior.

## Locking Strategy

The worker should only claim jobs that are:

- `queued`
- or `retryable` and due again

When claiming a job, the worker should write:

- `locked_by`
- `locked_at`
- `started_at`
- status -> `running`

If a worker dies mid-job, stale locks should eventually be recoverable based on time.

This avoids permanent queue deadlock.

## First Job Types To Queue

The first queued operations should be:

- `analyze_sources`
- `import_pptx`
- `rebuild_import`

These are the highest-value job types because they already involve meaningful work and can visibly benefit from async execution.

## API Design

This phase should keep the API small.

### New write behavior

Existing actions that are now long-running should enqueue work and return immediately with:

- `job_id`
- initial status

### New read endpoints

- `GET /jobs/{id}`
- `GET /projects/{id}/jobs`

These are enough for:

- job detail view
- project history
- frontend polling

This phase does not need:

- bulk cancellation
- priority edits
- advanced filtering UI

## Frontend Strategy

The frontend should use **polling**, not push.

Recommended behavior:

1. submit action
2. receive `job_id`
3. poll the job endpoint every few seconds
4. stop polling when the job reaches a terminal state
5. refresh affected project data after success

This is simpler and more reliable than WebSockets for the current local-app use case.

## UX Behavior

The user should see:

- immediate acknowledgement that work is queued
- clear `running` state
- success state with refreshed artifacts/history
- failure state with error reason
- retry option when appropriate

The queue should make the app feel more responsive, not more opaque.

## Worker Execution Model

The recommended local runtime is:

- API: `uvicorn app.main:app`
- worker: `python -m app.worker`

This keeps the service roles clear and avoids hidden execution inside the web server process.

## Failure Handling

The system should support:

- retryable failure for transient problems
- terminal failure for permanent problems
- stale-lock recovery

It should not require a full process restart for every failed long-running task.

## Success Criteria

This phase is successful when:

1. long-running operations enqueue instead of blocking the request
2. the worker can pick up and execute queued jobs
3. job state is visible through API endpoints
4. the frontend can poll and reflect job status
5. successful jobs refresh the relevant project views
6. failed jobs preserve useful error details

## Testing Strategy

This phase should include:

### 1. Job model and queue tests

Verify:

- job creation
- claim logic
- retry scheduling
- stale lock recovery

### 2. Worker handler tests

Verify:

- supported job types execute correctly
- success writes result data
- failure writes error data

### 3. API tests

Verify:

- enqueue endpoints return `job_id`
- job status endpoint works
- project job history endpoint works

### 4. Frontend tests

Verify:

- async actions enter queued/running states
- polling updates the UI
- terminal states refresh the right data

## Risks

The main risks are:

1. keeping synchronous and queued code paths inconsistent
2. making lock recovery too aggressive or too weak
3. adding queue complexity without enough visibility

This design reduces those risks by:

- reusing the existing `Job` model
- keeping the state machine small
- starting with polling and minimal job types

## Out Of Scope

This phase does not include:

- distributed workers
- external brokers
- real-time push status
- complex priorities
- DAGs or job dependencies

## Recommendation

Proceed with a local persistent queue built on the existing `Job` table, executed by a separate worker process and surfaced via polling.

This is the right next step because the project now has enough import and rebuild complexity that synchronous execution will increasingly hurt reliability and UX.
