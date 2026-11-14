# Multi-Session Deep Research & Synthesis Agent

**Stack:** `Python 3.10+` · `LangGraph` · `SQLite Checkpointer` · `DuckDuckGo Search` · `agent-guardrails-lite`

A long-running autonomous research agent engineered for crash-resilient state persistence, human-in-the-loop pause/resume workflows, and three-tier hierarchical memory management.

---

## Why This Matters

Long-running research and synthesis workflows often fail in production because:
- Network timeouts or rate limits wipe out progress halfway through a multi-step query.
- Accumulating raw web search results overflows the LLM context window and degrades reasoning.
- Agents repeat identical search queries when external sources return sparse results.

This system solves all three challenges using **persistent database checkpointing**, **bounded rolling working memory**, and **deterministic tool guardrails**.

---

## Memory & State Architecture

```text
  [Research Topic]
         │
         ▼
 ┌───────────────┐
 │ 1. Plan Node  │ ──► Decomposes topic into structured sub-questions
 └───────┬───────┘
         │
         ▼  (Persists state to SQLite after every step via thread_id)
 ┌───────────────┐     Protected by: agent-guardrails-lite
 │ 2. Step Node  │ ──► • Working Memory (rolling window of last 4 hits)
 │  (Web Search) │     • Episodic Scratchpad (accumulated markdown notes)
 └───────┬───────┘     • Interrupt / Resume checkpoint boundary
         │
         ▼
 ┌───────────────┐
 │ 3. Synthesize │ ──► Compiles final cited report to reports/latest_report.md
 └───────────────┘
```

---

## Key Capabilities

- **Crash-Resilient Checkpointing (`SqliteSaver`):** Every node transition serializes graph state, step counters, and `thread_id` metadata to SQLite (`research_checkpoints.sqlite`), allowing interrupted sessions to resume without repeating completed web searches.
- **Three-Tier Memory Hierarchy:** Separates short-term **Working Memory** (rolling window), **Episodic State** (structured sub-question findings), and **Persistent Outputs** (finalized markdown reports).
- **Runtime Guardrails (`agent-guardrails-lite`):** Validates search arguments via Pydantic schemas and blocks duplicate search queries across sessions.

---

## Quickstart

### 1. Set Up Environment
```bash
git clone https://github.com
cd deep-research-agent
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run Multi-Session Pause & Resume Demo
```bash
python -m src.agent
```

### 3. Run Automated Test Suite
```bash
python -m pytest -v
```

---

## Related Portfolio Projects
- **[agent-guardrails-lite](https://github.com):** Open-source Python reliability middleware protecting tool-calling loops.
- **[log-triage-agent](https://github.com):** Autonomous DevOps agent for CI/CD root-cause analysis.
