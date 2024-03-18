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
        event_type, unit_number, event_id = _decide_event_type_and_number(self.name)
        self.event_type: EventType = event_type
        """The type of the event."""
        self.unit: int = unit_number
        """The unit of the event."""
        self.group_id: str | None = event_id
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

    def topic_taught_depth(self, topic: Topic) -> int:
        """
        Calculates the maximum dependency depth of a topic within the topics taught in this event.
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


def _decide_event_type_and_number(name: str) -> tuple[EventType, int, str | None]:
    """
    Calculates the event type, unit, and group id using the event name.
    :param name: The name of the event.
    :return: A tuple containing the event type, the unit, and the group id.
    """
    short_name = name.lower() if '-' not in name else name[0:name.index('-')].lower()
    lecture = False
    lab = False
    homework = False
    project = False
    if 'lecture' in short_name:
        lecture = True
    if 'lab' in short_name:
        lab = True
    if 'homework' in short_name or 'hw' in short_name:
        homework = True
    if 'project' in short_name:
        project = True
    event_type: EventType
    if lecture:
        if lab or homework or project:
            raise ValueError(f'Cannot distinguish event type of {name}')
        event_type = EventType.LECTURE
    elif lab:
        if homework or project:
            raise ValueError(f'Cannot distinguish event type of {name}')
        event_type = EventType.LAB
    elif homework:
        if project:
            raise ValueError(f'Cannot distinguish event type of {name}')
        event_type = EventType.HOMEWORK
    elif project:
        event_type = EventType.PROJECT
    else:
        raise ValueError(f'Cannot distinguish event type of {name}')
    number_start: int = -1
    number_end: int = -1
    for i in range(len(short_name)):
        if number_start == -1 and short_name[i].isdigit():
            number_start = i
        elif number_start > -1 and number_end == -1 and not short_name[i].isdigit():
            number_end = i
        elif number_end > -1 and short_name[i].isdigit():
            raise ValueError(f'Cannot distinguish event number of {name}')
    unit_number = int(short_name[number_start:number_end])
    group_id = short_name[number_end] if short_name[number_end].strip() else None
    if group_id is None:
        if event_type != EventType.PROJECT:
            raise ValueError(f'Event {name} is missing an id')
    return event_type, unit_number, group_id
