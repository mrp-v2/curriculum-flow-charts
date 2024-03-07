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


EventType = Literal['lecture', 'lab', 'homework', 'project']


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
