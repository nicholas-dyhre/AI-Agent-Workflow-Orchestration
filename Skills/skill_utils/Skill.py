class Skill:
    def __init__(self, name: str, path: str):
        self.name = name
        self.path = path

    def load(self) -> str:
        with open(self.path) as f:
            return f.read()