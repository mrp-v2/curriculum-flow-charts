from graphviz import Digraph

from util.chart_context import ChartContext
from util.event import Event

from chart_builders.topic_by_event import TopicByEventChartBuilder
from chart_builders.topic import TopicChartBuilder
from chart_builders.event import EventChartBuilder
from chart_builders.full import FullChartBuilder


def __view_graph(chart_context: ChartContext, graph: Digraph):
    """
    Creates a pdf for a graph and opens it.
    :param chart_context: The ChartContext to get the output path from.
    :param graph: The graph to view.
    """
    path = graph.view(filename=chart_context.get_chart_file(graph.name), directory=chart_context.output_dir,
                      cleanup=not chart_context.verbose_graph)
    print(f'Chart saved to {path}')


def topic_chart(context: ChartContext):
    """
    Draws a topic chart.
    :param context: The ChartContext to use to draw the chart.
    """
    builder = TopicChartBuilder(context)
    builder.label('Topic Dependencies')

    for topic in context.info.topics:
        builder.draw_topic_and_dependencies(topic)

    __view_graph(context, builder.finish())


def topic_by_event_chart(context: ChartContext):
    """
    Draws a topic by event chart.
    :param context: The ChartContext to use to draw the chart.
    """
    builder = TopicByEventChartBuilder(context)
    builder.label('Topic Dependencies By Event')

    for event in context.info.events:
        builder.draw_event_topics_and_dependencies(event)

    __view_graph(context, builder.finish())


def event_chart(context: ChartContext):
    """
    Draws an event chart.
    :param context: The ChartContext to use to draw the chart.
    """
    builder: EventChartBuilder = EventChartBuilder(context)
    builder.label(f'{context.focus_event.name} Dependencies')
    builder.draw()
    __view_graph(context, builder.finish())


def full_chart(context: ChartContext):
    """
    Draws a full chart.
    :param context: The ChartContext to use to draw the chart.
    """
    builder = FullChartBuilder(context)
    builder.label('Full Course Dependencies')
    builder.draw_full()
    __view_graph(context, builder.finish())
