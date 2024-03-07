class Topic:
    """
    Stores information about a topic: its name, dependencies, and description
    """

    def __init__(self, name: str, dependencies: set[str], description: str):
        self.name: str = name
        self.dependencies: set[str] = dependencies
        self.description: str = description

    def __str__(self):
        return self.name
