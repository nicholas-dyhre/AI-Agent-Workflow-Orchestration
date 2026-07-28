import time
import json
import subprocess
import requests
from typing import Generator, Optional, Union
from LLM.LLMCache import LLMCache
from LLM.LLMProvider import LLMProvider


class LLM:
    def __init__(
        self,
        provider: LLMProvider,
        model: str,
        isStream: bool = False,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        auto_start: bool = False,
        process: subprocess.Popen | None = None,
        cache: LLMCache | None = None,
        num_ctx: int = 40000,
        num_predict: int = 2048,
        num_gpu: Optional[int] = None,
    ):
        self.provider = provider
        self.model = model
        self.isStream = isStream
        self.endpoint = endpoint
        self.api_key = api_key
        self.auto_start = auto_start
        self.process = process
        self.cache = cache
        self.num_ctx = num_ctx
        self.num_predict = num_predict
        self.num_gpu = num_gpu

    # ============================================================
    # Public Call Interface
    # ============================================================

    def __call__(self, prompt: str) -> Union[str, Generator[str, None, None]]:
        if self.isStream:
            return self.stream(prompt)
        else:
            return self.call(prompt)

    def call(self, prompt: str) -> str:
        if self.cache:
            cached = self.cache.get(prompt)
            if cached:
                return cached

        match self.provider:
            case LLMProvider.OLLAMA:
                self.verify_ollama()
                response = self._call_ollama(prompt)
            case LLMProvider.OPENAI:
                response = self._call_openai(prompt)
            case LLMProvider.LOCAL:
                response = self._call_local(prompt)
            case _:
                raise ValueError(f"Unknown LLM provider: {self.provider}")

        if self.cache:
            self.cache.set(prompt, response)

        return response

    def stream(self, prompt: str) -> Generator[str, None, None]:
        if self.cache:
            cached = self.cache.get(prompt)
            if cached:
                # Yield the cached data as one single chunk, then exit the generator
                yield cached
                return

        match self.provider:
            case LLMProvider.OLLAMA:
                self.verify_ollama()
                gen = self._stream_ollama(prompt)
            case LLMProvider.OPENAI:
                gen = self._stream_openai(prompt)
            case LLMProvider.LOCAL:
                gen = self._stream_local(prompt)
            case _:
                raise ValueError(f"Unknown LLM provider: {self.provider}")

            # 2. Use a wrapper function to intercept chunks for the cache
        full_response = []
        for chunk in gen:
            full_response.append(chunk)
            yield chunk

        # Once the consumer consumes the entire generator, save to cache
        if self.cache:
            self.cache.set(prompt, "".join(full_response))

    # ============================================================
    # Ollama (persistent local models)
    # ============================================================

    def _ensure_ollama_running(self):
        """Pings the server interface port. If it down, boots the binary daemon up."""
        base_endpoint = self.endpoint or "http://localhost:11434"
        try:
            # Send a quick check to the root endpoint
            requests.get(base_endpoint, timeout=2)
        except requests.exceptions.ConnectionError:
            print("[LLM] Ollama server offline. Attempting automatic start...")
            # Spin up the background server instance process
            self.process = subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            # Give the server daemon a few seconds to initialize
            time.sleep(3)

        # Trigger an on-demand pull to guarantee the specified model is installed
        print(f"[LLM] Verifying availability of local model: {self.model}")
        try:
            pull_url = f"{base_endpoint}/api/pull"
            requests.post(pull_url, json={"name": self.model}, timeout=5)
        except Exception as e:
            print(f"[LLM] Warning: Automated model pre-load checks skipped: {e}")

    def verify_ollama(self):
        try:
            res = requests.get("http://localhost:11434/api/tags")
            res.raise_for_status()
            models = [m["name"] for m in res.json()["models"]]

            if self.model not in models:
                raise Exception(f"Model {self.model} not found in Ollama. Available: {models}")

        except Exception as e:
            raise Exception(f"Ollama not ready: {e}")

    def _call_ollama(self, prompt: str) -> str:
        self._ensure_ollama_running()
        base = self.endpoint or "http://localhost:11434"
        url = (
            base
            if "/api/generate" in base
            else f"{base.rstrip('/')}/api/generate"
        )

        response = requests.post(
            url, json={"model": self.model, "prompt": prompt, "stream": False}
        )

        print(f"[LLM] Status Code: {response.status_code}")

        if response.status_code != 200:
            print(f"[LLM] Response Text: {response.text}")

        response.raise_for_status()
        return response.json()["response"]

    def _stream_ollama(self, prompt: str) -> Generator[str, None, None]:
        self._ensure_ollama_running()
        base = self.endpoint or "http://localhost:11434"
        url = (
            base
            if "/api/generate" in base
            else f"{base.rstrip('/')}/api/generate"
        )

        response = requests.post(
            url,
            json={"model": self.model, "prompt": prompt, "stream": True},
            stream=True,
        )

        print(f"[LLM] Status Code: {response.status_code}")

        if response.status_code != 200:
            print(f"[LLM] Response Text: {response.text}")

        response.raise_for_status()

        for line in response.iter_lines():
            if line:
                data = json.loads(line)
                yield data.get("response", "")

    def _build_ollama_options(self) -> dict:
        options = {"num_ctx": self.num_ctx, "num_predict": self.num_predict}
        if self.num_gpu is not None:
            options["num_gpu"] = self.num_gpu
        return options

    # ============================================================
    # OpenAI / Cloud
    # ============================================================

    def _call_openai(self, prompt: str) -> str:
        url = self.endpoint or "https://api.openai.com/v1/chat/completions"

        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

        response = requests.post(
            url,
            headers=headers,
            json={"model": self.model, "messages": [{"role": "user", "content": prompt}]},
        )

        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    def _stream_openai(self, prompt: str) -> Generator[str, None, None]:
        url = self.endpoint or "https://api.openai.com/v1/chat/completions"

        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

        # Must include "stream": True
        response = requests.post(
            url,
            headers=headers,
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": True,
            },
            stream=True,
        )
        response.raise_for_status()

        for line in response.iter_lines():
            if not line:
                continue

            # OpenAI prefixes SSE streams with 'data: '
            decoded_line = line.decode("utf-8").strip()
            if decoded_line.startswith("data: "):
                data_str = decoded_line[6:]

                # OpenAI signals the stream end with [DONE]
                if data_str == "[DONE]":
                    break

                try:
                    data = json.loads(data_str)
                    choices = data.get("choices", [])
                    if choices:
                        # Extract the token payload from the delta object
                        delta = choices[0].get("delta", {})
                        yield delta.get("content", "")
                except json.JSONDecodeError:
                    continue

    # ============================================================
    # Local Model (start → run → stop)
    # ============================================================

    def _call_local(self, prompt: str) -> str:

        if self.auto_start:
            self._start_local_model()

        try:
            result = subprocess.run([self.model, prompt], capture_output=True, text=True)

            if result.returncode != 0:
                raise RuntimeError(result.stderr)

            return result.stdout.strip()

        finally:
            if self.auto_start:
                self._stop_local_model()

    def _stream_local(self, prompt: str) -> Generator[str, None, None]:
        if self.auto_start:
            self._start_local_model()

        try:
            process = subprocess.Popen(
                [self.model, prompt],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )

            if process.stdout is None or process.stderr is None:
                raise RuntimeError("Failed to initialize subprocess I/O pipes.")

            for line in process.stdout:
                yield line

            process.wait()

            if process.returncode != 0:
                error_msg = process.stderr.read()
                raise RuntimeError(error_msg or f"Process failed with code {process.returncode}")

        finally:
            if self.auto_start:
                self._stop_local_model()

    def _start_local_model(self):
        if self.process is None:
            self.process = subprocess.Popen(
                [self.model, "--serve"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

    def _stop_local_model(self):
        if self.process:
            self.process.terminate()
            self.process = None
