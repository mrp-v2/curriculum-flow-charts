from enum import Enum
from typing import Generator

from util.topic import Topic


class EventType(Enum):
    LECTURE = 1
    LAB = 2
    HOMEWORK = 3
    PROJECT = 4

    def __lt__(self, other):
        return self.value < other.value

    def __gt__(self, other):
        return self.value > other.value


class Event:
    """
    Stores information about an event.
    """

    def __init__(self, name: str, topics_taught: set[Topic], topics_required: set[Topic]):
        """
        :param name: The name of the event.
        :param topics_taught: The names of topics taught in the event.
        :param topics_required: The names of topics required in the event.
        """
        self.name: str = name
        """The name of the event."""
        self.topics_taught: set[Topic] = topics_taught
        """The names of topics taught in the event."""
        self.topics_required: set[Topic] = topics_required
        """The names of topics required in the event."""
        event_type, unit, group_id = _parse_type_unit_and_group(self.name)
        self.event_type: EventType = event_type
        """The type of the event."""
        self.unit: int = unit
        """The unit of the event."""
        self.group_id: str | None = group_id
        """The group id of the event."""

    def __str__(self):
        return self.name

    def __lt__(self, other) -> bool:
        if isinstance(other, Event):
            event: Event = other
            if event.unit == self.unit:
                if event.group_id == self.group_id:
                    return self.event_type < event.event_type
                elif event.group_id is None:
                    return self.group_id is not None
                elif self.group_id is None:
                    return False
                return self.group_id < event.group_id
            return self.unit < event.unit
        return False

    def __gt__(self, other) -> bool:
        if isinstance(other, Event):
            event: Event = other
            if event.unit == self.unit:
                if event.group_id == self.group_id:
                    return self.event_type > event.event_type
                elif event.group_id is None:
                    return False
                elif self.group_id is None:
                    return other.group_id is not None
                return self.group_id > event.group_id
            return self.unit > event.unit
        return False

    def __le__(self, other):
        return not self > other

    def __ge__(self, other):
        return not self < other

    def get_all_topics(self) -> Generator[Topic, None, None]:
        """
        Iterates over all the topics in the event.
        Taught topics are iterated first, then required topics.
        No duplicate topics are given.
        """
        topics_seen: set[Topic] = set()
        for topic in self.topics_taught:
            if topic in topics_seen:
                continue
            topics_seen.add(topic)
            yield topic
        for topic in self.topics_required:
            if topic in topics_seen:
                continue
            topics_seen.add(topic)
            yield topic

    def calc_topic_depth(self, topic: Topic) -> int:
        """
        Calculates the maximum dependency depth of a topic within the topics taught in this event.
        :param topic: The topic to calculate the dependency depth of.
        """
        if topic not in self.topics_taught:
            raise ValueError(f'Topic \'{topic}\' is not taught in this event')
        max_depth: int = 0
        for test in self.topics_taught:
            if test == topic:
                continue
            test_result = topic.dependency_depth(test)
            if test_result and test_result > max_depth:
                max_depth = test_result
        return max_depth


def __parse_event_type(name: str) -> EventType:
    """
    Parses an event type from a name.
    :param name: The name.
    """
    event_type: EventType | None = None
    if 'lecture' in name:
        event_type = EventType.LECTURE
    if 'lab' in name:
        if event_type is not None:
            raise ValueError(f'Cannot distinguish event type of \'{name}\'')
        event_type = EventType.LAB
    if 'homework' in name or 'hw' in name:
        if event_type is not None:
            raise ValueError(f'Cannot distinguish event type of \'{name}\'')
        event_type = EventType.HOMEWORK
    if 'project' in name:
        if event_type is not None:
            raise ValueError(f'Cannot distinguish event type of \'{name}\'')
        event_type = EventType.PROJECT
    if event_type is None:
        raise ValueError(f'Cannot distinguish event type of \'{name}\'')
    return event_type


def __parse_unit_and_group(name: str) -> tuple[int, str]:
    """
    Parses a unit number and group id from a name.
    :param name: The name.
    """
    number_start: int = -1
    number_end: int = -1
    for i in range(len(name)):
        if number_start == -1 and name[i].isdigit():
            number_start = i
        elif number_start > -1 and number_end == -1 and not name[i].isdigit():
            number_end = i
        elif number_end > -1 and name[i].isdigit():
            raise ValueError(f'Cannot distinguish event number of \'{name}\'')
    unit_number = int(name[number_start:number_end])
    group_id = name[number_end] if name[number_end].strip() else None
    return unit_number, group_id


def _parse_type_unit_and_group(event_name: str) -> tuple[EventType, int, str | None]:
    """
    Parses the event type, group id, and unit using the event name.
    :param event_name: The name of the event.
    :return: A tuple containing the event type, unit number, and group id.
    """
    short_name = event_name.lower() if '-' not in event_name else event_name[0:event_name.index('-')].lower()
    try:
        event_type = __parse_event_type(short_name)
    except ValueError as e:
        raise ValueError(f'Error while parsing event type of \'{event_name}\': {e}')
    try:
        unit_number, group_id = __parse_unit_and_group(short_name)
    except ValueError as e:
        raise ValueError(f'Error while parsing unit number and group id of \'{event_name}\': {e}')
    if group_id is None and event_type != EventType.PROJECT:
        raise ValueError(f'Event \'{event_name}\' is missing an id')
    return event_type, unit_number, group_id
