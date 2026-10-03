# Multi-Agent AI Orchestration System — Architecture Specification

## 1. High-Level System Architecture

This system implements an asynchronous, event-driven multi-agent architecture designed for high responsiveness, state isolation, and auditability.

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Layer                         │
│                    React + TypeScript UI                    │
└──────────────────────────┬───────▲──────────────────────────┘
      1. POST /api/tasks   │       │  2. WebSocket Connection
                           ▼       │     (Live Event Streaming)
┌──────────────────────────────────┴──────────────────────────┐
│                          API Layer                          │
│                        FastAPI Server                       │
└──────┬───────────────────┬───────────────────────────▲──────┘
       │                   │                           │
3. Init│                   │ 4. Trigger Graph          │ 11. Push Event
  Task │                   ▼                           │     to Channel
┌──────▼──────┐   ┌───────────────────────────────┐    │
│ Persistence │   │     Orchestration & State     │    │
│    Layer    │   │      LangGraph Workflow       │    │
│  PostgreSQL │   │  [Planner, Researcher, Synth] │    │
└──────▲──────┘   └───┬─────────────────────────▲─┘    │
       │              │                         │      │
       │ 10. Log State│ 6. Publish Tool Task    │ 5. Completion
       │     Trans.   ▼                         ▼      │
       │         ┌───────────┐           ┌─────────────┴──────┐
       └─────────┤Redis Queue├───────────┤ External LLM Engine│
                 └─────┬─────┘           │       (Groq)       │
                       │ 7. Consume      └────────────────────┘
                       ▼
                 ┌───────────┐
                 │  Celery   │
                 │  Worker   │
                 └─────┬─────┘
                       │ 8. Execute Tool
                       ▼
               ┌───────────────────────┐
               │     External Tools    │
               │ Brave / Weather / Calc│
               └───────────────────────┘
```

---

## 2. End-to-End Architectural Flow Breakdown

1. **HTTP POST `/api/tasks`**:
   The user enters a complex multi-part objective in the React UI. The client issues a non-blocking `POST` request to FastAPI.
2. **WebSocket Connection (`/api/ws/{task_id}`)**:
   Immediately upon receiving `{ "task_id": "uuid" }`, the client opens a bi-directional WebSocket connection with an automatic heartbeat ping mechanism.
3. **Initialize Task & State**:
   FastAPI creates a new `TaskRun` record in PostgreSQL with status `PENDING` and commits it, guaranteeing an immediate recovery anchor.
4. **Trigger Graph Execution**:
   FastAPI spawns the LangGraph state machine asynchronously in the background (`asyncio.create_task` / `BackgroundTasks`), freeing the HTTP worker to return within 15 milliseconds.
5. **Prompt / Function Call Completion**:
   The Planner node decomposes the task into sequential steps and invokes Groq's high-speed inference engine (`llama-3.3-70b-versatile`).
6. **Publish Tool Task**:
   When the Researcher determines an external I/O tool is needed, it dispatches the tool call to the Redis queue (`celery_app.task`).
7. **Consume Task**:
   A dedicated Celery worker pulls the task from Redis without blocking the FastAPI event loop.
8. **Execute Tool**:
   The Celery worker invokes the external tool (Brave Search API, OpenWeatherMap API, or the safe AST Calculator sandbox).
9. **Return Tool Result**:
   The Celery worker stores the structured `ToolResult` in Redis backend DB 1, which the Researcher node retrieves asynchronously.
10. **Log State Transition**:
    Every state change, thought, tool invocation, and tool result is immediately committed to PostgreSQL in the `agent_events` table as structured JSONB.
11. **Push Event to Channel**:
    Simultaneously, `EventService` pushes the event envelope to the active WebSocket channel, allowing React to render live updates in real time.

---

## 3. Component Architecture

### A. API Layer (FastAPI)
- **Port:** 8000
- **Responsibilities:**
  - Request validation via strict Pydantic models.
  - Asynchronous background task dispatching.
  - WebSocket connection management with keep-alive heartbeat loop.
  - CORS security middleware.

### B. Persistence Layer (PostgreSQL 15+)
- **Tables:**
  - `task_runs`: Primary record tracking run lifecycle (`PENDING`, `RUNNING`, `COMPLETED`, `FAILED`), timestamps, and final synthesized outputs.
  - `agent_events`: Granular audit trail tracking agent thoughts, tool inputs/outputs, errors, and timestamps with indexed foreign keys.

### C. Task Queue & Broker (Redis 7+ & Celery)
- **Redis DB 0:** Celery message broker.
- **Redis DB 1:** Celery result backend.
- **Celery Worker:** Standalone worker process decoupled from the web server, isolating heavy I/O operations and external API latency.

### D. Multi-Agent Engine (LangGraph)
- **State Definition:** Shared `AgentState` TypedDict containing task ID, prompt, step array, research observations, tool history, and final answer.
- **Graph Topology:**
  - `START` → `Planner`
  - `Planner` → `Researcher`
  - `Researcher` → `Router` (conditional edge)
  - `Router` → `Researcher` (if steps remaining)
  - `Router` → `Synthesizer` (if steps completed)
  - `Synthesizer` → `END`

---

## 4. Fault Tolerance and Resilience

1. **Non-Crashing Tool Design:**
   All tools (Weather, Search, Calculator) return structured `ToolResult` envelopes with `success: False` and `error_type` instead of raising unhandled Python exceptions.
2. **Safe Math Sandbox:**
   The calculator uses Python's `ast.parse` to traverse the abstract syntax tree directly. It evaluates only whitelisted mathematical operators and functions. `eval()` and `exec()` are strictly banned.
3. **Graceful Degradation:**
   If API keys are missing or external APIs return 401/429/500, tools provide informative synthesized fallbacks to allow agents to continue reasoning rather than crashing.
4. **WebSocket Keep-Alives:**
   A dedicated background task sends periodic heartbeat frames every 15 seconds to prevent reverse proxy and Docker bridge idle disconnects.
