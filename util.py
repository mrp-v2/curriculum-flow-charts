import csv
from io import IOBase
from typing import Literal

EventType = Literal['lecture', 'lab', 'homework', 'project']
Side = Literal['taught', 'required']


def _decide_event_type_and_number(name: str) -> tuple[EventType, int, str | None]:
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
        event_type = 'lecture'
    elif lab:
        if homework or project:
            raise ValueError(f'Cannot distinguish event type of {name}')
        event_type = 'lab'
    elif homework:
        if project:
            raise ValueError(f'Cannot distinguish event type of {name}')
        event_type = 'homework'
    elif project:
        event_type = 'project'
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
    event_id = short_name[number_end] if short_name[number_end].strip() else None
    if event_id is None:
        if event_type != 'project':
            raise ValueError(f'Event {name} is missing an id')
    return event_type, unit_number, event_id


def _event_type_less_than(type1: EventType, type2: EventType) -> bool:
    if type1 == 'lecture':
        return type2 != 'lecture'
    if type1 == 'lab':
        return type2 != 'lecture' and type2 != 'lab'
    if type1 == 'homework':
        return type2 == 'project'
    return False


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
        self.next: Event | None = None
        event_type, unit_number, event_id = _decide_event_type_and_number(self.name)
        self.event_type: EventType = event_type
        self.unit_number: int = unit_number
        self.event_id: str | None = event_id

    def __str__(self):
        return self.name

    def __lt__(self, other) -> bool:
        if isinstance(other, Event):
            event: Event = other
            if self.unit_number < event.unit_number:
                return True
            if self.unit_number > event.unit_number:
                return False
            if event.event_id is None:
                return self.event_id is not None
            if self.event_id is None:
                return False
            if self.event_id < event.event_id:
                return True
            if self.event_id > event.event_id:
                return False
            return _event_type_less_than(self.event_type, event.event_type)

        return False


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


def qualify(topic: str, event: Event, modifier: Side = None) -> str:
    return f"{event.unit}${event.name}${'' if modifier is None else f'{modifier}$'}{topic}"


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
