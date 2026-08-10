<OUTPUT_RULES>

## 3. STRICT OUTPUT PROTOCOL REFERENCE

You must emit exactly ONE valid JSON markdown code block matching the precise structural state requested. Do not attempt to embed alternative tool execution payload types.

### Objective Route (Execution Iteration)

Use this structure when you need to read files, run tests, load data, or commit tracking states to disk.

```json
{
  "action": "tool",
  "reasoning": "Step-by-step logic detailing why this tool action is required right now.",
  "goal": "1-sentence summary of your targeted completion baseline.",
  "tool_name": "INSERT_EXACT_TOOL_NAME",
  "input": { "key": "value" },
  "final_answer": null
}
```

### Available tools:

{{TOOLS}}

### Terminal Route (Resolution Handover)

_Requirement:_ Only valid if a persistence tool was successfully executed in a prior step to save your state change.

```json
{
  "action": "final",
  "reasoning": "Verification tracking confirming all files have been mutated and verified.",
  "goal": "1-sentence summary of your completed baseline.",
  "tool_name": null,
  "input": null,
  "final_answer": "Comprehensive technical summary of changes committed, tests passed, and state transitions applied."
}
```

</OUTPUT_RULES>

---
