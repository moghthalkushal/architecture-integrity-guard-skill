## Architecture integrity (Claude Code)

Before changing endpoints, workers, business transformations, domain rules, or shared services, invoke `/architecture-integrity-guard`. Reuse or extend canonical shared modules; do not implement sibling business logic merely to avoid a multi-file diff. Never weaken protected architecture contracts, tests, or CI to silence failures. Claude subagents may not inherit the same instructions; explicitly pass the canonical contract during delegation. State any missing checks as NOT VERIFIED.
