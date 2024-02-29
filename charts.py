from pathlib import Path

from graphviz import Digraph

from util import DependencyInfo, Event, qualify

from chart_builder import TopicChartBuilder, EventChartBuilder, ChartBuilder


def topic_chart(info: DependencyInfo, file_out: Path):
    builder = TopicChartBuilder(info, file_out)
    builder.label('Topic Dependencies')

    for topic in info.topics:
        builder.draw_topic_and_dependencies(topic)

    builder.finish().view()


def topic_by_event_chart(info: DependencyInfo, file_out: Path):
    builder = EventChartBuilder(info, file_out)
    builder.label('Topic Dependencies By Event')

    for event in info.events:
        builder.draw_event_topics_and_dependencies(event)

    builder.finish().view()


def event_chart(info: DependencyInfo, file_out: Path, focus_event: Event):
    """
    Makes a graph showing the dependencies and dependents (recursively) of a specific event.
    Dependencies are based on the topics required for the event,
    and dependents are based on the topics taught in the event.
    """
    builder: ChartBuilder = ChartBuilder(info, file_out)
    builder.label(f'{focus_event.unit}, {focus_event.name} Dependencies')
    builder.draw_event_relations(focus_event)
    builder.finish().view()


def full_chart(info: DependencyInfo, file_out: Path):
    builder = ChartBuilder(info, file_out)
    builder.label('Full Course Dependencies')
    for event in info.events:
        builder.draw_event_relations(event)
    builder.finish().view()
