"""The business tool is checked against independently hand-computed expectations."""

from copy import deepcopy
from pathlib import Path

import pytest
from slimconfig import build_output, plain_output

from contract import RecheckInput
from plugin.planner import compute_recheck_plan
from tests.cases import CASES


@pytest.mark.parametrize("case", CASES, ids=[case["label"] for case in CASES])
def test_tool_matches_hand_computed_case(case, tmp_path: Path):
    given = build_output(case["arguments"], RecheckInput)
    assert plain_output(compute_recheck_plan(given, tmp_path)) == case["expected"]


def node(name="a", dependencies=None, fields=None, cached=True):
    return {"id": name, "dependencies": dependencies or [], "input_fields": fields or [], "cached": cached}


INVALID = [
    {"nodes": [node(), node()], "changed_fields": []},
    {"nodes": [node("")], "changed_fields": []},
    {"nodes": [node(" padded")], "changed_fields": []},
    {"nodes": [node(dependencies=["missing"])], "changed_fields": []},
    {"nodes": [node(dependencies=["a"])], "changed_fields": []},
    {"nodes": [node("a", ["b"]), node("b", ["a"])], "changed_fields": []},
    {"nodes": [node("a"), node("b", ["a", "a"])], "changed_fields": []},
    {"nodes": [node(fields=["x", "x"])], "changed_fields": []},
    {"nodes": [node(fields=[""])], "changed_fields": []},
    {"nodes": [node()], "changed_fields": ["x", "x"]},
    {"nodes": [node()], "changed_fields": [""]},
    {"nodes": [node("x" * 129)], "changed_fields": []},
    {"nodes": [node(str(i)) for i in range(201)], "changed_fields": []},
    {"nodes": [], "changed_fields": [str(i) for i in range(1001)]},
    {"nodes": [node(fields=[str(i) for i in range(1001)])], "changed_fields": []},
]


@pytest.mark.parametrize("arguments", INVALID)
def test_tool_raises_for_invalid_graphs(arguments, tmp_path: Path):
    with pytest.raises(ValueError):
        compute_recheck_plan(build_output(arguments, RecheckInput), tmp_path)


def test_tool_has_no_input_mutation_or_filesystem_side_effects(tmp_path: Path):
    raw = deepcopy(CASES[0]["arguments"])
    given = build_output(raw, RecheckInput)
    before = plain_output(given)
    first = compute_recheck_plan(given, tmp_path)
    assert plain_output(given) == before
    assert compute_recheck_plan(given, tmp_path) == first
    assert list(tmp_path.iterdir()) == []


def test_large_supported_chain_propagates_to_last_node(tmp_path: Path):
    raw = {
        "nodes": [node(str(i), [str(i - 1)] if i else [], ["x"] if not i else []) for i in range(200)],
        "changed_fields": ["x"],
    }
    made = compute_recheck_plan(build_output(raw, RecheckInput), tmp_path)
    assert made.execution_order == [str(i) for i in range(200)]
    assert set(made.rerun_ids) == {str(i) for i in range(200)}
    assert made.reused_ids == []


def test_only_downstream_change_preserves_cached_ancestors(tmp_path: Path):
    raw = {"nodes": [node("a"), node("b", ["a"], ["x"])], "changed_fields": ["x"]}
    made = compute_recheck_plan(build_output(raw, RecheckInput), tmp_path)
    assert made.rerun_ids == ["b"] and made.reused_ids == ["a"]


def test_both_isolated_uncached_nodes_rerun(tmp_path: Path):
    raw = {"nodes": [node("a", cached=False), node("b", cached=False)], "changed_fields": []}
    made = compute_recheck_plan(build_output(raw, RecheckInput), tmp_path)
    assert made.rerun_ids == ["a", "b"] and made.execution_order == ["a", "b"]
