# Multi-Agent AI Orchestration System — Evaluation & System Design Document

This document fulfills Core Requirement 11 (`EVALUATION.md`) for the Multi-Agent AI Orchestration system.

---

## 1. Orchestration Framework Selection: LangGraph vs. AutoGen

### Selection: LangGraph
We selected **LangGraph** (by LangChain) as the primary orchestration framework for this production system over Microsoft AutoGen.

### Rationale:
1. **Explicit Graph Topologies and Controlled State Transitions:**
   AutoGen relies primarily on multi-agent conversation patterns (chat rounds between ConversableAgents), where routing is often emergent or conversational. In contrast, LangGraph models agent workflows as explicit deterministic Directed Acyclic Graphs (DAGs) and cyclical State Machines with clear nodes and conditional edges.
2. **First-Class Shared State Context:**
   LangGraph's state machine pattern centers on a single typed state object (`AgentState`) passed into each node and atomically updated via reducer semantics. This prevents conversational context bloat where agents repeat previous dialogues.
3. **Deterministic Cyclic Looping:**
   Complex agentic problems require conditional looping (e.g., repeating the `Researcher` node for each item in the plan formulated by the `Planner`). LangGraph's `add_conditional_edges` provides deterministic routing that transitions back to `Researcher` until `current_step_index >= len(plan)`, at which point control transitions to `Synthesizer`.
4. **Seamless Async Execution & Asynchronous Persistence:**
   LangGraph natively integrates with `asyncio`, allowing us to invoke external Celery tasks, persist event logs to PostgreSQL via SQLAlchemy async sessions, and stream JSON events over WebSockets without blocking.

---

## 2. Specialized Agent Roles & System Prompts

The system defines three distinct, specialized AI agents:

### Agent 1: The Planner
- **File:** `backend/app/agents/planner.py`
- **Role:** Analyzes the overarching user query, extracts core intents, and decomposes the goal into a minimal, ordered sequence of 2–4 executable research/calculation sub-tasks.
- **System Prompt:**
```text
You are the Lead Planning Agent in an advanced multi-agent AI orchestration system.
Your responsibility is to analyze the user's objective and formulate a lean, sequential, and highly actionable execution plan.

Guidelines:
1. Break down the user prompt into 2 to 4 discrete, logical research or calculation steps.
2. Identify which external tools (e.g. 'weather', 'web_search', 'calculator') will be required for each step.
3. Keep each step concise and specific.
4. Output your plan strictly as a JSON array of strings, where each string is an actionable task.
```

### Agent 2: The Researcher
- **File:** `backend/app/agents/researcher.py`
- **Role:** Operates in a state-driven loop. For each sub-task in the plan, it identifies the necessary tool, validates arguments against Pydantic schemas, dispatches execution to Celery workers via Redis, inspects tool outputs, and handles errors gracefully.
- **System Prompt:**
```text
You are the Senior Research and Tool Execution Agent.
Your responsibility is to take a single step from the master plan, determine which tool to execute, and gather accurate real-world data.

Available Tools:
1. 'weather' (parameters: location: str, units: 'metric' or 'imperial')
2. 'web_search' (parameters: query: str, count: int)
3. 'calculator' (parameters: expression: str)

Guidelines:
- If a tool is needed, invoke the tool with precise, validated arguments.
- Analyze the tool output carefully. If a tool returns an error or warning, note it and adapt your summary rather than failing.
- Format your findings clearly for the Synthesizer agent.
```

### Agent 3: The Synthesizer
- **File:** `backend/app/agents/synthesizer.py`
- **Role:** Consolidates the original user prompt, the master execution plan, and all empirical evidence gathered across research loops to draft a comprehensive, well-structured final markdown report.
- **System Prompt:**
```text
You are the Lead Synthesizer and Reporting Agent.
Your responsibility is to review the original user request, the plan established by the Planner, and all empirical evidence and tool results gathered by the Researcher.

Guidelines:
1. Produce a comprehensive, beautifully structured response directly addressing the user's prompt.
2. Organize your answer with clear Markdown headings, bullet points, and key takeaways.
3. Explicitly cite specific facts, temperatures, figures, and calculations provided by the Researcher.
4. If any tool encountered limitations or fallback estimates, acknowledge them gracefully.
5. Provide actionable recommendations, packing advice, or insights tailored to the user's inquiry.
```

---

## 3. Custom Tools: Schemas, Execution & Error Handling

All tools inherit strict Pydantic validation schemas, zero-crash exception handling, and standardized `ToolResult` envelopes:

```python
class ToolResult(BaseModel):
    tool_name: str
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    retryable: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

### Tool 1: Web Search (`web_search`)
- **File:** `backend/app/tools/web_search.py`
- **Underlying Provider:** Brave Search API (`https://api.search.brave.com/res/v1/web/search`)
- **Pydantic Schema:**
  - `query: str` (required, non-empty search phrase)
  - `count: int` (optional, default: 5, ge: 1, le: 10)
- **Expected Output:**
  ```json
  {
    "query": "electric vehicles battery advances 2026",
    "total_results": 2,
    "results": [
      {
        "title": "Solid State Battery Breakthroughs",
        "url": "https://example.org/ev",
        "snippet": "Commercial solid state cells enter production..."
      }
    ]
  }
  ```
- **Error Handling Strategy:**
  - Catches `httpx.TimeoutException` returning `TIMEOUT_ERROR` (`retryable=True`).
  - Catches HTTP 401/403 returning `AUTH_ERROR`.
  - Catches HTTP 429 returning `RATE_LIMIT_ERROR`.
  - If API key is not configured, provides simulated search intelligence rather than halting the system.

