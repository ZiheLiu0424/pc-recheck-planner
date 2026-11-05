"""Independent fixed-point verification; does not import the tool implementation."""

from .checks import result


def name_problem(items):
    if any(not item or item.strip() != item or len(item) > 128 for item in items):
        return "names must be nonempty, at most 128 characters, without surrounding whitespace"
    if len(set(items)) != len(items):
        return "names in one list must be unique"
    return None


def input_problem(value):
    if len(value.nodes) > 200 or len(value.changed_fields) > 1000:
        return "at most 200 nodes and 1000 changed fields are supported"
    ids = [node.id for node in value.nodes]
    problem = name_problem(ids) or name_problem(value.changed_fields)
    if problem:
        return problem
    known = set(ids)
    for node in value.nodes:
        if len(node.dependencies) > 200 or len(node.input_fields) > 1000:
            return "a node supports at most 200 dependencies and 1000 input fields"
        problem = name_problem(node.dependencies) or name_problem(node.input_fields)
        if problem:
            return problem
        if not set(node.dependencies).issubset(known):
            return "a dependency names an unknown node"
        if node.id in node.dependencies:
            return "self dependency is invalid"
    # Fixed-point elimination, independent of the tool's indegree/queue algorithm.
    resolved = set()
    while True:
        expanded = resolved | {node.id for node in value.nodes if set(node.dependencies).issubset(resolved)}
        if expanded == resolved:
            break
        resolved = expanded
    if resolved != known:
        return "dependency graph contains a cycle"
    return None


def verify_input(value):
    problem = input_problem(value)
    return result(not problem, problem or "input is a finite acyclic dependency graph")


def verify_output(input_value, output_value, workspace):
    problem = input_problem(input_value)
    if problem:
        return result(False, problem)
    changed = set(input_value.changed_fields)
    required = {
        node.id for node in input_value.nodes
        if not node.cached or any(field in changed for field in node.input_fields)
    }
    # Least fixed point: add a node if an affected dependency feeds it.
    while True:
        expanded = required | {
            node.id for node in input_value.nodes if any(parent in required for parent in node.dependencies)
        }
        if expanded == required:
            break
        required = expanded
    all_ids = {node.id for node in input_value.nodes}
    reusable = all_ids - required
    for items in [output_value.rerun_ids, output_value.reused_ids, output_value.execution_order]:
        if len(items) != len(set(items)):
            return result(False, "output lists must not contain duplicates")
    if set(output_value.rerun_ids) != required:
        return result(False, "rerun_ids is not the exact minimal invalidation set")
    if set(output_value.reused_ids) != reusable:
        return result(False, "reused_ids is not exactly the unaffected cached set")
    if set(output_value.execution_order) != required:
        return result(False, "execution_order must contain every rerun node exactly once")
    dependencies = {node.id: set(node.dependencies) for node in input_value.nodes}
    completed = set(reusable)
    for item in output_value.execution_order:
        if not dependencies[item].issubset(completed):
            return result(False, "execution_order runs a node before a rerun dependency")
        completed.add(item)
    return result(
        True,
        "plan is minimal, complete, and respects dependency order",
        rerun_count=len(required),
        reused_count=len(reusable),
    )


def verify_task(arguments, output, reference, workspace):
    return verify_output(arguments, output, workspace)
