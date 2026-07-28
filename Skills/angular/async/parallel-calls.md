# Parallel calls (forkJoin)

## Rules

- All inner observables must complete
- Output emissions arrive as an array
- Handle individual stream failures early

---

## Use:

Dashboard initialization →|| `load multiple datasets`
Form configurations →|| `fetch static dropdown lists`
Form submissions →|| `save independent child records`

---

## Anti-patterns

- Using forkJoin with long-lived streams
- Sequential API waterfalls in services
- Expecting partial results before completion
