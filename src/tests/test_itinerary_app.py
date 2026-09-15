"""Exercise the A3 UI through Streamlit's actual session and render tree."""

from pathlib import Path
import sys
from unittest.mock import patch

import pytest
from streamlit.testing.v1 import AppTest

SRC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SRC))

from agent import PlanRun, StepResult, ToolCallRecord
from planner import Step


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setenv("LLM_MODE", "replay")
    monkeypatch.setenv("TOOLS_MODE", "replay")
    return AppTest.from_file(str(SRC / "itinerary_app.py"), default_timeout=20)


@pytest.mark.parametrize("status", ["done", "error", "skipped"])
def test_trace_preserves_order_and_escapes_external_content(app, status):
    unsafe = '<script>alert("web content")</script>'
    steps = [Step(n=1, goal=unsafe, tool_hint="web_search"),
             Step(n=2, goal="Write the answer", tool_hint="none")]
    run = PlanRun(
        goal="Example", initial_plan=steps, final_plan=steps,
        step_results=[
            StepResult(step=steps[0], status=status, text=unsafe,
                       observation="surprise: " + unsafe,
                       tool_calls=[ToolCallRecord(
                           name="web_search", arguments={"query": unsafe}, result=unsafe)]),
            StepResult(step=steps[1], status="done", text="Final summary", observation="ok"),
        ],
        revisions=[
            {"after_step": 1, "trigger": unsafe,
             "before": [Step(n=2, goal="Old " + unsafe, tool_hint="fetch_url").to_dict()],
             "after": [steps[1].to_dict()]},
            {"after_step": 2, "trigger": "No further work", "before": [], "after": []},
        ],
        final_answer="Final summary",
    )
    app.session_state["history"] = [(run.goal, run)]
    app.run()
    assert not app.exception
    html = "\n".join(element.value for element in app.markdown)
    assert html.index("step 1") < html.index("Plan revised after step 1") < html.index("step 2")
    assert html.index("step 2") < html.index("Plan revised after step 2")
    assert f"class='status'>{status}</span>" in html
    assert 'observation: surprise:' in html
    assert "web_search" in html and "query" in html
    assert "Old &lt;script&gt;" in html
    assert "Before: remaining steps" in html and "After: remaining steps" in html
    assert unsafe not in html
    assert "&lt;script&gt;" in html
    assert [element.label for element in app.expander] == [
        "Step 1 details", "Plan changes after step 1",
        "Step 2 details", "Plan changes after step 2",
    ]
    captions = [element.value for element in app.caption]
    assert "No tool calls in this step." in captions
    assert "No remaining steps." in captions


def test_empty_run_is_readable(app):
    run = PlanRun(goal="Cancelled", initial_plan=[], final_plan=[], stopped_reason="rejected")
    app.session_state["history"] = [(run.goal, run)]
    app.run()
    assert not app.exception
    captions = [element.value for element in app.caption]
    assert "No steps were executed." in captions
    assert "No plan revisions." in captions
    assert not app.expander


def test_approval_executes_plan_and_keeps_trace_in_history(app):
    app.run()
    with patch("agent.execute_step") as execute:
        app.chat_input[0].set_value("Plan an evening of database study.").run()
        assert not app.exception
        assert app.session_state["pending_plan"] is not None
        assert not app.session_state["history"]
        execute.assert_not_called()

    next(button for button in app.button if button.label == "Approve and run").click().run()
    assert not app.exception
    assert app.session_state["pending_plan"] is None
    history = app.session_state["history"]
    assert len(history) == 1
    run = history[0][1]
    assert run.step_results
    assert len([element for element in app.expander if element.label.endswith("details")]) == len(run.step_results)
    html = "\n".join(element.value for element in app.markdown)
    assert "Final answer" in html
    assert "TODO A3" not in html
    app.run()
    assert not app.exception
    assert len(app.session_state["history"]) == 1
    assert len([element for element in app.expander if element.label.endswith("details")]) == len(run.step_results)
