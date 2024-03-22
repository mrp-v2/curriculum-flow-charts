from chart_builders.event_base import EventBase
from util import Topic
from util.chart_context import ChartContext


class FocusTopic(EventBase):
    """
    Focuses on a single `Topic`, drawing all things related to it.
    """

    def __init__(self, context: ChartContext):
        super().__init__(context, context.focus_topic.name)

    def __topic_taught_predicate(self, topic: Topic):
        """
        The predicate to use to decide to draw a topic being taught.
        """
        return self.__topic_required_predicate(topic) or self._context.focus_topic.is_dependent_on(topic)

    def __topic_required_predicate(self, topic: Topic):
        """
        The predicate to use to decide to draw a topic being required.
        """
        return topic == self._context.focus_topic or topic.is_dependent_on(self._context.focus_topic)

    def _draw_event(self, event, start_rank) -> int | None:
        max_rank: int | None = None
        for topic in event.get_all_topics():
            if topic in event.topics_taught:
                if self.__topic_taught_predicate(topic):
                    rank = self._draw_topic_and_dependencies(topic, event, start_rank, self.__topic_taught_predicate)
                    if rank is not None and (max_rank is None or rank > max_rank):
                        max_rank = rank
            elif self.__topic_required_predicate(topic):
                rank = self._draw_required_topic(topic, event, start_rank)
                if max_rank is None or rank > max_rank:
                    max_rank = rank
        return max_rank
