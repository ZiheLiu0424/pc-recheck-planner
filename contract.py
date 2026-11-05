"""Typed task and tool declarations for the minimal recheck planner."""

from dataclasses import dataclass
from enum import Enum
from typing import Annotated

from slimconfig import Output


class Tool(Enum):
    COMPUTE_RECHECK_PLAN = "compute_recheck_plan"


class Task(Enum):
    PLAN_RECHECKS = "plan-rechecks"
    PLAN_RECHECKS_LOCAL = "plan-rechecks-local"


@dataclass
class Node(Output):
    id: Annotated[str, "Unique nonempty node identifier, with no surrounding whitespace"]
    dependencies: Annotated[list[str], "Distinct node IDs whose results this node needs"]
    input_fields: Annotated[list[str], "Distinct external fields read directly by this node"]
    cached: Annotated[bool, "Whether a valid result was cached before this change"]


@dataclass
class RecheckInput(Output):
    nodes: Annotated[list[Node], "The complete acyclic dependency graph, at most 200 nodes"]
    changed_fields: Annotated[list[str], "Distinct names of external fields changed since the cache was built"]


@dataclass
class RecheckOutput(Output):
    rerun_ids: Annotated[list[str], "Exactly the directly invalidated or uncached nodes and all their descendants"]
    reused_ids: Annotated[list[str], "Exactly the unaffected cached nodes"]
    execution_order: Annotated[list[str], "Every rerun node once, after each of its rerun dependencies"]


TOOLS = {Tool.COMPUTE_RECHECK_PLAN: (RecheckInput, RecheckOutput)}
TASKS = {
    Task.PLAN_RECHECKS: (RecheckInput, RecheckOutput),
    Task.PLAN_RECHECKS_LOCAL: (RecheckInput, RecheckOutput),
}
