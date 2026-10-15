# Python enforcement: AST + runtime contracts

The bundled `scripts/arch_guard.py` checks `python_forbidden_imports` using Python's AST. Example manifest shape:

```json
{
  "version": 1,
  "capabilities": [{
    "id": "order-normalization",
    "canonical": "src/domain/orders/normalize.py",
    "consumer_globs": ["src/api/orders/*_route.py", "src/workers/order_*.py"],
    "consumers": ["src/api/orders/create_route.py", "src/workers/order_ingest.py"],
    "python_forbidden_imports": [{
      "modules": ["src.domain.orders.mappers", "src.domain.orders.rules"],
      "allow_files": ["src/domain/orders/normalize.py"]
    }]
  }]
}
```

This rule prevents *direct* static imports of those Python modules from everywhere except the allowlist. It is not whole-program semantic proof. The checker can resolve ordinary Python relative imports using the module path rooted at the repository. Imports performed via `importlib`, reflection, dependency injection or string module names need additional controls.

## Framework-based consumer registry

The following is a **pattern**, not a drop-in test: replace router APIs, adapters, paths and golden cases with the project's real mechanisms. Importing a service does not prove execution. Ensure the expected canonical service function is wrapped by a spy or traced and its call count is asserted per consumer.

```python
import pytest

# Import real, engineer-reviewed adapters and router enumeration helpers.
# from app.routes import enumerate_order_route_ids
# from tests.architecture.adapters import ORDER_CONSUMERS, GOLDEN_CASES

# def test_all_order_routes_registered():
#     assert set(enumerate_order_route_ids()) == set(ORDER_CONSUMERS)
#
# @pytest.mark.parametrize('consumer_id', ORDER_CONSUMERS)
# @pytest.mark.parametrize('case', GOLDEN_CASES)
# def test_every_consumer_obeys_contract(consumer_id, case, canonical_spy):
#     result = ORDER_CONSUMERS[consumer_id](case.input)
#     assert result == case.expected
#     canonical_spy.assert_called()  # Real instrumentation must wrap the invoked path.
```

For FastAPI, one reasonable enumeration starts from `app.routes` (with matching APIRoute instances) and filters the target prefix; distinguish route methods and operation IDs instead of comparing ambiguous URL paths. Workers/event consumers need a second enumerator, often from the dispatcher/queue registration surface. Prefer the *exact same* adapter machinery for real endpoints and golden cases, not a hand-built alternative transformation inside a test.

## Dynamic safety

- Use one golden corpus for transformations, validations, null handling, errors, feature flags, locale/currency precision, idempotency, and versioning.
- Assert runtime invocation at the exact canonical seam; spies can miss calls if the endpoint cached a direct function reference before monkeypatching. Instrument the actual call site or use a wrapper provider seam.
- Distinguish equivalence at domain-result level from protocol-specific envelope fields.
- Add a new golden case whenever a divergence incident occurs.
