from graphviz import Digraph

from chart_builders.event_base import EventBase
from util import Event, qualify, Topic
from util.chart_context import ChartContext


class TopicByEvent(EventBase):
    """Draws all topics taught, grouped by event."""

    def _draw_event(self, event, start_rank) -> int | None:
        max_rank: int | None = None
        for topic in event.topics_taught:
            rank = self._draw_topic_and_dependencies(topic, event, start_rank)
            if max_rank is None or rank > max_rank:
                max_rank = rank
        return max_rank

    def __init__(self, context: ChartContext):
        """
        :param context: The ChartContext to use for this builder.
        """
        super().__init__(context, 'topics_by_event')
