# PolicyCheck Recheck Planner

An original, offline COMP 480/580 task for computing the **smallest safe set of
checks to rerun** after source inputs change or cached results disappear. This
plugin provides one task in model-routed and deterministic local forms; it does
not claim that a live model or RUSH Lab run has occurred merely because local
tests succeed.

## Tools

- `compute_recheck_plan`: takes `RecheckInput` and returns `RecheckOutput`. The
  tool computes business values in code using Kahn's topological algorithm and
  a forward invalidation closure. It performs no network requests or file writes.
- `plan-rechecks`: the main `agent` task. A model calls the tool with the unchanged
  structured input and submits its output; a pure program checks the submission.
- `plan-rechecks-local`: the same task with `runner: tool`, suitable for offline
  integration checks without a model or API key.

Input `nodes` contain `id`, `dependencies`, `input_fields`, and `cached`.
`changed_fields` lists the names of external inputs changed since cache creation.
The whole graph is supplied in the task input; there are no hidden files or
mutable external services. IDs and field names are case-sensitive strings,
nonempty, at most 128 characters, and have no surrounding whitespace. Lists must
have distinct names. Dependencies must name known nodes, with no self dependency
or cycle. Limits are 200 nodes, 200 dependencies per node, 1000 direct input
fields per node, and 1000 changed fields. Empty graphs, isolated nodes, and changed
fields that no node reads are valid.

The required rerun set starts with every uncached node and every node directly
reading a changed field. It then includes **all descendants** of those nodes.
Every remaining node must be reused. A downstream-only change does not invalidate
cached ancestors. Output `rerun_ids` and `reused_ids` are sets represented by
lists, whose order is irrelevant. `execution_order` must contain exactly the rerun
nodes once each and respect all dependencies between rerun nodes. Already cached,
unaffected dependencies are available before execution begins. Multiple legal
topological orders are accepted.

For example, `amount -> balance -> report` with all three cached, `balance`
reading `payments`, and only `payments` changed must rerun `balance, report` in
that order and reuse `amount`. An uncached `amount` instead invalidates all three.
An independent cached node can always be reused unless it directly reads a
changed field.

The verifier independently reconstructs the least invalidation fixed point and
checks the submitted order against dependency sets. It does not import the tool,
use a reference answer supplied by the model, or call an LLM. Contract construction
rejects missing and malformed values; semantic checks reject duplicate IDs,
invalid graphs, missing descendants, excessive reruns, false reuse, and bad order.
This proves correctness relative to the explicit graph only: identifying the
real dependencies, detecting undeclared input changes, fingerprinting source
files, and actually executing downstream jobs are outside the task.

## Layout

- `contract.py`: typed input/output dataclasses and the tool/task enums.
- `nanoagent.yaml`: spec v0001 manifest with identical task contracts.
- `src/plugin/planner.py`: deterministic graph tool.
- `src/plugin/__main__.py`: MCP stdio tool registration.
- `verifier/`: pure, independent fixed-point verifier and dispatch.
- `tests/`: hand-computed fixtures plus tool and verifier tests, including wrong,
  missing, malformed, boundary, and equivalent-order cases.
- `product/` and `ui/`: product description, original SVG, and schema renderer.

## Develop and run

Requires Git, Python 3.12 or later, and uv. No environment variables or API keys
are needed for the local task. The `.env` file is intentionally empty. Runtime
dependencies and the exact slimconfig Git revision are pinned by `uv.lock`.
From a fresh checkout:

```sh
uv sync --extra dev --frozen
uv run pytest
uv run ruff check .
uv lock --check
```

A minimal business-tool call (the framework normally supplies the workspace):

```sh
uv run python -c 'from pathlib import Path; from contract import RecheckInput; from plugin import compute_recheck_plan; print(compute_recheck_plan(RecheckInput(nodes=[], changed_fields=[]), Path(".")))'
```

Use NanoAgent/RUSH Lab to invoke `plan-rechecks-local` with the hand-computed task
inputs in `tests/cases.py`. The `plan-rechecks` task additionally requires the
host's configured model. Run inputs, actual validation logs and verdicts belong
in the separate milestone report, not this repository. Unit tests alone do not
establish publication, a live agent run, or execution on the course platform.
