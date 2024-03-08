from util.event import Event, EventType
from util.topic import Topic


class DependencyInfo:
    """
    Stores information about the course topics and events
    """

    def __init__(self):
        self.events: list[Event] = []
        """A list of all events in chronological order"""
        self.grouped_events: dict[int, dict[str, dict[EventType, Event]]] = {}
        """Allows access to an event by unit, id, and type"""
        self.topics: dict[str, Topic] = {}
        """Maps topic names to their Topic object"""

    def is_topic_dependent_on(self, topic: str, dependency: str) -> bool:
        """
        Returns True if dependency is a dependency - or a sub-dependency - of topic.
        """
        return self.get_topic_dependency_depth(topic, dependency) is not None

    def get_topic_dependency_depth(self, topic: str, dependency: str) -> int | None:
        """
        Calculates the number of dependencies between topic and dependency, including dependency.
        e.g. if dependency is a direct dependency of topic, then the result is 1.
        """
        try:
            topic = self.topics[topic]
        except KeyError:
            return None
        if dependency in topic.dependencies:
            return 1
        for test_dependency in topic.dependencies:
            test_result = self.get_topic_dependency_depth(test_dependency, dependency)
            if test_result:
                return 1 + test_result
        return None

    def get_topic_taught_depth(self, topic: str, event: Event) -> int:
        """
        Calculates the maximum dependency depth of a topic within the taught topics of an event.
        """
        if topic not in event.topics_taught:
            raise ValueError(f'Topic {topic} is not taught in {event}')
        max_depth: int = 0
        for test in event.topics_taught:
            if test == topic:
                continue
            test_result = self.get_topic_dependency_depth(topic, test)
            if test_result and test_result > max_depth:
                max_depth = test_result
        return max_depth

    def get_topics_taught_depth(self, event: Event) -> int:
        """
        Calculates the maximum dependency depth of topics taught in this event on other topics taught in this event.
        :return: The number of layers of dependency within the topics taught in this event. Will be at least one
                 as long as there are topics taught in the event.
        """
        if not event.topics_taught:
            raise ValueError(f'Event {event} has no topics taught')
        max_depth: int = 0
        for topic in event.topics_taught:
            test_result = self.get_topic_taught_depth(topic, event)
            if test_result and test_result > max_depth:
                max_depth = test_result
        return max_depth + 1

    def finalize(self):
        """
        Ensures there is only one project for each unit.
        For each event, removes required topics that are dependencies of other required topics for that event.
        For each topic, removes dependencies that are dependencies of other dependencies for that topic.
        Prints information regarding removals to the console.
        """
        # Ensure only one project per unit
        units_with_projects: set[int] = set()
        for event in self.events:
            if event.event_type == 'project':
                if event.unit_number in units_with_projects:
                    raise ValueError(f"Unit {event.unit_number} has multiple projects!")
                units_with_projects.add(event.unit_number)
        # Simplify topic dependencies
        for topic in self.topics.values():
            _simplify(self, topic.dependencies, topic.__str__())
        # simplify event topics and ensure all topics are referenced in an event
        unused_topics = [item for item in self.topics]
        for event in self.events:
            _simplify(self, event.topics_required, event.__str__())
            for topic in event.topics_taught:
                if topic in unused_topics:
                    unused_topics.remove(topic)
            for topic in event.topics_required:
                if topic in unused_topics:
                    unused_topics.remove(topic)
        for topic in unused_topics:
            print(f'DATA-WARNING: topic \'{topic}\' is not used in any event')

    def get_most_recent_taught_time(self, start: Event, topic: str, include_start: bool = False) -> Event | None:
        index: int = self.events.index(start)
        if not include_start:
            index -= 1
        while topic not in self.events[index].topics_taught and index >= 0:
            index -= 1
        if index == -1:
            return None
        return self.events[index]


def _simplify(info: DependencyInfo, topics: set[str], title: str):
    """
    Takes a list of topics, and removes topics that are dependencies of other topics in the list.
    Prints info about each topic removed in this way.
    """
    topics_to_remove: set[str] = set()
    for topic in topics:
        for other_topic in topics:
            if other_topic == topic or topic in topics_to_remove:
                continue
            if info.is_topic_dependent_on(other_topic, topic):
                print(f'DATA-INFO: ignoring topic \'{topic}\' in \'{title}\' because it is a dependency of \''
                      f'{other_topic}\', which is also in \'{title}\'')
                topics_to_remove.add(topic)
                break
    for topic in topics_to_remove:
        topics.remove(topic)