from chart_builders.base import Base
from util.chart_context import ChartContext
from util.topic import Topic as TopicObj


class Topic(Base):
    """Draws charts using only topics."""

    def __init__(self, context: ChartContext):
        super().__init__(context, 'topics')

    def draw_topic_and_dependencies(self, topic: TopicObj):
        """
        Draws a topic, and edges connecting it to its dependencies.
        """
        self._draw_node(topic.name, topic.name)
        for dependency in topic.dependencies:
            self._draw_edge(dependency.name, topic.name)
