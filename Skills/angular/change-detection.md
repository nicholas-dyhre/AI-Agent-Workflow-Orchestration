# Change Detection (CRITICAL)

## Rules

- Always use `OnPush`
- Prefer signals over mutable state
- Avoid zone.js dependency in new apps

---

## Correct Pattern

- signals drive UI updates
- no manual change detection

---

## Anti-patterns

- mutable component state
- default change detection
- template-heavy recalculation
