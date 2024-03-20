from chart_builders.event_base import EventBase
from util import Event as EventObj
from util.chart_context import ChartContext
from util.topic import Topic, get_dependent_topics


class Event(EventBase):
    """
    Draws charts that focus on a single event, drawing all things related to that event.
    """

    def __init__(self, context: ChartContext, chart_name: str = None):
        """
        :param context: The ChartContext to use for this builder.
        :param chart_name: The name of this chart. Defaults to the event name
        """
        super().__init__(context, chart_name if chart_name else context.focus_event.name)

    def _draw_event(self, event: EventObj, start_rank: int) -> int | None:
        max_rank: int | None = None
        if event == self._context.focus_event:
            rank = self._draw_focus_event(event, start_rank)
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

    def _draw_focus_event(self, event: EventObj, start_rank: int):
        max_rank: int | None = None
        for topic in event.get_all_topics():
            if topic in event.topics_taught:
                rank = self._draw_topic_and_dependencies(topic, event, start_rank)
                if max_rank is None or rank > max_rank:
                    max_rank = rank
            else:
                head = self._draw_topic(topic, event)
                rank = self._draw_rank_edge(head, start_rank, False)
                if max_rank is None or rank > max_rank:
                    max_rank = rank
                tail = self._get_tail_node(topic, event, False)
                self._draw_edge(tail, head, constraint='false')
                self._latest_required_times[topic] = event, head
        return max_rank

    def _draw_post_focus_event(self, event: EventObj, start_rank: int) -> int:
        max_rank: int | None = None
        for topic in get_dependent_topics(self._context.focus_event.topics_taught, event.get_all_topics()):
            if topic in event.topics_taught:
                def predicate(dep: Topic):
                    return dep.is_dependent_of_depth(self._context.focus_event.topics_taught)

                rank = self._draw_topic_and_dependencies(topic, event, start_rank, predicate)
                if max_rank is None or rank > max_rank:
                    max_rank = rank
            else:
                head = self._draw_topic(topic, event)
                rank = self._draw_rank_edge(head, start_rank, False)
                if max_rank is None or rank > max_rank:
                    max_rank = rank
                tail = self._get_tail_node(topic, event, False)
                self._draw_edge(tail, head, constraint='false')
                self._latest_required_times[topic] = event, head
        return max_rank

    def _draw_pre_focus_event(self, event: EventObj, start_rank: int) -> int | None:
        max_rank: int | None = None
        for topic in event.topics_taught:
            if topic.is_dependency_of_depth(self._context.focus_event.get_all_topics()):
                rank = self._draw_topic_and_dependencies(topic, event, start_rank)
                if max_rank is None or rank > max_rank:
                    max_rank = rank
        return max_rank
