class Topic:
    """
    Stores information about a topic.
    """

    def __init__(self, name: str, description: str):
        self.name: str = name
        """The name of the topic."""
        self.dependencies: set[Topic] = set()
        """The names of the topics this topic depends on."""
        self.description: str = description
        """A description of the topic."""

    def add_dependencies(self, dependencies: set):
        for dependency in dependencies:
            self.dependencies.add(dependency)

    def __str__(self):
        return self.name
