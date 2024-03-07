from util.chart_context import ChartContext
from util.event import Event

from chart_builders.chart_builder import TopicChartBuilder, TopicByEventChartBuilder, EventChartBuilder, \
    FullChartBuilder


def topic_chart(context: ChartContext):
    builder = TopicChartBuilder(context)
    builder.label('Topic Dependencies')

    for topic in context.info.topics:
        builder.draw_topic_and_dependencies(topic)

    builder.finish().view()


def topic_by_event_chart(context: ChartContext):
    builder = TopicByEventChartBuilder(context)
    builder.label('Topic Dependencies By Event')

    for event in context.info.events:
        builder.draw_event_topics_and_dependencies(event)

    builder.finish().view()


def event_chart(context: ChartContext, focus_event: Event):
    """
    Makes a graph showing the dependencies and dependents (recursively) of a specific event.
    Dependencies are based on the topics required for the event,
    and dependents are based on the topics taught in the event.
    """
    builder: EventChartBuilder = EventChartBuilder(context, focus_event)
    builder.label(f'{focus_event.unit}, {focus_event.name} Dependencies')
    builder.draw_event_relations(focus_event)
    builder.finish().view()


def full_chart(context: ChartContext):
    builder = FullChartBuilder(context)
    builder.label('Full Course Dependencies')
    builder.draw_full()
    builder.finish().view()
