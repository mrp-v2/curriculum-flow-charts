class Topic:
    """
    Stores information about a topic.
    """

    def __init__(self, name: str, dependencies: set[str], description: str):
        self.name: str = name
        """The name of the topic."""
        self.dependencies: set[str] = dependencies
        """The names of the topics this topic depends on."""
        self.description: str = description
        """A description of the topic."""

    def __str__(self):
        return self.name
