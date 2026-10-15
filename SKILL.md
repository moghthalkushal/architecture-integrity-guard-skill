---
name: architecture-integrity-guard
description: Prevent architectural drift when AI coding agents add endpoints, change business logic, refactor shared code, or create new execution paths. Discover canonical implementations, prefer extending shared flows over parallel code, identify forbidden dependency bypasses, verify consumer coverage and contracts, and report evidence before completion. Use for Codex, Claude Code, and agent-generated PR architecture reviews.
---

# Architecture Integrity Guard

**Non-negotiable:** passing unit tests is not proof of architectural consistency. When a canonical flow applies, extending that shared flow **is in scope** even if it affects multiple consumers. Do not create a sibling implementation to keep the diff small. If the canonical contract truly cannot support the change, explain the conflict and request architectural authorization instead of silently forking it.

## Trigger and boundaries

Use before and after changes to APIs, handlers, workers, transformations, domain rules, workflows, persistence boundaries, integration clients, or shared packages. Use in review-only mode for drift audits. Skip detailed checks for docs-only changes unless they alter architecture policy.

Do not assume all similar code is duplicate domain behavior: adapters and intentionally distinct business rules are allowed when their contracts justify the difference. Do not rewrite unrelated logic or weaken existing validation to satisfy a check.

## Workflow (one compact pass; do not spawn redundant reviewers)

1. **Locate the truth.** Read `AGENTS.md`, `CLAUDE.md` when applicable, architecture contracts (`architecture/canonical-contracts.json` by default), relevant ADRs, shared services, and neighboring tests. Verify what instruction files actually loaded; an explorer subagent may have different context. Never assume its summary includes architecture constraints.
2. **Trace the change.** Search for all behaviorally equivalent implementations, not only matching names. Enumerate affected entrypoints/consumers and follow execution paths to transformations, business rules, and privileged low-level primitives. Distinguish observed code from inferred paths.
3. **Produce a concise Reuse Impact Brief (<= 250 words):** capability; canonical owner (symbol/file); consumer inventory; shared changes needed; forbidden bypass surfaces; exceptions/risks; exact tests to run. If no authoritative owner exists, label it `UNDEFINED` and propose one before coding. Do not generate a second implementation by default.
4. **Implement through the canonical contract.** Extend canonical code and update affected consumers together; endpoint adapters may differ, but protected business invariants must remain shared. Avoid a new parallel path or raw primitive access outside its owner. If the contract does not fit, stop and submit a small ADR/exception proposal for human review. No automatic guardrail edits.
5. **Verify multiple independent properties:**
   - **Ownership:** forbidden imports and bypasses fail in architecture lint.
   - **Inventory:** discovered consumers are registered; route discovery must be complete for the chosen framework.
   - **Execution:** exercise representative paths and assert they invoke the canonical boundary (runtime spy/instrumentation or equivalent).
   - **Behavior:** run the same golden business cases through every applicable consumer.
   - **Protection:** guards/contracts changed only with explicit owner approval and branch-protected CI.
6. **Report results** as `PASS`, `FAIL`, or `NOT VERIFIED` **per property**, with paths, commands, evidence, newly created edges, exceptions, and remaining risk. Do not report PASS merely because a skill ran or all existing unit tests passed.

## Execute deterministic checks

From the repository root, once engineers have configured `architecture/canonical-contracts.json`:

```bash
python .agents/skills/architecture-integrity-guard/scripts/arch_guard.py check --repo . --config architecture/canonical-contracts.json
```

In Claude Code, substitute `.claude/skills/architecture-integrity-guard/scripts/arch_guard.py`. The included checker validates canonical file ownership, registered consumers against configured discovery globs, and **Python AST** forbidden imports. It **does not** prove JS/TS dependency safety, semantic equivalence, actual route inventory, or runtime canonical invocation. Those require the additional stack-specific checks described below. No configuration means `NOT VERIFIED`, not `PASS`.

## Read supporting materials only when relevant

- [Implementation playbook](references/implementation-playbook.md): discovery, decision tree, exceptions, reporting, context loading, and ownership.
- [Python contracts](references/contracts-python.md): structural and runtime tests, route registry completeness, golden cases.
- [TypeScript contracts](references/contracts-typescript.md): dependency-cruiser and behavioral test patterns.
- [Evaluation protocol](references/evaluation.md): adversarial tests, token/refactor baselines, pilot and roll-out.
- [Starter contracts](templates/canonical-contracts.example.json), [CI](templates/architecture-guard.yml), [CODEOWNERS](templates/CODEOWNERS.example), [Claude hook](templates/claude-settings.hooks.example.json): adapt and have engineers own them; do not install blindly.

## Critical limitations

- Static reachability only proves the canonical flow **can** be reached, not that the target request uses it. Pair forbidden-bypass rules with actual execution checks.
- Consumer file globs are a partial inventory. A framework router or dispatch registry must be enumerated separately in tests; unregistered routes remain a risk without this check.
- A Claude `PreToolUse` hook is advisory/protective for supported edit tools, not a security boundary; a shell or another tool may modify files. A `Stop` hook is not a reliable fail-closed gate. Require independent CI and human-owned protected branches.
- Skill guidance is not a substitute for independent verification. Never modify its own tests, manifests, allowlists, or CI rules merely to turn a failing result green.
