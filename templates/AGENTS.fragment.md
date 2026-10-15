## Architecture integrity (Codex)

Before changing endpoints, workers, business transformations, domain rules, or shared services, use `$architecture-integrity-guard`. Reuse or extend the canonical implementation even if it means editing shared modules. Do not create sibling business-logic paths solely to minimize diffs. Never weaken architecture manifests, tests, or CI to make a failing check pass. Run the human-owned architecture checks, list any missing checks as NOT VERIFIED, and seek approval for legitimate exceptions.
