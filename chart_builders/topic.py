from chart_builders.base_chart_builder import BaseChartBuilder
from util.chart_context import ChartContext


class TopicChartBuilder(BaseChartBuilder):
    """Draws charts using only topics."""

    def __init__(self, context: ChartContext):
        super().__init__(context, 'topics')

    def draw_topic_and_dependencies(self, topic: str):
        """
        Draws a topic, and edges connecting it to its dependencies.
        """
        self._draw_node(topic, topic)
        for dependency in self._context.info.topics[topic].dependencies:
            self._draw_edge(dependency, topic)
