from chart_builders.event import EventChartBuilder
from util import Event
from util.chart_context import ChartContext


class FullChartBuilder(EventChartBuilder):
    def __init__(self, context: ChartContext):
        super().__init__(context, chart_name='full')

    def _draw_event_full(self, event, start_rank) -> int:
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

    def _draw_event(self, event: Event, start_rank: int) -> int:
        return self._draw_event_full(event, start_rank)
