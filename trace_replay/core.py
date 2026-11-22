from __future__ import annotations

from dataclasses import dataclass
from typing import Any

DEFAULT_IGNORED_KEYS = frozenset({"timestamp", "elapsed_ms", "request_id", "trace_timestamp"})


@dataclass(frozen=True)
class ReplayReport:
    missing_ids: tuple[str, ...]
    unexpected_ids: tuple[str, ...]
    differences: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return not (self.missing_ids or self.unexpected_ids or self.differences)


def normalize(value: Any, ignored_keys: frozenset[str] = DEFAULT_IGNORED_KEYS) -> Any:
    """Return a JSON-compatible value with volatile dictionary keys removed."""
    if isinstance(value, dict):
        return {
            key: normalize(item, ignored_keys)
            for key, item in sorted(value.items())
            if key not in ignored_keys
        }
    if isinstance(value, list):
        return [normalize(item, ignored_keys) for item in value]
    return value


def diff_values(expected: Any, actual: Any, path: str = "$") -> list[str]:
    """List stable leaf-level mismatches using JSONPath-like locations."""
    if isinstance(expected, dict) and isinstance(actual, dict):
        result: list[str] = []
        for key in sorted(expected.keys() | actual.keys()):
            child = f"{path}.{key}"
            if key not in expected:
                result.append(f"{child}: unexpected {actual[key]!r}")
            elif key not in actual:
                result.append(f"{child}: missing (expected {expected[key]!r})")
            else:
                result.extend(diff_values(expected[key], actual[key], child))
        return result
    if isinstance(expected, list) and isinstance(actual, list):
        result = []
        for index in range(max(len(expected), len(actual))):
            child = f"{path}[{index}]"
            if index >= len(expected):
                result.append(f"{child}: unexpected {actual[index]!r}")
            elif index >= len(actual):
                result.append(f"{child}: missing (expected {expected[index]!r})")
            else:
                result.extend(diff_values(expected[index], actual[index], child))
        return result
    if type(expected) is not type(actual) or expected != actual:
        return [f"{path}: expected {expected!r}, got {actual!r}"]
    return []


def _index(traces: list[dict[str, Any]], label: str) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for trace in traces:
        trace_id = trace.get("trace_id")
        if not isinstance(trace_id, str) or not trace_id.strip():
            raise ValueError(f"{label} trace is missing a non-empty trace_id")
        if trace_id in indexed:
            raise ValueError(f"duplicate {label} trace_id: {trace_id}")
        indexed[trace_id] = trace
    return indexed


def compare_traces(
    expected: list[dict[str, Any]],
    actual: list[dict[str, Any]],
    ignored_keys: frozenset[str] = DEFAULT_IGNORED_KEYS,
) -> ReplayReport:
    """Compare trace sets by ID; trace list order is irrelevant, nested list order is not."""
    left = _index(expected, "expected")
    right = _index(actual, "actual")
    missing = tuple(sorted(left.keys() - right.keys()))
    unexpected = tuple(sorted(right.keys() - left.keys()))
    differences: list[str] = []
    for trace_id in sorted(left.keys() & right.keys()):
        differences.extend(
            f"{trace_id}{message[1:]}"
            for message in diff_values(
                normalize(left[trace_id], ignored_keys),
                normalize(right[trace_id], ignored_keys),
            )
        )
    return ReplayReport(missing, unexpected, tuple(differences))
