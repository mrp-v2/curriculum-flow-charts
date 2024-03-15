from graphviz import Digraph

from chart_builders.base_chart_builder import BaseChartBuilder
from util import Event, qualify
from util.chart_context import ChartContext


class TopicByEventChartBuilder(BaseChartBuilder):
    """Draws charts focusing on topics, but grouping topics by event."""

    def __init__(self, context: ChartContext):
        """
        :param context: The ChartContext to use for this builder.
        """
        super().__init__(context, 'topics_by_event')
        self._event_graphs: dict[Event, Digraph] = {}
        """Stores the sub-graphs for each event."""

    def __draw_topic(self, topic: str, event: Event) -> str:
        """
        Draws a topic.
        :param topic: The topic to draw.
        :param event: The event to draw the topic under.
        :return: The qualified name of the topic node.
        """
        if event not in self._event_graphs:
            self._event_graphs[event] = Digraph(f'Unit {event.unit}${event.name}')
            self._event_graphs[event].attr(cluster='True')
            self._event_graphs[event].attr(label=event.name)
        qualified_name = qualify(topic, event)
        self._draw_node(qualified_name, topic, self._event_graphs[event])
        return qualified_name

    def draw_event_topics_and_dependencies(self, event: Event):
        """
        Draws the topics taught in an event and the dependencies of those topics.
        :param event: The event to use.
        """
        for topic in event.topics_taught:
            qualified_name = self.__draw_topic(topic.name, event)
            last_taught_time = self._context.info.get_most_recent_taught_time(event, topic)
            if last_taught_time:
                self._draw_edge(qualify(topic.name, last_taught_time), qualified_name)
            for dependency in topic.dependencies:
                dependency_taught_time = self._context.info.get_most_recent_taught_time(event, dependency, True)
                self._draw_edge(qualify(dependency.name, dependency_taught_time), qualified_name)

    def finish(self):
        for sub_graph in self._event_graphs.values():
            self._graph.subgraph(sub_graph)
        return super().finish()
