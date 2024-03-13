from typing import Literal

from util.event import Event

Side = Literal['taught', 'required']
"""The different sides a topic can have under an event. Either 'taught' or 'required'."""


def qualify(topic: str, parent_event: Event) -> str:
    """
    Qualifies a topic name with its unit, event, and optionally a modifier.
    Used to differentiate between different nodes for the same topic within different sub-graphs.
    :param topic: The topic to qualify.
    :param parent_event: The event to qualify the topic under.
    :return: The qualified name of the topic.
    """
    return f"{parent_event.name}${topic}"
