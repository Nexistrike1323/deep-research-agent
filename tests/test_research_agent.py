from src.agent import build_research_graph

def test_checkpoint_pause_and_resume(tmp_path):
    db_file = str(tmp_path / "test_state.sqlite")
    app = build_research_graph(db_path=db_file)
    cfg = {"configurable": {"thread_id": "test-thread-1"}}

    s1 = app.invoke({"topic": "Distributed RAG"}, config=cfg)
    assert s1["completed_index"] == 1
    assert s1.get("final_report") is None

    s2 = app.invoke(None, config=cfg)
    assert s2["completed_index"] == 2

    s3 = app.invoke(None, config=cfg)
    assert "Deep Research Report: Distributed RAG" in s3["final_report"]
