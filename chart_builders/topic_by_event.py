from graphviz import Digraph

from chart_builders.base_chart_builder import BaseChartBuilder
from util import Event, qualify
from util.chart_context import ChartContext


class TopicByEventChartBuilder(BaseChartBuilder):
    """Draws charts focusing on topics, but grouping topics by event."""

    def __init__(self, context: ChartContext):
        super().__init__(context, 'topics_by_event')
        self._event_graphs: dict[Event, Digraph] = {}
        """Stores the sub-graphs for each event."""

    def __draw_topic(self, topic: str, event: Event) -> str:
        if event not in self._event_graphs:
            self._event_graphs[event] = Digraph(f'{event.unit}${event.name}')
            self._event_graphs[event].attr(cluster='True')
            self._event_graphs[event].attr(label=event.name)
        qualified_name = qualify(topic, event)
        self._draw_node(qualified_name, topic, self._event_graphs[event])
        return qualified_name

    def draw_event_topics_and_dependencies(self, event: Event):
        for topic in event.topics_taught:
            qualified_name = self.__draw_topic(topic, event)
            last_taught_time = self._info.get_most_recent_taught_time(event, topic)
            if last_taught_time:
                self._draw_edge(qualify(topic, last_taught_time), qualified_name)
            for dependency in self._info.topics[topic].dependencies:
                dependency_taught_time = self._info.get_most_recent_taught_time(event, dependency, True)
                self._draw_edge(qualify(dependency, dependency_taught_time), qualified_name)

    def finish(self):
        for event in self._event_graphs:
            self._graph.subgraph(self._event_graphs[event])
        return super().finish()
