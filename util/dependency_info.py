from typing import Generator

from util import InfoLevel
from util.event import Event, EventType
from util.topic import Topic


class DependencyInfo:
    """
    Stores information about the course topics and events.
    """

    def __init__(self):
        self.grouped_events: dict[int, dict[str | None, dict[EventType, Event]]] = {}
        """Allows access to an event by unit, id, and type"""

    def get_topics(self) -> Generator[Topic, None, None]:
        """
        Iterates over all topics in all events.
        Duplicate topics are ignored.
        """
        topics_seen: set[Topic] = set()
        for event in self.get_events():
            for topic in event.topics_taught:
                if topic in topics_seen:
                    continue
                topics_seen.add(topic)
                yield topic

    def get_events(self, start: Event = None, include_start: bool = None, forward: bool = True) -> \
            Generator[Event, None, None]:
        """
        Iterates through all events.
        :param start: The event to start iterating at.
        :param include_start: Whether to include the starting event when iterating.
                              Must be specified if `start` is not `None`.
        :param forward: Whether to iterate forwards or backwards. Defaults to forwards.
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

    def finalize(self, info_level: InfoLevel):
        """
        Ensures there is only independent event of each type for each unit.
        For each event, removes required topics that are dependencies of other required topics for that event.
        For each topic, removes dependencies that are dependencies of other dependencies for that topic.
        Prints information regarding removals to the console.
        """
        # Ensure each event type has only one group independent instance per unit
        independent_events: dict[int, list[EventType]] = {}
        for event in self.get_events():
            if event.group_id is not None:
                continue
            if event.unit not in independent_events:
                independent_events[event.unit] = []
            if event.event_type in independent_events[event.unit]:
                raise ValueError(f'Unit {event.unit} has multiple events of type {event.event_type} without groups')
            independent_events[event.unit].append(event.event_type)
        # Simplify topic dependencies
        for topic in self.get_topics():
            _simplify(topic.dependencies, topic.__str__(), info_level)
        # simplify event topics and ensure all topics are referenced in an event
        unused_topics = [item for item in self.get_topics()]
        for event in self.get_events():
            _simplify(event.topics_required, event.__str__(), info_level)
            for topic in event.topics_taught:
                if topic in unused_topics:
                    unused_topics.remove(topic)
            for topic in event.topics_required:
                if topic in unused_topics:
                    unused_topics.remove(topic)
        if info_level >= InfoLevel.WARNING:
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


def _simplify(topics: set[Topic], label: str, info_level: InfoLevel):
    """
    Removes any `Topic` that is a dependency of any other `Topic` in the `set`.
    Prints info about each `Topic` removed in this way.
    :param topics: The `set` to simplify.
    :param label: A label for the list, used when printing info messages about removals.
    """
    topics_to_remove: set[Topic] = set()
    for topic in topics:
        for other_topic in topics:
            if other_topic == topic or topic in topics_to_remove:
                continue
            if other_topic.is_dependent_on(topic):
                if info_level >= InfoLevel.INFO:
                    print(f'DATA-INFO: ignoring topic \'{topic}\' in \'{label}\' because it is a dependency of \''
                          f'{other_topic}\', which is also in \'{label}\'')
                topics_to_remove.add(topic)
                break
    for topic in topics_to_remove:
        topics.remove(topic)
