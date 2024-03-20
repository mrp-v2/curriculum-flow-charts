from chart_builders.base import Base as ChartBuilder
from chart_builders.focus_topic import FocusTopic
from util.chart_context import ChartContext
from util.event import Event

from chart_builders.topic_by_event import TopicByEvent
from chart_builders.topic import Topic
from chart_builders.focus_event import FocusEvent
from chart_builders.full import Full


def __view_graph(chart_context: ChartContext, builder: ChartBuilder):
    """
    Creates a pdf for a graph and opens it.
    :param chart_context: The ChartContext to get the output path from.
    :param builder: The chart builder to draw and view.
    """
    builder.draw()
    graph = builder.finish()
    path = graph.view(filename=chart_context.get_chart_file(graph.name), directory=chart_context.output_dir,
                      cleanup=not chart_context.verbose_graph)
    print(f'Chart saved to {path}')


def topics_chart(context: ChartContext):
    """
    Draws a topic chart.
    :param context: The ChartContext to use to draw the chart.
    """
    builder = Topic(context)
    builder.label('Topic Dependencies')
    __view_graph(context, builder)


def topics_by_event_chart(context: ChartContext):
    """
    Draws a topic by event chart.
    :param context: The ChartContext to use to draw the chart.
    """
    builder = TopicByEvent(context)
    builder.label('Topic Dependencies By Event')
    __view_graph(context, builder)


def event_chart(context: ChartContext):
    """
    Draws an event chart.
    :param context: The ChartContext to use to draw the chart.
    """
    builder: FocusEvent = FocusEvent(context)
    builder.label(f'{context.focus_event} Relations')
    __view_graph(context, builder)


def topic_chart(context: ChartContext):
    builder: FocusTopic = FocusTopic(context)
    builder.label(f'{context.focus_topic} Relations')
    __view_graph(context, builder)


def full_chart(context: ChartContext):
    """
    Draws a full chart.
    :param context: The ChartContext to use to draw the chart.
    """
    builder = Full(context)
    builder.label('Full Course Dependencies')
    __view_graph(context, builder)
