import sqlite3
from pathlib import Path
from typing import TypedDict, List, Dict
from pydantic import BaseModel
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from agent_guardrails import GuardrailSession
from src.tools import web_search_tool


class SearchInput(BaseModel):
    query: str
    max_results: int = 2


class ResearchState(TypedDict):
    topic: str
    sub_questions: List[str]
    completed_index: int
    working_memory: List[Dict[str, str]]
    episodic_notes: List[str]
    final_report: str


guardrails = GuardrailSession(max_steps=12, max_tokens=20000, max_duplicate_calls=2)


def plan_research_node(state: ResearchState) -> ResearchState:
    if state.get("sub_questions"):
        return state
    topic = state["topic"]
    plan = [
        f"{topic} architecture and core components",
        f"{topic} failure modes and production benchmarks",
    ]
    return {
        **state,
        "sub_questions": plan,
        "completed_index": 0,
        "working_memory": [],
        "episodic_notes": [],
    }


def execute_step_node(state: ResearchState) -> ResearchState:
    idx = state["completed_index"]
    sub_q = state["sub_questions"][idx]

    res = guardrails.execute_tool(
        "web_search",
        web_search_tool,
        {"query": sub_q, "max_results": 2},
        schema=SearchInput,
    )
    hits = res.get("output", [])
    summary = f"### Sub-Question {idx + 1}: {sub_q}\n" + "\n".join(
        f"- **{h['title']}** ({h['url']}): {h['snippet']}" for h in hits
    )

    updated_working = (state["working_memory"] + hits)[-4:]
    updated_episodic = state["episodic_notes"] + [summary]

    return {
        **state,
        "completed_index": idx + 1,
        "working_memory": updated_working,
        "episodic_notes": updated_episodic,
    }


def synthesize_report_node(state: ResearchState) -> ResearchState:
    report = (
        f"# Deep Research Report: {state['topic']}\n\n"
        + "\n\n".join(state["episodic_notes"])
        + "\n\n---\n*Synthesized across checkpointed sessions.*"
    )
    Path("reports").mkdir(exist_ok=True)
    Path("reports/latest_report.md").write_text(report, encoding="utf-8")
    return {**state, "final_report": report}


def should_continue(state: ResearchState) -> str:
    if state["completed_index"] < len(state["sub_questions"]):
        return "research_step"
    return "synthesize"


def build_research_graph(db_path: str = "research_checkpoints.sqlite"):
    conn = sqlite3.connect(db_path, check_same_thread=False)
    checkpointer = SqliteSaver(conn)

    workflow = StateGraph(ResearchState)
    workflow.add_node("plan", plan_research_node)
    workflow.add_node("research_step", execute_step_node)
    workflow.add_node("synthesize", synthesize_report_node)

    workflow.set_entry_point("plan")
    workflow.add_edge("plan", "research_step")
    workflow.add_conditional_edges(
        "research_step",
        should_continue,
        {"research_step": "research_step", "synthesize": "synthesize"},
    )
    workflow.add_edge("synthesize", END)
    return workflow.compile(checkpointer=checkpointer, interrupt_after=["research_step"])


if __name__ == "__main__":
    app = build_research_graph()
    config = {"configurable": {"thread_id": "session-alpha-001"}}

    print("=== SESSION 1: Starting Research & Pausing After Step 1 ===")
    state_1 = app.invoke({"topic": "Agentic State Checkpointing"}, config=config)
    print(f"Paused at completed_index = {state_1['completed_index']} / {len(state_1['sub_questions'])}")

    print("\n=== SESSION 2: Resuming From SQLite Checkpoint ===")
    state_2 = app.invoke(None, config=config)
    print(f"Resumed and completed_index = {state_2['completed_index']} / {len(state_2['sub_questions'])}")

    print("\n=== SESSION 3: Final Synthesis ===")
    final_state = app.invoke(None, config=config)
    print(final_state["final_report"])
