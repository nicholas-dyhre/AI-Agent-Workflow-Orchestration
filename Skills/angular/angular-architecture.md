# Angular Architecture Rules

## Folder Responsibilities

### /services

- RxJS logic ONLY
- API calls ONLY
- data fetching ONLY
- caching + orchestration

### /app

- Signals only
- UI state only
- no async logic
- no RxJS

---

## Signals Rule

- signals = UI reactive state
- computed() = derived state
- no subscriptions in components

---

## Pipes Rule

All transformations MUST be pipes:

- filtering
- formatting
- sorting
- mapping display values

---

## Component Design

- small components only
- composition over nesting
- avoid monolithic pages

---

## Tailwind Rule

- Tailwind ONLY
- no CSS files
- remove unused utilities immediately

---

## Anti-patterns

- RxJS in components
- HTTP in UI layer
- large templates
- inline transformations
