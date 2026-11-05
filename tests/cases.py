"""Hand-computed fixtures, shared by tests and the external framework evidence runner."""

CASES = [
    {
        "label": "payment-only-change-reuses-amount",
        "arguments": {
            "nodes": [
                {"id": "amount", "dependencies": [], "input_fields": ["claim", "policy"], "cached": True},
                {"id": "balance", "dependencies": ["amount"], "input_fields": ["payments"], "cached": True},
                {"id": "report", "dependencies": ["balance"], "input_fields": [], "cached": True},
            ],
            "changed_fields": ["payments"],
        },
        "expected": {
            "rerun_ids": ["balance", "report"],
            "reused_ids": ["amount"],
            "execution_order": ["balance", "report"],
        },
    },
    {
        "label": "diamond-ancestor-change",
        "arguments": {
            "nodes": [
                {"id": "source", "dependencies": [], "input_fields": ["policy"], "cached": True},
                {"id": "left", "dependencies": ["source"], "input_fields": [], "cached": True},
                {"id": "right", "dependencies": ["source"], "input_fields": [], "cached": True},
                {"id": "join", "dependencies": ["left", "right"], "input_fields": [], "cached": True},
            ],
            "changed_fields": ["policy"],
        },
        "expected": {
            "rerun_ids": ["join", "left", "right", "source"],
            "reused_ids": [],
            "execution_order": ["source", "left", "right", "join"],
        },
    },
    {
        "label": "missing-cache-propagates-without-input-changes",
        "arguments": {
            "nodes": [
                {"id": "a", "dependencies": [], "input_fields": [], "cached": False},
                {"id": "b", "dependencies": ["a"], "input_fields": [], "cached": True},
                {"id": "unrelated", "dependencies": [], "input_fields": ["other"], "cached": True},
            ],
            "changed_fields": [],
        },
        "expected": {"rerun_ids": ["a", "b"], "reused_ids": ["unrelated"], "execution_order": ["a", "b"]},
    },
    {
        "label": "empty-graph-with-unconsumed-change",
        "arguments": {"nodes": [], "changed_fields": ["unused"]},
        "expected": {"rerun_ids": [], "reused_ids": [], "execution_order": []},
    },
    {
        "label": "unchanged-cached-graph",
        "arguments": {
            "nodes": [
                {"id": "a", "dependencies": [], "input_fields": ["x"], "cached": True},
                {"id": "b", "dependencies": ["a"], "input_fields": ["y"], "cached": True},
            ],
            "changed_fields": [],
        },
        "expected": {"rerun_ids": [], "reused_ids": ["a", "b"], "execution_order": []},
    },
]
