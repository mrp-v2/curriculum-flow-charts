from typing import Generator

from util.event import Event, EventType
from util.topic import Topic


class DependencyInfo:
    """
    Stores information about the course topics and events.
    """

    def __init__(self):
        self.grouped_events: dict[int, dict[str, dict[EventType, Event]]] = {}
        """Allows access to an event by unit, id, and type"""

    def get_topics(self) -> Generator[Topic, None, None]:
        topics_seen: set[Topic] = set()
        for event in self.get_events():
            for topic in event.topics_taught:
                if topic in topics_seen:
                    continue
                topics_seen.add(topic)
                yield topic

    def get_events(self, start: Event = None, include_start: bool = None, forward: bool = True) -> Generator[
        Event, None, None]:
        """
        Iterates through all events.
        """
        if start is not None and include_start is None:
            raise ValueError('If start is not None, then include_start should also not be None')
        if forward:
            for unit in self.grouped_events:
                for group_id in self.grouped_events[unit]:
                    for event in self.grouped_events[unit][group_id].values():
                        if start is not None:
                            if event < start:
                                continue
                            elif event == start and not include_start:
                                continue
                        yield event
        else:
            for unit in self.grouped_events.__reversed__():
                for group_id in self.grouped_events[unit].__reversed__():
                    for event in self.grouped_events[unit][group_id].values().__reversed__():
                        if start is not None:
                            if event > start:
                                continue
                            elif event == start and not include_start:
                                continue
                        yield event

    def is_topic_dependent_on(self, topic: Topic, dependency: Topic) -> bool:
        """
        Returns True if dependency is a dependency - or a sub-dependency - of topic.
        """
        return self.get_topic_dependency_depth(topic, dependency) is not None

    def get_topic_dependency_depth(self, topic: Topic, dependency: Topic) -> int | None:
        """
        Calculates the number of dependencies between topic and dependency, including dependency.
        e.g. if dependency is a direct dependency of topic, then the result is 1.
        """
        if dependency in topic.dependencies:
            return 1
        for test_dependency in topic.dependencies:
            test_result = self.get_topic_dependency_depth(test_dependency, dependency)
            if test_result:
                return 1 + test_result
        return None

    def get_topic_taught_depth(self, topic: Topic, event: Event) -> int:
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
        for event in self.get_events():
            if event.event_type == 'project':
                if event.unit in units_with_projects:
                    raise ValueError(f"Unit {event.unit} has multiple projects!")
                units_with_projects.add(event.unit)
        # Simplify topic dependencies
        for topic in self.get_topics():
            _simplify(self, topic.dependencies, topic.__str__())
        # simplify event topics and ensure all topics are referenced in an event
        unused_topics = [item for item in self.get_topics()]
        for event in self.get_events():
            _simplify(self, event.topics_required, event.__str__())
            for topic in event.topics_taught:
                if topic in unused_topics:
                    unused_topics.remove(topic)
            for topic in event.topics_required:
                if topic in unused_topics:
                    unused_topics.remove(topic)
        for topic in unused_topics:
            print(f'DATA-WARNING: topic \'{topic}\' is not used in any event')

    def get_most_recent_taught_time(self, start: Event, topic: Topic, include_start: bool = False) -> Event | None:
        """
        Finds the most recent time a topic was taught, before the starting event.
        :param start: The event to search for the topic being taught before it.
        :param topic: The topic to search for being taught.
        :param include_start: If true, includes the starting event in the search.
        :return: The event if one is found, otherwise None.
        """
        for event in self.get_events(start, include_start, False):
            if topic not in event.topics_taught:
                continue
            return event
        return None


def _simplify(info: DependencyInfo, topics: set[Topic], title: str):
    """
    Takes a list of topics, and removes topics that are dependencies of other topics in the list.
    Prints info about each topic removed in this way.
    :param title: The title of the list, used when printing info messages about removals.
    """
    topics_to_remove: set[Topic] = set()
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
