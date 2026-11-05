"""Sandbox-style typed values plus independent negative and boundary checks."""

from copy import deepcopy

import pytest
from slimconfig import build_output, plain_output

import verifier
from contract import RecheckInput, RecheckOutput
from tests.cases import CASES
from tests.test_planner import INVALID, node


def typed_arguments(raw):
    return build_output(plain_output(build_output(raw, RecheckInput)), RecheckInput)


def typed_output(raw):
    return build_output(plain_output(build_output(raw, RecheckOutput)), RecheckOutput)


@pytest.mark.parametrize("case", CASES, ids=[case["label"] for case in CASES])
def test_hand_calculated_results_pass_both_tasks_and_tool(case):
    given = typed_arguments(case["arguments"])
    made = typed_output(case["expected"])
    assert verifier.verify_input("compute_recheck_plan", given)["valid"] is True
    assert verifier.verify_output("compute_recheck_plan", given, made, ".")["valid"] is True
    for task in ["plan-rechecks", "plan-rechecks-local"]:
        first = verifier.verify_task(task, given, made, None, ".")
        second = verifier.verify_task(task, given, made, None, ".")
        assert first["valid"] is True and first == second
        assert first["score"] == 1.0


@pytest.mark.parametrize("arguments", INVALID)
def test_invalid_graph_is_refused_before_and_during_verification(arguments):
    given = typed_arguments(arguments)
    made = typed_output({"rerun_ids": [], "reused_ids": [], "execution_order": []})
    assert verifier.verify_input("compute_recheck_plan", given)["valid"] is False
    assert verifier.verify_task("plan-rechecks", given, made, None, ".")["valid"] is False


WRONG_PLANS = [
    {"rerun_ids": [], "reused_ids": ["amount", "balance", "report"], "execution_order": []},
    {"rerun_ids": ["balance"], "reused_ids": ["amount", "report"], "execution_order": ["balance"]},
    {"rerun_ids": ["amount", "balance", "report"], "reused_ids": [], "execution_order": ["amount", "balance", "report"]},
    {"rerun_ids": ["balance", "report", "fake"], "reused_ids": ["amount"], "execution_order": ["balance", "report"]},
    {"rerun_ids": ["balance", "report"], "reused_ids": [], "execution_order": ["balance", "report"]},
    {"rerun_ids": ["balance", "report"], "reused_ids": ["amount", "balance"], "execution_order": ["balance", "report"]},
    {"rerun_ids": ["balance", "report"], "reused_ids": ["amount"], "execution_order": ["report", "balance"]},
    {"rerun_ids": ["balance", "report"], "reused_ids": ["amount"], "execution_order": ["balance"]},
    {"rerun_ids": ["balance", "report"], "reused_ids": ["amount"], "execution_order": ["balance", "report", "fake"]},
    {"rerun_ids": ["balance", "balance", "report"], "reused_ids": ["amount"], "execution_order": ["balance", "report"]},
    {"rerun_ids": ["balance", "report"], "reused_ids": ["amount", "amount"], "execution_order": ["balance", "report"]},
    {"rerun_ids": ["balance", "report"], "reused_ids": ["amount"], "execution_order": ["balance", "report", "report"]},
]


@pytest.mark.parametrize("raw_output", WRONG_PLANS)
def test_rejects_incorrect_incomplete_excessive_and_duplicate_plans(raw_output):
    given = typed_arguments(CASES[0]["arguments"])
    made = typed_output(raw_output)
    tool = verifier.verify_output("compute_recheck_plan", given, made, ".")
    assert tool["valid"] is False and tool["score"] == 0.0
    assert verifier.verify_task("plan-rechecks", given, made, None, ".")["valid"] is False


def test_accepts_equivalent_topological_order_and_unordered_sets():
    case = CASES[1]
    made = deepcopy(case["expected"])
    made["rerun_ids"] = ["right", "source", "join", "left"]
    made["execution_order"] = ["source", "right", "left", "join"]
    assert verifier.verify_task(
        "plan-rechecks", typed_arguments(case["arguments"]), typed_output(made), None, "."
    )["valid"] is True


def test_rejects_topology_that_violates_one_diamond_parent():
    case = CASES[1]
    made = deepcopy(case["expected"])
    made["execution_order"] = ["source", "left", "join", "right"]
    assert verifier.verify_task(
        "plan-rechecks", typed_arguments(case["arguments"]), typed_output(made), None, "."
    )["valid"] is False


@pytest.mark.parametrize("raw", [
    {},
    {"rerun_ids": [], "reused_ids": []},
    {"rerun_ids": None, "reused_ids": [], "execution_order": []},
    {"rerun_ids": "a", "reused_ids": [], "execution_order": []},
    {"rerun_ids": [True], "reused_ids": [], "execution_order": []},
    {"rerun_ids": [3], "reused_ids": [], "execution_order": []},
    {"rerun_ids": [], "reused_ids": [], "execution_order": True},
])
def test_missing_or_malformed_outputs_fail_contract_build(raw):
    with pytest.raises(ValueError):
        build_output(raw, RecheckOutput)


@pytest.mark.parametrize("raw", [
    {},
    {"nodes": [], "changed_fields": None},
    {"nodes": [node() | {"cached": 1}], "changed_fields": []},
    {"nodes": [node() | {"cached": "true"}], "changed_fields": []},
    {"nodes": [node() | {"dependencies": "a"}], "changed_fields": []},
    {"nodes": [node() | {"id": 1}], "changed_fields": []},
])
def test_missing_or_malformed_inputs_fail_contract_build(raw):
    with pytest.raises(ValueError):
        build_output(raw, RecheckInput)


def test_unknown_changed_field_is_valid_and_has_no_effect():
    arguments = {"nodes": [node()], "changed_fields": ["not-read-by-any-node"]}
    made = {"rerun_ids": [], "reused_ids": ["a"], "execution_order": []}
    assert verifier.verify_task(
        "plan-rechecks", typed_arguments(arguments), typed_output(made), None, "."
    )["valid"] is True


def test_isolated_nodes_allow_either_execution_order():
    arguments = {"nodes": [node("a", cached=False), node("b", cached=False)], "changed_fields": []}
    made = {"rerun_ids": ["b", "a"], "reused_ids": [], "execution_order": ["b", "a"]}
    assert verifier.verify_task(
        "plan-rechecks-local", typed_arguments(arguments), typed_output(made), None, "."
    )["valid"] is True
