# Implementation playbook

## A. Minimal architectural contract per capability

Maintain a human-owned record of (1) owner implementation, (2) low-level primitives it alone may access, (3) all applicable consumer entrypoints, (4) consumer discovery rules, (5) golden test set, (6) runtime-path test. Keep the contract brief. Prefer exact source paths and symbols to vague names.

A repo-specific owner might be `src/domain/orders/normalize.py`. A new `orders_v2_normalize.py` providing equivalent business transformations is presumptively disallowed unless there is a documented, approved business reason.

## B. Discovery strategy

Search architecture docs, file symbols, imports, callers, route registration and worker registrations; inspect actual method bodies. For Python use `rg`, AST, and tests. For TS/JS use language server/call hierarchy, `rg`, and dependency-cruiser. Consider dynamic factories, lazy injection, event handlers, alternate bootstraps, shadow implementations, transitive imports and integrations. Test cases alone do not establish whether a canonical service was bypassed.

Check subagent context explicitly. Claude built-in Explore/Plan may not receive the same repo instruction context. Pass the relevant owner contract in the delegation request or create a custom explorer that preloads this skill. Codex and Claude have different ways of loading top-level repo instructions. Inspect, don't assume.

## C. Mandatory decision tree

1. Existing canonical service covers the behavior? **Extend/reuse it**, including shared-code edits needed to preserve intent.
2. Existing canonical contract is almost sufficient? Propose an explicit shared contract extension and migration plan.
3. Different behavior is intentionally required? Document invariants, differentiate semantics, and seek approval for a separate implementation.
4. Ownership genuinely unclear? Stop implementation and propose a canonical location; do not introduce another competing flow.
5. Guardrail failure? Fix runtime architecture, not the validator. Changes to a legitimate contract require named human approval and CI review.

## D. Five independent validations

| Validation | Evidence | False reassurance to avoid |
|---|---|---|
| Canonical ownership | Forbid imports of raw mappers/rules/clients from noncanonical modules | A mere import/reachability assertion |
| Consumer completeness | Compare enumerated router/workflow registrations to checked-in consumer registry | A manually incomplete registry |
| Runtime invocation | Invoke each consumer and assert canonical boundary was called | Canonical helper imported but unused |
| Behavioral uniformity | Parametrize the same business golden inputs through all consumers | Individual endpoint unit tests |
| Policy integrity | Branch protection, required CI check and CODEOWNERS | Agent-authored tests self-approving |

Policy contract files are engineer-owned. An agent may draft proposals but must never self-authorize exceptions or weaken checks. For emergency changes, require human-reviewed exceptions with justification, scope, expiration/review date, and an owner.

## E. Reuse Impact Brief template

```text
CAPABILITY: <business behavior>
CANONICAL OWNER: <symbol / source> | UNDEFINED
AFFECTED CONSUMERS: <discovered inventory; say if incomplete>
PROPOSED REUSE: <shared changes and consumers touched>
BYPASS RISKS: <raw primitives and disallowed edges>
CHECKS: <exact CI commands + runtime/golden contract tests>
EXCEPTIONS: <none or human review required>
```

## F. Completion report

```text
Ownership: PASS | FAIL | NOT VERIFIED — <evidence>
Consumer inventory: PASS | FAIL | NOT VERIFIED — <evidence>
Runtime canonical invocation: PASS | FAIL | NOT VERIFIED — <evidence>
Golden behavior contracts: PASS | FAIL | NOT VERIFIED — <evidence>
Protected policy / CI: PASS | FAIL | NOT VERIFIED — <evidence>
New dependency edges: <files/edges, or not analyzed>
Next action: <minimal correction or required human approval>
```

## G. Context loading / installation policy

Place the same portable SKILL.md in `.agents/skills/architecture-integrity-guard/` for Codex and `.claude/skills/architecture-integrity-guard/` for Claude Code. Keep one upstream source and synchronize releases rather than hand-editing copies. Put a two-line mandatory trigger in `AGENTS.md` and in `CLAUDE.md` where applicable, but never replace existing instructions wholesale.

Use Claude Code hooks only as an optional interactive tripwire; CI is the independent enforcement point. Require branch protection and review of architecture manifests, skills, contract tests, hook configurations and workflows.
