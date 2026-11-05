"""Verifier dispatch for both the model-routed and deterministic local task."""

from contract import Task, Tool

from . import planner

TOOLS = {Tool.COMPUTE_RECHECK_PLAN: planner}
TASKS = {
    Task.PLAN_RECHECKS: planner.verify_task,
    Task.PLAN_RECHECKS_LOCAL: planner.verify_task,
}


def verify_input(tool, value):
    return TOOLS[Tool(tool)].verify_input(value)


def verify_output(tool, input_value, output_value, workspace):
    return TOOLS[Tool(tool)].verify_output(input_value, output_value, workspace)


def verify_task(task, arguments, output, reference, workspace):
    return TASKS[Task(task)](arguments, output, reference, workspace)
