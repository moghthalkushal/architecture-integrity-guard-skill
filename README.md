# Architecture Integrity Guard v1.0

**One portable Agent Skill for Codex and Claude Code.** It guides AI coding agents to preserve canonical shared implementations, and includes a no-dependency architecture contract checker plus opt-in templates for CI, code ownership, and Claude Code hooks.

> Core principle: **Functional correctness is not architectural consistency.** Extending canonical code is within scope; a second implementation is not the default solution.

## What is implemented versus what requires integration

| Guardrail | Status |
|---|---|
| Reuse-first agent workflow with concise impact brief | Included in `SKILL.md` |
| Canonical file and explicit consumer inventory validation | Working Python CLI, any stack |
| Newly discovered consumer file under configured globs fails | Working Python CLI, any stack |
| Python direct forbidden-import / ownership boundary | Working Python AST CLI |
| Interactive ask before editing human-owned config in Claude | Working *optional* Claude PreToolUse script (not a security boundary) |
| JavaScript/TypeScript forbidden dependencies | Example dependency-cruiser rule; integrate in host repo |
| Real router/dispatcher completeness | Contract-test pattern; implement for your framework |
| Verify every consumer *executes* canonical code | Runtime test pattern; implement for your framework |
| Golden cross-consumer behavior tests | Test pattern; real cases are team-owned |
| Real human review / branch protection | CODEOWNERS/CI templates; enable in GitHub settings |

An unconfigured skill does **not** magically enforce an architecture. Missing configuration or unchecked runtime properties must be reported as `NOT VERIFIED`.

## Install (project scoped)

Unzip `architecture-integrity-guard.zip` to obtain its top-level `architecture-integrity-guard/` folder. Then run from the directory containing the extracted folder:

```bash
python architecture-integrity-guard/scripts/install.py --repo /path/to/your/repo --targets both --init-starters
```

For only Codex use `--targets codex`; for only Claude Code use `--targets claude`. If you want to install manually:

- Codex: copy `architecture-integrity-guard/` into `<repo>/.agents/skills/`.
- Claude Code: copy `architecture-integrity-guard/` into `<repo>/.claude/skills/`.

The installer deliberately refuses to overwrite an existing copy unless `--overwrite` is specified. Both installations are copies of a single versioned source; keep them synchronized on upgrades.

**Windows:** use `py` rather than `python` if your Python launcher is configured that way; in the optional Claude hook JSON, change `python3` to the executable available on your machine. This package requires Python 3.9+ and no third-party Python dependencies.

## Configure one capability first

1. Read `templates/canonical-contracts.example.json`. Replace example paths with **real files** and copy it to `<repo>/architecture/canonical-contracts.json`. Do not commit the fake example as the live manifest.
2. Pick 2–3 high-risk capabilities, each with an explicit canonical source, discovery globs, checked-in consumer file list, and owner-only raw modules. Use Python `python_forbidden_imports` rules for Python repos.
3. Add `templates/AGENTS.fragment.md` to your existing `AGENTS.md`, and `templates/CLAUDE.fragment.md` to your existing `CLAUDE.md` when you use Claude. Do not overwrite other repo instructions.
4. Merge `templates/architecture-guard.yml` into `.github/workflows/architecture-guard.yml`; add independent language-specific dependency checks and test commands for actual runtime paths and cross-consumer golden cases.
5. Adapt `templates/CODEOWNERS.example` with a real team, place it at `.github/CODEOWNERS`, require Code Owner review and the architecture job via branch protection.
6. Optional: merge `templates/claude-settings.hooks.example.json` into `.claude/settings.json` for interactive approval prompts on supported edit tools.

### Quick checks

For Codex installation:

```bash
python .agents/skills/architecture-integrity-guard/scripts/arch_guard.py doctor --repo . --config architecture/canonical-contracts.json
python .agents/skills/architecture-integrity-guard/scripts/arch_guard.py check --repo . --config architecture/canonical-contracts.json
```

For Claude installation:

```bash
python .claude/skills/architecture-integrity-guard/scripts/arch_guard.py check --repo . --config architecture/canonical-contracts.json
```

Exit codes: `0` means **only the CLI's documented scope passed**; `1` means violations; `2` means config/usage error or `NOT VERIFIED`. Runtime path invocation, dynamic router completeness, TS imports and semantic duplication are **not** covered by the Python CLI.

### Invoke the skill

- **Claude Code:** `/architecture-integrity-guard` and ask it to implement/review a feature.
- **Codex:** `$architecture-integrity-guard` and ask it to implement/review a feature.

Example:

> Use architecture-integrity-guard to add an orders bulk-ingest endpoint. Identify the canonical transformation owner, list all consumers, propose the shared-code change before implementation, and verify forbidden bypasses plus runtime and golden-case contracts. Mark unimplemented checks as NOT VERIFIED.

## Self-test

```bash
python -m unittest discover -s architecture-integrity-guard/tests -v
```

The test suite covers a passing baseline, new unregistered consumer detection, direct and relative Python import bypass detection, missing/empty manifests, duplicate capability IDs, and opt-in hook behavior.

## Security and operational caveats

- The skill and installed scripts are executable repo content. Review them before installing in untrusted repositories.
- The hook covers common edit tools; other tool surfaces and shell commands can bypass it. It should never replace protected CI.
- For serious enforcement, store architecture rules and contract tests in protected files with real repository review policy.
- Developers should own the goldens and manifest. AI can propose changes but should not approve its own rule relaxations.
- Always compare **observed runtime paths** with required canonical paths. Static import reachability is insufficient.
- The checked-in consumer file globs are only a partial safeguard. A new endpoint with an unexpected naming scheme requires framework router enumeration and human review.
- The Python CLI checks ordinary static imports, not dynamic imports, reflection, DI resolution, side effects or semantic clones. Complement it with targeted tests and code review.

## Package tree

```text
architecture-integrity-guard/
├── SKILL.md
├── README.md
├── scripts/
│   ├── arch_guard.py
│   ├── claude_protect.py
│   └── install.py
├── references/
│   ├── implementation-playbook.md
│   ├── contracts-python.md
│   ├── contracts-typescript.md
│   └── evaluation.md
├── templates/
│   ├── canonical-contracts.example.json
│   ├── AGENTS.fragment.md
│   ├── CLAUDE.fragment.md
│   ├── claude-settings.hooks.example.json
│   ├── architecture-guard.yml
│   └── CODEOWNERS.example
└── tests/
    └── test_arch_guard.py
```

## Source documentation

- Claude Code skills: https://code.claude.com/docs/en/skills
- Claude Code hooks: https://code.claude.com/docs/en/hooks
- OpenAI Codex project skills: https://developers.openai.com/codex/skills
- Dependency-cruiser reference: https://github.com/sverweij/dependency-cruiser/blob/main/doc/rules-reference.md
