# LLM Trace Replay Lab

A small, dependency-free toolkit for replaying recorded assistant traces against saved expectations and producing stable, reviewable diffs. It is intended for regression tests of prompt, orchestration, and tool-call changes without contacting a model provider.

## What it does

- Canonicalizes JSON while ignoring explicitly volatile fields such as timestamps and request IDs.
- Compares complete trace objects and reports deterministic JSON-path differences.
- Detects missing, unexpected, and duplicate trace IDs.
- Keeps tool-call ordering and stable response content significant.

```python
from trace_replay import compare_traces

expected = [{"trace_id": "case-1", "output": {"answer": "42"}}]
actual = [{"trace_id": "case-1", "output": {"answer": "42"}}]
report = compare_traces(expected, actual)
assert report.passed
```

Run `python -m unittest discover -s tests -v` and `uvx ruff check .`.

## Scope

The tool compares recorded data; it does not call an LLM, establish semantic equivalence, or prove a trace is safe to replay. Store fixtures with secrets removed and review diffs before release.
