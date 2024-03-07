from typing import Literal

from util.event import Event

Side = Literal['taught', 'required']


def qualify(topic: str, parent_event: Event, modifier: Side = None) -> str:
    return f"{parent_event.unit}${parent_event.name}${'' if modifier is None else f'{modifier}$'}{topic}"
