import ast
import json
import re


def clean_and_parse_json(raw_string: str) -> str:
    """Cleans up markdown and Python dict formats, returning a strict JSON string."""
    if not isinstance(raw_string, str):
        return raw_string
    
    cleaned = raw_string.strip()
    match = re.match(r"^```(?:json|JSON)?\s*(.*?)\s*```\$", cleaned, re.DOTALL)
    if match:
        cleaned = match.group(1).strip()
    else:
        cleaned = (
            cleaned.replace("```json", "")
            .replace("```JSON", "")
            .replace("```", "")
            .strip()
        )

    def fix_backticks_in_input(text: str) -> str:
        pattern = re.compile(r'"input"\s*:\s*\{.*?\}', re.DOTALL)

        def process_block(match: re.Match) -> str:
            block = match.group(0)

            # Replace `value` → "value"
            fixed = re.sub(
                r'"([^"]+)"\s*:\s*`([^`]*)`',
                lambda m: f'"{m.group(1)}": "{m.group(2)}"',
                block
            )

            return fixed

        return pattern.sub(process_block, text)
    
    cleaned = fix_backticks_in_input(cleaned)

    cleaned = re.sub(r"\bnull\b", "None", cleaned)

    try:
        json.loads(cleaned)
        return cleaned
    except json.JSONDecodeError:
        pass

    try:
        python_obj = ast.literal_eval(cleaned)
        return json.dumps(python_obj, ensure_ascii=False)
    except (ValueError, SyntaxError):
        return cleaned