from chart_builders.base import Base
from util.chart_context import ChartContext
from util.topic import Topic as TopicObj


class Topic(Base):
    """Draws all topics taught."""

    def draw(self):
        for topic in self._context.info.get_topics():
            self.__draw_topic_and_dependencies(topic)

    def __init__(self, context: ChartContext):
        super().__init__(context, 'topics')

    def __draw_topic_and_dependencies(self, topic: TopicObj):
        """
        Draws a topic, and edges connecting it to its dependencies.
        """
        self._draw_node(topic.name, topic.name)
        for dependency in topic.dependencies:
            self._draw_edge(dependency.name, topic.name)
