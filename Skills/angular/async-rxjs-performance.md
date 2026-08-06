# Async & RxJS Performance

## Rules

- NO RxJS in components
- ALL async logic in `/services`
- avoid nested subscriptions

---

## Use:

- rxjs, async, switchMap → `dependent-flows`
- rxjs, async, forkJoin → `parallel-calls`
- rxjs, observables, combineLatest → `reactive-composition`

---

## Anti-patterns

- subscribe inside subscribe
- API calls in components
- waterfalls in UI layer
