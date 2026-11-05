"""Compute minimal invalidation with Kahn's algorithm and a forward closure."""

from collections import deque
from pathlib import Path

from contract import RecheckInput, RecheckOutput


def _name(value: str) -> bool:
    return bool(value) and value == value.strip() and len(value) <= 128


def compute_recheck_plan(value: RecheckInput, workspace: Path) -> RecheckOutput:
    """Return the unique minimal node sets and one deterministic topological order.

    The workspace argument is the standard plugin interface; this pure tool writes
    no files. Cached ancestors may be reused when only a downstream node changes.
    """
    if len(value.nodes) > 200 or len(value.changed_fields) > 1000:
        raise ValueError("at most 200 nodes and 1000 changed fields are supported")
    ids = [node.id for node in value.nodes]
    if any(not _name(item) for item in ids) or len(set(ids)) != len(ids):
        raise ValueError("node IDs must be unique nonempty names of at most 128 characters")
    if any(not _name(item) for item in value.changed_fields):
        raise ValueError("changed fields must be nonempty names of at most 128 characters")
    if len(set(value.changed_fields)) != len(value.changed_fields):
        raise ValueError("changed fields must not contain duplicates")
    node_ids = set(ids)
    children = {item: [] for item in ids}
    indegree = {}
    for node in value.nodes:
        if len(node.dependencies) > 200 or len(node.input_fields) > 1000:
            raise ValueError("a node supports at most 200 dependencies and 1000 input fields")
        if len(set(node.dependencies)) != len(node.dependencies):
            raise ValueError("dependencies must not contain duplicates")
        if any(item not in node_ids for item in node.dependencies):
            raise ValueError("every dependency must name a known node")
        if node.id in node.dependencies:
            raise ValueError("a node cannot depend on itself")
        if any(not _name(item) for item in node.input_fields):
            raise ValueError("input fields must be nonempty names of at most 128 characters")
        if len(set(node.input_fields)) != len(node.input_fields):
            raise ValueError("input fields must not contain duplicates")
        indegree[node.id] = len(node.dependencies)
        for dependency in node.dependencies:
            children[dependency].append(node.id)
    queue = deque(sorted(item for item in ids if indegree[item] == 0))
    ordered = []
    while queue:
        item = queue.popleft()
        ordered.append(item)
        for child in sorted(children[item]):
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)
    if len(ordered) != len(ids):
        raise ValueError("dependency graph must be acyclic")
    changed = set(value.changed_fields)
    affected = {node.id for node in value.nodes if not node.cached or changed.intersection(node.input_fields)}
    queue = deque(sorted(affected))
    while queue:
        for child in children[queue.popleft()]:
            if child not in affected:
                affected.add(child)
                queue.append(child)
    return RecheckOutput(
        rerun_ids=sorted(affected),
        reused_ids=sorted(node_ids - affected),
        execution_order=[item for item in ordered if item in affected],
    )
