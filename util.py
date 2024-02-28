import csv
from io import IOBase
from typing import Literal


class Event:
    """
    Stores information about an event: its unit, name, the topics taught, and the topics required.
    Also stores a link to the previous and next event.
    """

    def __init__(self, unit: str, name: str, topics_taught: set[str], topics_required: set[str]):
        self.unit: str = unit
        self.name: str = name
        self.topics_taught: set[str] = topics_taught
        self.topics_required: set[str] = topics_required
        self.previous: Event | None = None
        self.next: Event | None = None

    def __str__(self):
        return self.name


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


class DependencyInfo:
    """
    Stores information about the course topics and events
    """

    def __init__(self):
        self.events: list[Event] = []
        # Stores Topics by their name
        self.topics: dict[str, Topic] = {}

    def is_topic_dependent_on(self, topic: str, dependency: str) -> bool:
        """
        Returns True if dependency is a dependency - or a sub-dependency - of topic.
        """
        try:
            topic = self.topics[topic]
        except KeyError:
            return False
        if dependency in topic.dependencies:
            return True
        for test_dependency in topic.dependencies:
            if self.is_topic_dependent_on(test_dependency, dependency):
                return True
        return False

    def finalize(self):
        """
        For each event, removes required topics that are dependencies of other required topics for that event.
        For each topic, removes dependencies that are dependencies of other dependencies for that topic.
        Prints information regarding removals to the console.
        """
        for topic in self.topics.values():
            simplify(self, topic.dependencies, topic.__str__())
        unused_topics = [item for item in self.topics]
        for event in self.events:
            simplify(self, event.topics_required, event.__str__())
            for topic in event.topics_taught:
                if topic in unused_topics:
                    unused_topics.remove(topic)
            for topic in event.topics_required:
                if topic in unused_topics:
                    unused_topics.remove(topic)
        for topic in unused_topics:
            print(f'INFO: topic \'{topic}\' is not used in any event')

    def get_most_recent_taught_time(self, start: Event, topic: str, include_start: bool = False) -> Event | None:
        index: int = self.events.index(start)
        if not include_start:
            index -= 1
        while topic not in self.events[index].topics_taught and index >= 0:
            index -= 1
        if index == -1:
            return None
        return self.events[index]

    def get_next_required_time(self, start: Event, topic: str, include_start: bool = False) -> Event | None:
        index: int = self.events.index(start)
        if not include_start:
            index += 1
        while index < len(self.events) and topic not in self.events[index].topics_required:
            index += 1
        if index == len(self.events):
            return None
        return self.events[index]


def simplify(info: DependencyInfo, topics: set[str], title: str):
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


def qualify(topic: str, event: Event, modifier: Literal['taught', 'required'] = None) -> str:
    return f"{event.unit}${event.name}${'' if modifier is None else f'{modifier}$'}{topic}"


def verify_topics(topics: set[str], event: str, prefix: str, info: DependencyInfo):
    for topic in topics:
        if topic not in info.topics:
            print(f'WARNING: {prefix} topic \'{topic}\' in \'{event}\' not in topics list')


def parse_topics(topics_string: str, comment: str) -> set[str]:
    topics = set()
    for topic in topics_string.split(';'):
        topic = topic.strip()
        if topic:
            if topic not in topics:
                topics.add(topic)
            else:
                print(f'DATA-ERROR: Ignoring duplicate topic \'{topic}\' {comment}')
    return topics


def read_info(topics_file: IOBase, events_file: IOBase) -> DependencyInfo:
    info = DependencyInfo()
    topics_reader = csv.reader(topics_file, delimiter='\t')
    first_row: bool = True
    for row in topics_reader:
        if first_row:
            first_row = False
            continue
        topic = row[0].strip()
        dependencies = parse_topics(row[1], f'dependency of \'{topic}\'')
        info.topics[topic] = Topic(topic, dependencies, row[2].strip())
    for topic in info.topics:
        for dependency in info.topics[topic].dependencies:
            if dependency not in info.topics:
                print(f'DATA-WARNING: dependency \'{dependency}\' of \'{topic}\' is not in the topic list')
    topic_taught_events: dict[str, str] = {}
    events_reader = csv.reader(events_file, delimiter='\t')
    first_row: bool = True
    current_unit: str | None = None
    last_event: Event | None = None
    for row in events_reader:
        if first_row:
            first_row = False
            continue
        if row[0]:
            current_unit = row[0]
        event = row[1]
        topics_taught = parse_topics(row[2], f'taught in \'{event}\'')
        for topic in topics_taught:
            if topic in topic_taught_events:
                print(f'DATA-WARNING: topic \'{topic}\' is taught in \'{event}\','
                      f' but it is already taught in \'{topic_taught_events[topic]}\'')
                topic_taught_events[topic] = event
            else:
                topic_taught_events[topic] = event
        verify_topics(topics_taught, event, 'taught', info)
        topics_needed = parse_topics(row[3], f'required in \'{event}\'')
        verify_topics(topics_needed, event, 'required', info)
        event_obj = Event(current_unit, event, topics_taught, topics_needed)
        info.events.append(event_obj)
        event_obj.previous = last_event
        if last_event is not None:
            last_event.next = event_obj
        last_event = event_obj
    info.finalize()
    return info
