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

    def is_dependent_on(self, dependency) -> bool:
        """
        Checks if dependency is a dependency of this topic.
        """
        return self.dependency_depth(dependency) is not None

    def dependency_depth(self, dependency) -> int | None:
        """
        Calculates the depth of a dependency - how many layers down the dependency tree it is.
        """
        if dependency in self.dependencies:
            return 1
        for test_dependency in self.dependencies:
            test_result = test_dependency.dependency_depth(dependency)
            if test_result:
                return 1 + test_result
        return None
