from chart_builders.event_base import EventBase
from util import Event as EventObj
from util.chart_context import ChartContext
from util.topic import Topic, get_dependent_topics


class FocusEvent(EventBase):
    """
    Focuses on a single event, drawing all things related to that event.
    """

    def __init__(self, context: ChartContext):
        """
        :param context: The ChartContext to use for this builder.
        """
        super().__init__(context, context.focus_event.name)

    def _draw_event(self, event: EventObj, start_rank: int) -> int | None:
        max_rank: int | None = None
        if event == self._context.focus_event:
            rank = self._draw_event_full(event, start_rank)
            if rank is not None and (max_rank is None or rank > max_rank):
                max_rank = rank
        elif event < self._context.focus_event:
            rank = self._draw_pre_focus_event(event, start_rank)
            if rank is not None and (max_rank is None or rank > max_rank):
                max_rank = rank
        elif event > self._context.focus_event and not self._context.focus_event.topics_taught:
            return None
        else:
            rank = self._draw_post_focus_event(event, start_rank)
            if max_rank is None or rank > max_rank:
                max_rank = rank
        return max_rank

    def _draw_post_focus_event(self, event: EventObj, start_rank: int) -> int:
        """
        Draws an event in the same way as `draw_event_full`,
         but only draws topic that are dependent on a topic taught by the focus event.
        """
        max_rank: int | None = None
        for topic in get_dependent_topics(self._context.focus_event.topics_taught, event.get_all_topics()):
            if topic in event.topics_taught:
                def predicate(dep: Topic):
                    return dep.is_dependent_of_depth(self._context.focus_event.topics_taught)

                rank = self._draw_topic_and_dependencies(topic, event, start_rank, predicate)
                if max_rank is None or rank > max_rank:
                    max_rank = rank
            else:
                rank = self._draw_required_topic(topic, event, start_rank)
                if max_rank is None or rank > max_rank:
                    max_rank = rank
        return max_rank

    def _draw_pre_focus_event(self, event: EventObj, start_rank: int) -> int | None:
        """
        Draws an event in the same way as `draw_event_full`,
        but only draws topics that are taught and are dependencies of a topic in the focus event.
        """
        max_rank: int | None = None
        for topic in event.topics_taught:
            if topic.is_dependency_of_depth(self._context.focus_event.get_all_topics()):
                rank = self._draw_topic_and_dependencies(topic, event, start_rank)
                if max_rank is None or rank > max_rank:
                    max_rank = rank
        return max_rank
