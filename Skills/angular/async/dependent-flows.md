# Dependent Flows (switchMap)

## Rules

- Cancel previous in-flight requests
- Map outer emissions to inner streams
- Keep transformation logic pure

---

## Use:

Type-ahead search →|| `instant cancellation`
ID changes →|| `fetch fresh data`
Reset triggers →|| `clear active streams`

---

## Anti-patterns

- Using switchMap for data writes
- Manual unsubscription management
- Side-effects inside the mapping function
