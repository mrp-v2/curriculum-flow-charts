from argparse import ArgumentParser, FileType, Namespace
from pathlib import Path
from typing import Literal

from util import find_match
from util.chart_context import ChartContext
from util.chart_handler import event_chart, full_chart, topic_chart, topics_by_event_chart, topics_chart
from util.parse_dependency_info import read_info

ChartType = Literal['topics', 'topics_by_event', 'event', 'full', 'topic']


def main(args: Namespace):
    """
    Handles parsed command line arguments.
    """
    info = read_info(args.topics, args.events, args.info_level)
    output_dir = Path(args.output_dir) if args.output_dir else Path.cwd()
    flags = args.flags if args.flags else []
    if args.all_topics:
        topics_chart(ChartContext(info, output_dir, args.output_prefix, flags))
    if args.topics_by_event:
        topics_by_event_chart(ChartContext(info, output_dir, args.output_prefix, flags))
    for event_name in args.event if args.event else []:
        event = find_match(event_name, info.get_events)
        if event is None:
            print(f'Event query \'{event_name}\' was ambiguous. Try again with a different query.')
            return
        event_chart(ChartContext(info, output_dir, args.output_prefix, flags, focus_event=event))
    for topic_name in args.topic if args.topic else []:
        topic = find_match(topic_name, info.get_topics)
        if topic is None:
            print(f'Topic query \'{topic_name}\' was ambiguous. Try again with a different query.')
            return
        topic_chart(ChartContext(info, output_dir, args.output_prefix, flags, focus_topic=topic))
    if args.full:
        full_chart(ChartContext(info, output_dir, args.output_prefix, flags))


if __name__ == '__main__':
    parser = ArgumentParser(prog='Course Dependency Chart Maker')
    parser.add_argument('topics', type=FileType(),
                        help='''The path to a tsv file containing topic information. 
                        One topic per row - the first row is assumed to be a header and is ignored.
                        The first column is the topic name.
                        The second column is a semicolon seperated list of topics the topic depends on.
                        The third column is a description of the topic.''')
    parser.add_argument('events', type=FileType(),
                        help='''The path to a tsv file containing event information. One event per row - the first 
                        row is assumed to be a header and is ignored. The first column is ignored. It may contain 
                        extra information or be left empty. The second column specifies the name of the event. The 
                        name should include an event type (lecture, lab, homework (hw), or project) and an event id 
                        starting with the unit number, followed by a letter (e.g. '1a', '4c'). Events are 
                        chronologically ordered by unit, then the alphabetical part of their id
                        (Example event name: 'Lecture 3b - Learning stuff').
                        Events may have the alphabetical part of their id omitted,
                        if they are the only event without an id of their type within their unit.
                        Extra parts of the event name should come after a hyphen. 
                        The third column is a semicolon seperated list of topics taught in the event. 
                        The fourth column is a semicolon seperated list of topics required for the event.''')
    parser.add_argument('--output-dir', default='output', help='''Specifies a directory to save output files to.
                        Defaults to \'./output/\'.''')
    parser.add_argument('--output-prefix', default='', help='''Specifies a prefix to prepend to output file names.''')
    parser.add_argument('-d', '--debug-rank', dest='flags', action='append_const', const='debug_rank',
                        help='''Activates drawing debug information relating to rank in graphs that support it.''')
    parser.add_argument('-i', '--info-level', default='warning', choices=['info', 'warning', 'error', 'silent'],
                        help='''Specifies the upper severity limit of what information to print while parsing the 
                        topics and events. Defaults to \'warning\'.''')
    charts_options = parser.add_argument_group('charts options', 'zero or more of the following charts:')
    charts_options.add_argument('--all-topics', action='store_true',
                                help='''Creates a chart showing what topics build off of each topic.''')
    charts_options.add_argument('--topics-by-event', action='store_true',
                                help='''Creates a chart showing what topics each event teaches,
                                and what topics build off of each topic.''')
    charts_options.add_argument('-e', '--event', action='append', help='''Creates a chart showing the specified event, 
    its topics taught and required, as well as all other events and topics that relate to that event.''')
    charts_options.add_argument('--topic', action='append', help='''Creates a chart showing the all the places the 
    specified topic is taught or required.''')
    charts_options.add_argument('-f', '--full', action='store_true', help='''Creates a chart showing all events,
    their topics taught and required, as well as all relations between events and topics.''')
    main(parser.parse_args())
