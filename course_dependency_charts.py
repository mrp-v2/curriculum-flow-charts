from argparse import ArgumentParser, FileType, Namespace
from pathlib import Path
from typing import Literal

from util.chart_handler import topics_chart, topics_by_event_chart, event_chart, full_chart, topic_chart
from util import Event, Topic, find_match
from util.chart_context import ChartContext
from util.parse_dependency_info import read_info

ChartType = Literal['topics', 'topics_by_event', 'event', 'full', 'topic']


def draw_chart(context: ChartContext, chart_type: ChartType):
    """
    Draws the ChartType specified by chart_type and using the given ChartContext.
    :param context: The ChartContext to use for drawing the chart.
    :param chart_type: The ChartType to draw.
    """
    match chart_type:
        case 'topics':
            topics_chart(context)
        case 'topics_by_event':
            topics_by_event_chart(context)
        case 'event':
            event_chart(context)
        case 'full':
            full_chart(context)
        case 'topic':
            topic_chart(context)


def __main(args: Namespace):
    """Handles the parsed command line arguments."""
    info = read_info(args.topics_file, args.events_file)
    chart_type: ChartType | None = None
    event: Event | None = None
    topic: Topic | None = None
    if args.topics:
        chart_type = 'topics'
    if args.topics_by_event:
        chart_type = 'topics_by_event'
    if args.event:
        chart_type = 'event'
        event = find_match(args.event, info.get_events)
        if event is None:
            print(f'Event query \'{args.event}\' was ambiguous. Try again with a different query.')
            return
    if args.topic:
        chart_type = 'topic'
        topic = find_match(args.topic, info.get_topics)
        if topic is None:
            print(f'Topic query \'{args.topic}\' was ambiguous. Try again with a different query.')
            return
    if args.full:
        chart_type = 'full'
    output_dir = Path(args.output_dir) if args.output_dir else Path.cwd()
    context = ChartContext(info, output_dir, args.output_prefix, args.flags if args.flags else [], event, topic)
    if chart_type:
        draw_chart(context, chart_type)


if __name__ == '__main__':
    parser = ArgumentParser(prog='Course Dependency Chart Maker')
    parser.add_argument('topics_file', type=FileType(),
                        help='''The path to a tsv file containing topic information. 
    One topic per row - the first row is assumed to be a header and is ignored.
    The first column is the topic name.
    The second column is a semicolon seperated list of topics the topic depends on.
    The third column is a description of the topic.''')
    parser.add_argument('events_file', type=FileType(),
                        help='''The path to a tsv file containing event information.
    One event per row - the first row is assumed to be a header and is ignored.
    The first column is ignored. It may contain extra information or be left empty.
    The second column specifies the name of the event. 
    The name should include an event type (lecture, lab, homework (hw), or project) and an event id starting with the 
    unit number, followed by a letter (e.g. '1a', '4c').
    Events are chronologically ordered by unit, then the alphabetical part of their id
    (Example event name: 'Lecture 3b - Learning stuff'). 
    Projects may have the alphabetical part of their id omitted, and there may only be one project in each unit.
    Extra parts of the event name should come after a hyphen.
    The third column is a semicolon seperated list of topics taught in the event.
    The fourth column is a semicolon seperated list of topics required for the event.''')
    parser.add_argument('-output_dir', help='''Specifies a directory to save output files to.
    Defaults to the current working directory.''')
    parser.add_argument('-output_prefix', default='', help='''Specifies a prefix to prepend to output file names.''')
    parser.add_argument('-verbose_graph', dest='flags', action='append_const', const='verbose_graph',
                        help='''Activates drawing debug information in graphs that support it.''')
    descriptive_options = parser.add_argument_group('charts options', 'one of the following charts:')
    options = descriptive_options.add_mutually_exclusive_group(required=True)
    options.add_argument('-topics', action='store_true',
                         help='''Creates a chart showing what topics build off of each topic.''')
    options.add_argument('-topics_by_event', action='store_true',
                         help='''Creates a chart showing what topics each event teaches,
    and what topics build off of each topic.''')
    options.add_argument('-event', help='''Creates a chart showing the specified event,
    its topics taught and required, as well as all other events and topics that relate to that event.''')
    options.add_argument('-topic', help='''Creates a chart showing the all the places the specified topic
    is taught or required.''')
    options.add_argument('-full', action='store_true', help='''Creates a chart showing all events,
    their topics taught and required, as well as all relations between events and topics.''')
    __main(parser.parse_args())
