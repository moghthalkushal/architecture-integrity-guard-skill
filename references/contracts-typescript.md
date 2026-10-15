# TypeScript / JavaScript enforcement

Use a real TS/JS dependency parser such as [dependency-cruiser](https://github.com/sverweij/dependency-cruiser) rather than searching import text with regular expressions. The bundled Python AST checker **does not inspect JS/TS imports**. Its manifest still checks canonical files and declared-vs-discovered consumer inventory for all languages.

## Example forbidden bypass rule

Adapt to your project's build paths (and check that your dependency-cruiser version supports the rule shape):

```js
// .dependency-cruiser.cjs — add to forbidden[]
{
  name: 'only-order-normalizer-imports-primitives',
  severity: 'error',
  from: { pathNot: '^src/domain/orders/normalize\\.ts$' },
  to: { path: '^src/domain/orders/(mappers|rules)/' }
}
```

Example invocation:

```bash
npx depcruise --config .dependency-cruiser.cjs src
```

Restrict raw API clients, rule tables, repositories and mapper imports similarly. For stronger confinement, make primitives private to the owning package and disallow direct deep imports using package `exports` boundaries.

## Route completeness and real behavior

Framework-specific examples must be adapted. Derive discovered routes/worker handlers from the *real* registration surface, not a manually maintained list alone:

```ts
// Pseudocode: replace adapters and route enumeration with actual implementations.
// expect(new Set(discoverOrderRouteIds(app))).toEqual(new Set(Object.keys(consumers)));
// for (const [name, runConsumer] of Object.entries(consumers)) {
//   for (const testCase of goldenCases) {
//     const canonicalSpy = instrumentActualNormalizerCall();
//     expect(await runConsumer(testCase.input)).toEqual(testCase.expected);
//     expect(canonicalSpy).toHaveBeenCalled();
//     canonicalSpy.restore();
//   }
// }
```

Use the dependency-cruiser rule as a structural gate **plus** route enumeration **plus** runtime invocation and golden behavior tests. A `required`/`reachable` rule cannot prove that the correct runtime path actually calls the canonical implementation.

Put these tests and the dependency rules in protected files. No agent should be authorized to weaken them as a way to resolve a failing CI run.
