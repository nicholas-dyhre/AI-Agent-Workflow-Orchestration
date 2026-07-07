class workflow:
    def __init__(self, nodes, edges):
        self.nodes = nodes
        self.edges = edges

class edge: 
    def __init__(self, from_agent, to_agent, condition=None):
        self.from_agent = from_agent
        self.to_agent = to_agent
        self.condition = condition
