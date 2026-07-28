import hashlib
import json
from pathlib import Path

class LLMCache:
    def __init__(self, cache_dir: str = ".llm_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def _key(self, prompt: str) -> str:
        return hashlib.sha256(prompt.encode()).hexdigest()

    def get(self, prompt: str) -> str | None:
        key = self._key(prompt)
        path = self.cache_dir / f"{key}.json"

        if not path.exists():
            return None

        content = path.read_text(encoding="utf-8")
        
        # Locate the exact split point where the raw prompt block ends and the response text begins
        response_marker = ',\n"response": "'
        if response_marker not in content:
            return None
            
        parts = content.split(response_marker, 1)
        response_part = parts[1]
        
        # Strip away trailing block structure symbols down to the raw string content
        if response_part.endswith('"\n}'):
            response_part = response_part[:-3]
        elif response_part.endswith('"}'):
            response_part = response_part[:-2]

        return response_part

    def set(self, prompt: str, response: str):
        key = self._key(prompt)
        path = self.cache_dir / f"{key}.json"

        # Step 1: Clean up any literal "\n" strings or escaped text inside the response payload
        # This converts hardcoded string literals into actual, true Python newlines
        clean_response = response.replace('\\n', '\n').replace('\\"', '"')

        # Step 2: Format the text layout line-by-line so it sits beautifully within the file
        # We indent every sub-line by 3 spaces to align cleanly under the parent "response" key
        response_lines = clean_response.splitlines()
        formatted_lines = []
        for i, line in enumerate(response_lines):
            if i == 0:
                formatted_lines.append(line)
            else:
                formatted_lines.append(f"   {line}")
        
        response_indented = "\n".join(formatted_lines)

        # Step 3: Piece together the file string using raw visual line breaks across all data fields
        custom_output = (
            f'{{"prompt": "{prompt}",\n'
            f'"response": "{response_indented}"\n'
            f'}}'
        )

        path.write_text(custom_output, encoding="utf-8")