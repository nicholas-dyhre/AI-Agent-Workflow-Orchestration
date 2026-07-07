# Async & RxJS Performance

## Rules

- NO RxJS in components
- ALL async logic in `/services`
- avoid nested subscriptions

---

## Use:

- switchMap → dependent flows
- forkJoin → parallel calls
- combineLatest → reactive composition

---

## Anti-patterns

- subscribe inside subscribe
- API calls in components
- waterfalls in UI layer
