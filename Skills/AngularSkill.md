# Angular Skill System

This skill defines strict Angular architecture, performance rules, and code organization standards.

All files in `/angular/` contain detailed rules. This file defines how they are used.

---

## Core Rule: Layer Separation

### /services (STRICT)

All async and RxJS logic MUST live here:

- API calls
- data fetching
- streams (RxJS)
- async orchestration

Never place RxJS in components

---

### /app (UI ONLY)

Only allowed:

- Signals (`signal`, `computed`)
- UI state
- presentation logic
- component composition

Forbidden:

- RxJS
- HTTP calls
- async orchestration

---

## Global Rules

- Use Tailwind ONLY (no CSS/SCSS files)
- Remove unused Tailwind classes immediately
- Prefer small composable components
- Avoid deeply nested HTML
- Use pipes for all transformations
- Avoid logic in templates

---

## Skill Modules (with usage hints)

- async, rxjs, observables → ./angular/async-rxjs-performance.md
- change detection, performance → ./angular/change-detection.md
- bundle, build size → ./angular/bundle-optimization.md
- rendering, dom → ./angular/rendering-performance.md
- ssr, server-side → ./angular/ssr-performance.md
- templates, html → ./angular/template-optimization.md
- state, signals → ./angular/state-management.md
- memory, leaks → ./angular/memory-management.md
- architecture, structure → ./angular/angular-architecture.md

---

## Enforcement Mental Model

When writing Angular code:

1. If it is async → `/services`
2. If it affects UI state → `signals in /app`
3. If it transforms data → pipe or service
4. If it renders UI → component
5. If it styles → Tailwind only

---

## Goal

This system is designed to ensure:

- minimal re-renders
- predictable state flow
- zero async logic in UI layer
- maximum tree-shaking
- clean component boundaries
