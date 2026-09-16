from app.orchestrator import AgenticOrchestrator, Status


def test_dependency_graph_and_release_gate():
    workflow = AgenticOrchestrator("greenfield")
    result = workflow.run()

    assert result["scenario"] == "greenfield"

    assert result["tasks"]["architecture"]["deps"] == ["requirements"]
    assert result["tasks"]["implementation"]["deps"] == ["architecture"]

    assert result["tasks"]["tests"]["deps"] == ["implementation"]
    assert result["tasks"]["security"]["deps"] == ["implementation"]

    assert result["tasks"]["validation"]["deps"] == [
        "tests",
        "security",
    ]

    assert result["tasks"]["release"]["status"] == "approval"

    assert any(
        event["event"] == "approval_required"
        for event in result["audit"]
    )


def test_parallel_validation_branches():
    workflow = AgenticOrchestrator("greenfield")
    result = workflow.run()

    events = [event["event"] for event in result["audit"]]

    assert "parallel_branch_started" in events
    assert "parallel_branch_synchronized" in events

    assert result["tasks"]["tests"]["status"] == "passed"
    assert result["tasks"]["security"]["status"] == "passed"
    assert result["tasks"]["validation"]["status"] == "passed"


def test_human_release_approval():
    workflow = AgenticOrchestrator("greenfield")

    result = workflow.run()

    assert result["tasks"]["release"]["status"] == "approval"

    approved = workflow.approve_release()

    assert approved is True
    assert workflow.tasks["release"].status == Status.PASSED
    assert workflow.tasks["release"].output["approved_by"] == "human"

    final = workflow.snapshot()

    assert final["state"] == "COMPLETED"


def test_brownfield_requires_regression_testing():
    workflow = AgenticOrchestrator("brownfield")
    result = workflow.run()

    assert result["scenario"] == "brownfield"

    requirements = result["tasks"]["requirements"]["output"]
    architecture = result["tasks"]["architecture"]["output"]
    tests = result["tasks"]["tests"]["output"]

    assert requirements["change_type"] == "enhancement"
    assert "preserve backward compatibility" in requirements["analysis"]

    assert architecture["mode"] == "brownfield"
    assert architecture["risk"] == "backward compatibility"

    assert tests["regression_required"] is True


def test_ambiguous_requirements_stop_workflow():
    workflow = AgenticOrchestrator("ambiguous")
    result = workflow.run()

    assert result["scenario"] == "ambiguous"
    assert result["state"] == "AWAITING_HUMAN_APPROVAL"

    assert result["tasks"]["requirements"]["status"] == "approval"

    assert result["tasks"]["architecture"]["status"] == "pending"
    assert result["tasks"]["implementation"]["status"] == "pending"
    assert result["tasks"]["tests"]["status"] == "pending"
    assert result["tasks"]["security"]["status"] == "pending"

    questions = result["tasks"]["requirements"]["output"]["questions"]

    assert len(questions) == 3
    assert "What scale and SLO are required?" in questions


def test_replanning_for_database_contention():
    workflow = AgenticOrchestrator("greenfield")
    workflow.run()

    result = workflow.replan("database contention detected")

    change = result["context"]["architecture_change"]

    assert change["from"] == "synchronous database writes"
    assert change["to"] == "queue-based click aggregation"

    events = [event["event"] for event in result["audit"]]

    assert "replan_started" in events
    assert "replan_completed" in events