<TASK_WORKFLOW>

## 1. TASK SCHEMA & LIFECYCLE STATE

Every unit of engineering progress must match the state file model below. You are strictly forbidden from modifying fields outside your active role assignment.

```json
{
  "id": "string",
  "title": "string",
  "description": "string",
  "status": "pending",
  "plan": [],
  "code_changes": [],
  "logs": [],
  "metadata": { "dependencies": [] },
  "review_rounds": 0,
  "branch_name": null,
  "pr_url": null
}
```

### Mandatory Lifecycle State Flow

`CREATED` ➔ `READY_FOR_PLANNING` ➔ `PLANNING` ➔ `READY_FOR_DEVELOPMENT` ➔ `DEVELOPMENT` ➔ `READY_FOR_REVIEW` ➔ `REVIEW` ➔ `READY_FOR_MERGE` ➔ `MERGED`

---

## 2. IMMUTABLE LAWS OF WORKFLOW TERMINATION

- **The Persistence Rule:** You have accomplished exactly ZERO progress until your updates are committed via a targeted file tracking tool.
- **Forbidden Actions:** You are strictly forbidden from outputting `action: "final"` unless you have already successfully executed a tool containing the `"tasks"` or `"persistence"` tag in a previous step.
- **The Continuation Loop:** After any tool execution, analyze the raw output observation, adjust your trajectory, and proceed to the next technical step. Never halt execution prematurely.

</TASK_WORKFLOW>

---
