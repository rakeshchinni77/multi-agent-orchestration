# Multi-Agent AI Orchestration System

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-StateGraph-orange.svg)](https://langchain-ai.github.io/langgraph/)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev/)
[![Docker Compose](https://img.shields.io/badge/Docker-5_Services-2496ED.svg)](docker-compose.yml)

A stateful, production-grade **Multi-Agent AI Orchestration System** capable of decomposing complex user goals, executing multi-step research through a distributed worker queue, and synthesizing actionable reports in real time.

Built with **LangGraph**, **FastAPI**, **React (TypeScript)**, **PostgreSQL**, **Redis**, and **Celery**, powered by **Groq Cloud LLM** (`llama-3.3-70b-versatile`) and real external tools (**Brave Search API**, **OpenWeatherMap API**, and a **Safe AST Calculator**).

---

## 🌟 Key Features

- **Autonomous Multi-Agent Collaboration:** Specialized **Planner**, **Researcher**, and **Synthesizer** agents operating over an explicit state machine.
- **Stateful Looping & Routing:** LangGraph cyclical graph with conditional edges that iteratively loops until all sub-goals are fulfilled.
- **Asynchronous Tool Offloading:** I/O heavy operations offloaded to a distributed **Celery** worker pool backed by **Redis**, keeping the FastAPI event loop responsive.
- **End-to-End Auditability:** Relational persistence in **PostgreSQL** tracking all task lifecycles (`task_runs`) and granular agent thoughts, parameters, and results (`agent_events`).
- **Live WebSocket Event Streaming:** Bi-directional real-time telemetry streaming agent state transitions directly to the React frontend with automatic keep-alive heartbeats and reconnect replay.
- **Ultra-Safe Math Sandbox:** Custom AST-based mathematical evaluator evaluating formulas with zero risk of code injection (zero `eval()`).
- **Modern Glassmorphic UI:** Sleek dark-mode interface featuring dynamic timeline animations, expandable tool payload inspects, and copyable reports.
- **One-Command Orchestration:** Ready to run anywhere via `docker compose up --build` with integrated service healthchecks.

---

## 🏗️ Architecture Diagram

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

## 📁 Project Structure

```
multi-agent-orchestration/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── tasks.py          # Primary REST task endpoints
│   │   │   │   └── websocket.py      # Real-time WebSocket streaming
│   │   │   └── schemas.py            # Pydantic API schemas
│   │   ├── core/
│   │   │   ├── config.py             # Pydantic Settings & environment
│   │   │   ├── logging.py            # Structured logging
│   │   │   └── security.py           # Sanitization & UUID validation
│   │   ├── db/
│   │   │   ├── base.py               # SQLAlchemy Base
│   │   │   ├── models.py             # TaskRun & AgentEvent models
│   │   │   ├── session.py            # Async engine & sessionmaker
│   │   │   └── repositories.py       # Asynchronous repository queries
│   │   ├── agents/
│   │   │   ├── state.py              # AgentState TypedDict
│   │   │   ├── prompts.py            # System prompts for 3 agents
│   │   │   ├── planner.py            # Planner agent node
│   │   │   ├── researcher.py         # Researcher agent node
│   │   │   ├── synthesizer.py        # Synthesizer agent node
│   │   │   ├── router.py             # Conditional routing edge
│   │   │   ├── llm.py                # Groq ChatGroq connector
│   │   │   └── graph.py              # Compiled LangGraph StateMachine
│   │   ├── tools/
│   │   │   ├── schemas.py            # Tool Pydantic input schemas
│   │   │   ├── web_search.py         # Brave Search API integration
│   │   │   ├── weather.py            # OpenWeatherMap API integration
│   │   │   ├── calculator.py         # Safe AST mathematical sandbox
│   │   │   └── registry.py           # Central tool registry
│   │   ├── worker/
│   │   │   ├── celery_app.py         # Celery instance configuration
│   │   │   ├── tasks.py              # Diagnostic ping tasks
│   │   │   └── tool_tasks.py         # @celery_app.task tool wrappers
│   │   └── services/
│   │       ├── task_service.py       # Task lifecycle orchestrator
│   │       ├── event_service.py      # Event bus (DB + WebSockets)
│   │       └── websocket_manager.py  # Active connection registry
│   ├── tests/                        # Pytest suite
│   ├── requirements.txt
│   ├── Dockerfile
│   └── pytest.ini
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── TaskForm.tsx          # Prompt input & quick examples
│   │   │   ├── AgentTimeline.tsx     # Live vertical event timeline
│   │   │   ├── AgentCard.tsx         # Agent state card component
│   │   │   ├── ToolEvent.tsx         # Tool execution inspector
│   │   │   ├── FinalResult.tsx       # Formatted solution display
│   │   │   └── StatusBadge.tsx       # Status indicator pill
│   │   ├── hooks/
│   │   │   └── useAgentWebSocket.ts  # WebSocket auto-reconnect hook
│   │   ├── services/
│   │   │   └── api.ts                # REST API client
│   │   ├── types/
│   │   │   └── events.ts             # TypeScript definitions
│   │   ├── App.tsx                   # Main interface shell
│   │   ├── main.tsx
│   │   └── index.css                 # Glassmorphic CSS design system
│   ├── package.json
│   ├── vite.config.ts
│   └── Dockerfile
├── migrations/                       # Alembic schema migrations
├── docker-compose.yml                # 5-service container orchestrator
├── .env.example                      # Documented configuration template
├── EVALUATION.md                     # Deep system design & evaluation
└── ARCHITECTURE.md                   # Complete architectural spec
```

---

## 🚀 Quickstart with Docker Compose

Ensure Docker and Docker Compose are installed, then run:

```bash
# 1. Clone the repository and enter the directory
git clone https://github.com/rakeshchinni77/multi-agent-orchestration.git
cd multi-agent-orchestration

# 2. Configure environment variables
cp .env.example .env
# Edit .env and supply your API keys (GROQ_API_KEY, BRAVE_SEARCH_API_KEY, OPENWEATHER_API_KEY)

# 3. Spin up all 5 containers
docker compose up --build
```

### Access Points:
- **React Frontend:** [http://localhost:3000](http://localhost:3000)
- **FastAPI Backend:** [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **API Health Check:** [http://localhost:8000/health](http://localhost:8000/health)

---

## 💻 Local Development Setup (Outside Docker)

### Backend:
```bash
cd backend
python -m venv .venv

# On Linux/macOS:
source .venv/bin/activate
# On Windows PowerShell:
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Celery Worker:
```bash
# Ensure Redis is running on port 6379
celery -A app.worker.celery_app.celery_app worker --loglevel=info
```

### Frontend:
```bash
cd frontend
npm install
npm run dev
```

---

## 🛠️ API Reference

### 1. Initiate Workflow
```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is the current weather in Tokyo, and based on that, what should I pack?"}'
```
**Response:**
```json
{
  "task_id": "7f8b9c2a-11e4-4d89-9134-8c73d9e03d42",
  "status": "PENDING",
  "message": "Task registered successfully; multi-agent execution running in background."
}
```

### 2. Stream Live Agent Telemetry via WebSocket
Connect using any WebSocket client or wscat:
```bash
wscat -c ws://localhost:8000/api/ws/7f8b9c2a-11e4-4d89-9134-8c73d9e03d42
```
**Sample Event Stream:**
```json
{"task_id": "...", "agent": "Planner", "event_type": "AGENT_STARTED", "payload": {"message": "Formulating execution plan..."}}
{"task_id": "...", "agent": "Planner", "event_type": "PLAN_CREATED", "payload": {"steps": ["Query weather in Tokyo.", "Synthesize packing list."]}}
{"task_id": "...", "agent": "Researcher", "event_type": "TOOL_INVOCATION", "payload": {"tool": "weather", "arguments": {"location": "Tokyo", "units": "metric"}}}
{"task_id": "...", "agent": "Weather Tool", "event_type": "TOOL_RESULT", "payload": {"tool": "weather", "success": true, "data": {"temperature": "21°C", "condition": "Partly Cloudy"}}}
{"task_id": "...", "agent": "Synthesizer", "event_type": "FINAL_RESULT", "payload": {"final_result": "# Packing Recommendations..."}}
{"task_id": "...", "agent": "System", "event_type": "TASK_COMPLETED", "payload": {"message": "Multi-agent workflow executed successfully."}}
```

---

## 🧪 Automated Testing

Run the comprehensive pytest suite covering API health, task persistence, custom tools, agents, and WebSocket streaming:

```bash
cd backend
pytest -v
```

---

## 🛡️ Custom Tools Overview

| Tool | Provider | Purpose | Safety Mechanism |
| :--- | :--- | :--- | :--- |
| `weather` | OpenWeatherMap | Real-time global weather conditions | Catches 404/401/timeouts, provides graceful fallbacks |
| `web_search` | Brave Search | Live web research & fact retrieval | Parameter validation, rate-limit backoff handling |
| `calculator` | Safe AST Sandbox | Mathematical computations & conversions | **No `eval()`**. Parses AST nodes with division-by-zero handling |

---

## 📄 License
This project is open-source under the [MIT License](LICENSE).
