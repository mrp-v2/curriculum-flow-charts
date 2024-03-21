from typing import Literal, TypeVar

from util.event import Event
from util.topic import Topic

Side = Literal['taught', 'required']
"""The different sides a topic can have under an event. Either 'taught' or 'required'."""


def qualify(_topic: Topic, parent_event: Event) -> str:
    """
    Qualifies a topic name with its unit, event, and optionally a modifier.
    Used to differentiate between different nodes for the same topic within different sub-graphs.
    :param _topic: The topic to qualify.
    :param parent_event: The event to qualify the topic under.
    :return: The qualified name of the topic.
    """
    return f"{parent_event.name}${_topic}"


T = TypeVar('T')


def find_match(pattern: str, item_getter: Callable[[], Iterable[T]]) -> T | None:
    items = item_getter()
    matches = [item for item in items if pattern == str(item)]
    if len(matches) == 1:
        return matches[0]
    items = item_getter()
    matches = [item for item in items if pattern.lower() == str(item).lower()]
    if len(matches) == 1:
        return matches[0]
    items = item_getter()
    matches = [item for item in items if pattern.lower() in str(item).lower()]
    return matches[0] if len(matches) == 1 else None
