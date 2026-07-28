# Reactive Composition (combineLatest)

## Rules

- All source streams must emit once first
- Emits a tuple on every subsequent change
- Keep derived calculation functions synchronous

---

## Use:

Multi-source filtering →|| `search + category + page`
Form validation →|| `combine independent control states`
Dynamic UI state →|| `combine user preferences with data`

---

## Anti-patterns

- Using combineLatest for triggering side-effects
- Mixing independent, unrelated streams together
- Forgetting to handle initial undefined values
