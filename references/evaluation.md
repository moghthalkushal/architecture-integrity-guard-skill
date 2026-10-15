# Adversarial evaluation and ROI

Before rollout, record a baseline across 10–20 representative agent changes: violations per change, duplicate business implementations introduced, corrective refactoring changes/effort, and (if available) coding-agent tokens spent on architecture rework. Avoid promising an unsupported percentage improvement.

Adversarial cases:

1. Add a new endpoint whose business behavior is already implemented elsewhere. Expected: reuse canonical code, no sibling transform.
2. Import canonical implementation for an unrelated helper but execute local TransformB. Expected: reachability-only check is insufficient; runtime instrumentation or forbidden primitives catches bypass.
3. Introduce an entirely new endpoint under a configured discovery glob. Expected: registry mismatch fails.
4. Call raw mappers/rules from a new Python module. Expected: Python AST guard fails.
5. Duplicate rules under new names without direct imports. Expected: semantic code review or golden behavior tests are needed; admit static blind spot.
6. Have agent modify guardrail config/tests. Expected: protected branch/owner review (hook prompts alone are not security).
7. Legitimately different business capability. Expected: avoid false duplication report with recorded contract and owner approval.
8. Dynamic route/import not matched by globs or AST. Expected: report `NOT VERIFIED`; add framework-specific enumerator and instrumentation.

Run agent with and without the skill over comparable tasks, using the same independent benchmark assertions. Measure both missed violations and false positives, the number of spawned model reviewers, and net tokens consumed. Introduce an optional semantic analyzer only after deterministic blind spots are measured.
