import csv
from io import IOBase

from util.dependency_info import DependencyInfo
from util.event import Event
from util.topic import Topic


def __verify_topics(topics: set[str], event: str, prefix: str, info: DependencyInfo):
    for topic in topics:
        if topic not in info.topics:
            print(f'WARNING: {prefix} topic \'{topic}\' in \'{event}\' not in topics list')


def __parse_topics(topics_string: str, comment: str) -> set[str]:
    topics = set()
    for topic in topics_string.split(';'):
        topic = topic.strip()
        if topic:
            if topic not in topics:
                topics.add(topic)
            else:
                print(f'DATA-ERROR: Ignoring duplicate topic \'{topic}\' {comment}')
    return topics


def __verify_events(info: DependencyInfo):
    list_index: int = 0
    for unit in info.grouped_events:
        for event_id in info.grouped_events[unit]:
            for event_type in info.grouped_events[unit][event_id]:
                if info.grouped_events[unit][event_id][event_type] != info.events[list_index]:
                    raise ValueError('Events are not given in the same order as their unit, id, and type indicate!')
                list_index += 1


def __read_topics(info: DependencyInfo, topics_file: IOBase):
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


def __read_event(info: DependencyInfo, line: list[str], unit: str | None, topic_taught_events: dict[str, str]) -> Event:
    if line[0]:
        unit = line[0]
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
    event_obj = Event(unit, event_name, topics_taught, topics_needed)
    return event_obj


def __add_event(info: DependencyInfo, event: Event) -> bool:
    if not event.topics_taught and not event.topics_required:
        print(f'DATA-ERROR: Ignoring event {event} because no topics are taught or required by it')
        return False
    info.events.append(event)
    if event.unit_number not in info.grouped_events:
        info.grouped_events[event.unit_number] = {}
    if event.event_id not in info.grouped_events[event.unit_number]:
        info.grouped_events[event.unit_number][event.event_id] = {}
    info.grouped_events[event.unit_number][event.event_id][event.event_type] = event
    return True


def __read_events(info: DependencyInfo, events_file: IOBase):
    topic_taught_events: dict[str, str] = {}
    events_reader = csv.reader(events_file, delimiter='\t')
    first_row: bool = True
    last_unit: str | None = None
    last_event: Event | None = None

    for row in events_reader:
        if first_row:
            first_row = False
            continue
        event = __read_event(info, row, last_unit, topic_taught_events)
        if __add_event(info, event):
            if last_event is not None:
                last_event.next = event
            last_unit = event.unit
            last_event = event

    __verify_events(info)


def read_info(topics_file: IOBase, events_file: IOBase) -> DependencyInfo:
    info = DependencyInfo()
    __read_topics(info, topics_file)
    __read_events(info, events_file)
    info.finalize()
    return info
