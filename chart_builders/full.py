from chart_builders.event_base import EventBase
from util import Event as EventObj
from util.chart_context import ChartContext


class Full(EventBase):
    """
    Draws everything.
    """

    def __init__(self, context: ChartContext):
        super().__init__(context, 'full')

    def _draw_event(self, event: EventObj, start_rank: int) -> int:
        return self._draw_event_full(event, start_rank)