### Tool 2: Weather Query (`weather`)
- **File:** `backend/app/tools/weather.py`
- **Underlying Provider:** OpenWeatherMap API (`https://api.openweathermap.org/data/2.5/weather`)
- **Pydantic Schema:**
  - `location: str` (required, e.g. "Tokyo, JP")
  - `units: Literal['metric', 'imperial']` (optional, default: "metric")
- **Expected Output:**
  ```json
  {
    "location": "Tokyo, JP",
    "temperature": "21.5°C",
    "feels_like": "21.0°C",
    "condition": "Partly Cloudy",
    "humidity": "65%",
    "wind_speed": "3.5 m/s",
    "units": "metric"
  }
  ```
- **Error Handling Strategy:**
  - Catches HTTP 404 returning `LOCATION_NOT_FOUND` with suggestions to check spelling.
  - Catches HTTP 401 returning `AUTH_ERROR`.
  - Catches connection timeouts returning `TIMEOUT_ERROR`.
  - Provides realistic meteorological estimations for common cities when running without external credentials.

### Tool 3: Safe AST Calculator (`calculator`)
- **File:** `backend/app/tools/calculator.py`
- **Engine:** Python `ast.parse` Abstract Syntax Tree recursive sandbox (**Zero use of `eval()` or `exec()`**).
- **Pydantic Schema:**
  - `expression: str` (required mathematical formula)
- **Supported Syntax:**
  - Binary Operators: `+`, `-`, `*`, `/`, `//`, `%`, `**`
  - Unary Operators: `-`, `+`
  - Whitelisted Functions: `sqrt`, `round`, `abs`, `min`, `max`, `sin`, `cos`, `tan`, `log`, `log10`, `exp`, `ceil`, `floor`
  - Safe Constants: `pi`, `e`
- **Expected Output:**
  ```json
  {
    "expression": "(23 * 9/5) + 32",
    "result": 73.4
  }
  ```
- **Error Handling Strategy:**
  - `ZeroDivisionError` is caught and returned as `MATH_ERROR` ("Division by zero is mathematically undefined").
  - `SyntaxError` is caught and returned as `SYNTAX_ERROR`.
  - Malicious AST nodes (calls to `__import__`, `os.system`, attribute lookups, lambdas) raise explicit sandbox violations.
  - Large exponential attacks (e.g. `9999 ** 9999`) are caught by complexity checks.

---

## 4. Shared State Specification (`AgentState`)

The state dictionary is defined in `backend/app/agents/state.py` as a `TypedDict`:

| Field | Type | Description |
| :--- | :--- | :--- |
| `task_id` | `str` | UUIDv4 uniquely identifying the task run. |
| `prompt` | `str` | Original user inquiry. |
| `plan` | `List[str]` | Decomposed execution steps created by the Planner. |
| `current_step_index` | `int` | Counter tracking the active step index in the loop. |
| `research_results` | `List[Dict[str, Any]]` | Accumulated tool outputs and empirical evidence. |
| `tool_history` | `List[Dict[str, Any]]` | Complete audit log of all tool invocations and results. |
| `messages` | `List[Dict[str, str]]` | Intermediate agent communications. |
| `final_result` | `Optional[str]` | Final synthesized markdown report. |
| `status` | `str` | Current workflow state (`INITIALIZED`, `RESEARCHING`, `COMPLETED`). |
| `error` | `Optional[str]` | Error message if a fatal failure occurred. |

---

## 5. Database Auditability Architecture

Persistent audit logging is handled by PostgreSQL via SQLAlchemy models:
- **`task_runs`**:
  - `id` (UUID Primary Key)
  - `prompt` (Text)
  - `status` (`PENDING`, `RUNNING`, `COMPLETED`, `FAILED`)
  - `final_result` (Text)
  - `error_message` (Text)
  - `created_at`, `started_at`, `completed_at` (DateTime)
- **`agent_events`**:
  - `id` (UUID Primary Key)
  - `task_run_id` (ForeignKey to `task_runs.id`, indexed)
  - `agent_name` (String, e.g. "Planner", "Researcher", "Synthesizer", "Weather Tool")
  - `event_type` (String, e.g. `AGENT_STARTED`, `PLAN_CREATED`, `TOOL_INVOCATION`, `TOOL_RESULT`, `FINAL_RESULT`)
  - `payload` (JSON / JSONB storing full arguments and responses)
  - `timestamp` (DateTime, indexed)

---

## 6. Asynchronous Queueing with Redis & Celery

To prevent long-running external API calls or mathematical computations from blocking FastAPI's single-threaded async event loop:
1. Tool executions are wrapped in `@celery_app.task`.
2. The agent layer calls `async_dispatch_tool(tool_name, arguments)`, which dispatches the task to Redis DB 0 (`.delay()`) and polls the result asynchronously using `asyncio.sleep` non-blocking waits.
3. If Celery or Redis is temporarily down in lightweight standalone mode, the dispatcher automatically executes the tool safely inside an `asyncio` thread pool executor without crashing.

---

## 7. Real-Time Streaming & WebSocket Lifecycle

- **Endpoint:** `WS /api/ws/{task_id}`
- **Historical Event Replay:** When a client connects or refreshes, the backend automatically replays all previously persisted `agent_events` from PostgreSQL.
- **Heartbeat & Keep-Alive:** The server runs a background heartbeat task that pushes an event frame every 15 seconds, preventing timeouts across Docker network bridges, proxies, or firewalls.
- **Graceful Disconnects:** Handled cleanly through the `WebSocketConnectionManager` without leaking open file descriptors or raising unhandled exceptions.
