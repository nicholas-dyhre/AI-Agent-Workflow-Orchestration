class Skill:
    def __init__(self, name: str, path: str, keywords: list[str] = []):
        self.name = name
        self.path = path
        self.keywords : list[str] = keywords

    def load(self) -> str:
        with open(self.path) as f:
            return f.read()