# HOW TO WORK WITH TASKS

Task actions are handled using tools. To execute a task action, you must provide the exact tool_name, and a valid input according to the Tool Call description.

## Task Structure (STRICT)

You MUST output tasks using this model:

{
"id": "string",
"title": "string",
"description": "string",
"status": "pending",
"plan": [],
"code_changes": [],
"logs": [],
"metadata": {
"dependencies": []
},
"review_rounds": 0,
"branch_name": null,
"pr_url": null
}

---

# Completing a prompt

Any agent that runs, must deliver results as a Task, persisted as a file. Tools tagged with {{TASK_-_TAGS}} enable access to accomplish such persistence, updates and revisions.

# TASK COMPLETION RULES (STRICT)

You are NOT done unless:

1. A Task has been created or updated
2. The Task has been persisted using a TASK tool

If no task file is created or updated → the task is NOT complete.

---

# TOOL USAGE RULE (MANDATORY)

You MUST use tools tagged with "tasks" to:

- Create tasks
- Update tasks
- Save tasks
- Append logs
  etc.

You are NOT allowed to simulate task completion.

---

# FORBIDDEN

You MUST NOT:

- Return "final" without persisting a task
- Stop after calling a tool
- Assume work is complete without saving a task

---

# CONTINUATION RULE

After calling ANY tool:

1. Analyze result
2. Continue working
3. Only stop when task is persisted

# WORKFLOW (STRICT EXECUTION ORDER)

1. Project Planner → creates tasks
2. Planner → adds plan steps
3. Developer → implements steps
4. Reviewer → validates work

---

# STATE TRANSITIONS

You MUST respect task states:

CREATED → READY_FOR_PLANNING → PLANNING  
→ READY_FOR_DEVELOPMENT → DEVELOPMENT  
→ READY_FOR_REVIEW → REVIEW  
→ READY_FOR_MERGE → MERGED

---

# YOU MUST:

- Only act on tasks relevant to your role
- Update task state when your work is complete
- Persist the updated task using a tool
