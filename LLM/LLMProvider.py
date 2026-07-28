from enum import Enum


# class syntax
class LLMProvider(Enum):
    OLLAMA = "ollama"
    OPENAI = "openai"
    LOCAL = "local"
