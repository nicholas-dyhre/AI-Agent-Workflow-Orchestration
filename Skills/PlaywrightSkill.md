# Playwright Skill System

This skill provides guidance for writing, debugging, maintaining, and scaling Playwright test suites in TypeScript.

## Core Rule (NON-NEGOTIABLE)

- Tests must be deterministic, isolated, and parallel-safe
- No business logic in tests
- All async logic must be mocked or controlled

## Modules

See folder for details.

This skill defines strict rules for End-to-End testing.

---

# Test Location Rule

All E2E tests MUST be written to:

```
[PROJECT_ROOT]/E2E
```

---

# E2E Test Structure

## Pattern

- Arrange
- Act
- Assert

---

## Rules

- keep tests linear
- no branching logic
- no duplicated setup
- no conditional statements

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

- Playwright, enforcement, rules, constraints, testing → `playwright-enforcement`
- Debugging, trace inspection, root cause → `debugging`
- Fixtures, test setup, teardown, dependency injection, test context → `fixtures`
- Routing, URL handling, flow control, redirection → `routing`

- accessibility, screen readers, keyboard navigation → `accessibility`
- experimental APIs, tracing, extensions, capabilities → `advanced-features`
- assertions, waits, synchronization, expectations → `assertions-waits`
- authentication, login, sessions, cookies, tokens, identity flow → `authentication`
- browser APIs, window, DOM APIs, execution context, JS bridge → `browser-apis`
- CI/CD, pipelines, automation, GitHub Actions, deployment testing → `ci-cd`
- debugging, traces, screenshots, logs, playwright inspector → `debugging`
- error handling, negative testing, failure cases, exceptions → `error-testing`
- fixtures, hooks, beforeEach, afterEach, lifecycle, setup → `fixtures-hooks`
- flaky tests, stability, retries, determinism, timing issues → `flaky-tests`
- locators, selectors, DOM targeting, querying elements → `locators`
- mobile testing, responsive, device emulation, viewport → `mobile-testing`
- multi-user, concurrency, sessions, parallel users, isolation → `multi-user`
- network mocking, intercept, API mocking, request stubbing → `network-mocking`
- page object model, abstraction, POM, UI encapsulation → `page-object-model`
- performance, load, speed, profiling, bottlenecks → `performance`
- security testing, XSS, auth bypass, injection, vulnerability testing → `security-testing`
- test writing, best practices, structure, readable tests, maintainability → `test-writing`
- visual testing, screenshots, regression, UI diffing, snapshots → `visual-testing`

---
