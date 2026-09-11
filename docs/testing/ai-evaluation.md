# AI Evaluation Test Implementation — Paraxis AI

> **Purpose**: Automated evaluation runners, benchmark dataset formats, and CI regression testing for AI components.

---

## 1. Evaluation Runner (`tests/evaluation/eval_runner.py`)

The evaluation runner compares agent outputs against labeled gold-standard datasets:
- **Input**: `dataset.json` containing 100+ prompt variations (spelling mistakes, slang, emergency phrasing).
- **Assertions**:
  - `category_accuracy >= 0.95`
  - `entity_recall >= 0.95`
  - `duplicate_detection_f1 >= 0.92`
  - `policy_compliance == 1.0` (Zero unauthorized dispatches)

---

## 2. CI Regression Gate

In GitHub Actions CI:
- The evaluation suite runs against `MockModelAdapter` to ensure zero regressions in graph transitions and deterministic policy logic on every commit.
- Before deployment or major release, a manual dispatch workflow runs against live model endpoints with temperature 0.0 to verify model prompt stability.
