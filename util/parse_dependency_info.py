import csv
from io import IOBase

from util.dependency_info import DependencyInfo
from util.event import Event
from util.topic import Topic


def __verify_topics(topics: set[str], event: str, prefix: str, info: DependencyInfo):
    """
    Verifies that a set of topics are all found in the topics list of a DependencyInfo object.
    Prints warnings if a topic is in the set but not in the DependencyInfo object.
    :param topics: The set of topics to verify.
    :param event: The event the topics are in, used to print a warning if a topic is missing.
    :param prefix: Used to print a warning if a topic is missing.
    :param info: The DependencyInfo object to check if the topics are in.
    :return:
    """
    for topic in topics:
        if topic not in info.topics:
            print(f'WARNING: {prefix} topic \'{topic}\' in \'{event}\' not in topics list')


def __parse_topics(topics_string: str, comment: str) -> set[str]:
    """
    Parses a semicolon-separated list of topics into a set.
    Prints a warning if a duplicate topic is found.
    :param topics_string: The topics string.
    :param comment: Used when printing a warning about a duplicate topic.
    :return: A set of topic names.
    """
    topics = set()
    for topic in topics_string.split(';'):
        topic = topic.strip()
        if topic:
            if topic not in topics:
                topics.add(topic)
            else:
                print(f'DATA-ERROR: Ignoring duplicate topic \'{topic}\' {comment}')
    return topics


def __order_events(info: DependencyInfo):
    """
    Sets the next property of each event in a DependencyInfo object.
    :param info: The DependencyInfo object to use.
    """
    last_event: Event | None = None
    for unit in info.grouped_events:
        for event_id in info.grouped_events[unit]:
            for event_type in info.grouped_events[unit][event_id]:
                if last_event is not None:
                    last_event.next = info.grouped_events[unit][event_id][event_type]
                    pass
                last_event = info.grouped_events[unit][event_id][event_type]


def __read_topics(info: DependencyInfo, topics_file: IOBase):
    """
    Reads the topics file into a DependencyInfo object.
    :param info: The DependencyInfo object to read information into.
    :param topics_file: The topics file.
    """
    topics_reader = csv.reader(topics_file, delimiter='\t')
    first_row: bool = True
    for row in topics_reader:
        if first_row:
            first_row = False
            continue
        topic = row[0].strip()
        dependencies = __parse_topics(row[1], f'dependency of \'{topic}\'')
        info.topics[topic] = Topic(topic, dependencies, row[2].strip())
    for topic in info.topics:
        for dependency in info.topics[topic].dependencies:
            if dependency not in info.topics:
                print(f'DATA-WARNING: dependency \'{dependency}\' of \'{topic}\' is not in the topic list')


def __read_event(info: DependencyInfo, line: list[str], topic_taught_events: dict[str, str]) -> Event:
    """
    Reads an event from a list of strings (e.g. the entries of a line in a TSV file).
    :param info: The DependencyInfo object to use to verify topics.
    :param line: The strings to read the event from.
    :param topic_taught_events: A dictionary mapping each topic to the name of the last event it was taught in.
    :return: An event.
    """
    event_name = line[1]
    topics_taught = __parse_topics(line[2], f'taught in \'{event_name}\'')
    for topic in topics_taught:
        if topic in topic_taught_events:
            print(f'DATA-WARNING: topic \'{topic}\' is taught in \'{event_name}\','
                  f' but it is already taught in \'{topic_taught_events[topic]}\'')
            topic_taught_events[topic] = event_name
        else:
            topic_taught_events[topic] = event_name
    __verify_topics(topics_taught, event_name, 'taught', info)
    topics_needed = __parse_topics(line[3], f'required in \'{event_name}\'')
    __verify_topics(topics_needed, event_name, 'required', info)
    event_obj = Event(event_name, topics_taught, topics_needed)
    return event_obj


def __add_event(info: DependencyInfo, event: Event) -> bool:
    """
    Adds an event to a DependencyInfo object if it has any topics taught or required.
    Otherwise, prints a warning.
    :param info: The DependencyInfo object to add the event to.
    :param event: The event to add to the DependencyInfo object.
    :return: Whether the event was successfully added to the DependencyInfo object.
    """
    if not event.topics_taught and not event.topics_required:
        print(f'DATA-ERROR: Ignoring event {event} because no topics are taught or required by it')
        return False
    if event.unit not in info.grouped_events:
        info.grouped_events[event.unit] = {}
    if event.group_id not in info.grouped_events[event.unit]:
        info.grouped_events[event.unit][event.group_id] = {}
    info.grouped_events[event.unit][event.group_id][event.event_type] = event
    return True


def __read_events(info: DependencyInfo, events_file: IOBase):
    """
    Reads the events file into a DependencyInfo object.
    :param info: The DependencyInfo object to read information into.
    :param events_file: The events file.
    """
    topic_taught_events: dict[str, str] = {}
    events_reader = csv.reader(events_file, delimiter='\t')
    first_row: bool = True
    last_event: Event | None = None

    for row in events_reader:
        if first_row:
            first_row = False
            continue
        event = __read_event(info, row, topic_taught_events)
        if __add_event(info, event):
            if last_event is not None:
                last_event.next = event
            last_event = event

    __order_events(info)


def read_info(topics_file: IOBase, events_file: IOBase) -> DependencyInfo:
    """
    Reads information from a topics file and an events file to create a DependencyInfo object.
    :return: A DependencyInfo object.
    """
    info = DependencyInfo()
    __read_topics(info, topics_file)
    __read_events(info, events_file)
    info.finalize()
    return info
