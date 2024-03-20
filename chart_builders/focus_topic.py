from chart_builders.event_base import EventBase
from util import Topic
from util.chart_context import ChartContext


class FocusTopic(EventBase):

    def __init__(self, context: ChartContext):
        super().__init__(context, context.focus_topic.name)

    def __topic_predicate(self, topic: Topic):
        return topic == self._context.focus_topic

    def _draw_event(self, event, start_rank) -> int | None:
        max_rank: int | None = None
        for topic in event.get_all_topics():
            if self.__topic_predicate(topic):
                if topic in event.topics_taught:
                    self._draw_topic_and_dependencies(topic, event, start_rank, self.__topic_predicate)
                    pass  # TODO
                else:
                    pass  # TODO
        return max_rank
