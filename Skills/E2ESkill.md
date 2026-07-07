# E2E Skill System (Playwright Enforcement Layer)

This skill defines strict rules for End-to-End testing.

---

# Core Rule (NON-NEGOTIABLE)

All E2E tests MUST use:

> **Playwright (TypeScript)**

No other frameworks are allowed.

---

# Test Location Rule

All E2E tests MUST be written to:

```
/E2E
```

This folder is located **next to `.claude/`**, not inside it.

---

# Directory Layout

```
/.claude
/E2E
```

---

# Execution Model

When writing or modifying E2E tests:

1. Use Playwright APIs only
2. Write tests into `/E2E`
3. Keep tests isolated and deterministic
4. Do not mix unit/integration logic here

---

# What Belongs in E2E

Use Playwright E2E tests for:

- user flows
- authentication flows
- navigation
- form submission
- API + UI integration
- cross-page behavior

---

# What is NOT allowed

- unit tests
- component tests
- service logic tests
- business logic inside tests
- duplicate selectors

---

# Skill Modules

Routing logic is split into focused modules:

- Playwright enforcement → `./e2e/playwright-enforcement.md`
- Test structure → `./e2e/test-structure.md`
- Debugging → `./e2e/debugging.md`
- Fixtures → `./e2e/fixtures.md`
- Routing rules → `./e2e/routing.md`

---

# Decision Rule

When creating tests:

- If it runs in a browser → E2E (Playwright)
- If it verifies UI flow → E2E (Playwright)
- If it touches multiple systems → E2E (Playwright)

---

# Golden Rule

If you're unsure:

> Default to Playwright E2E in `/E2E`
