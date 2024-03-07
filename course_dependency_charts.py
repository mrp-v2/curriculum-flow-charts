from pathlib import Path

from argparse import ArgumentParser, FileType, Namespace

from util import Event

from chart_handler import topic_chart, topic_by_event_chart, event_chart, full_chart
from util.chart_context import ChartContext
from util.parse_dependency_info import read_info


def main(args: Namespace):
    info = read_info(args.topics_file, args.events_file)
    output_dir = Path(args.output_dir) if args.output_dir else Path.cwd()
    context = ChartContext(info, output_dir, args.output_prefix, args.flags if args.flags else [])
    if args.topics:
        topic_chart(context)
    if args.topics_by_event:
        topic_by_event_chart(context)
    if args.event:
        unit, name = args.event.split('$')
        event: Event | None = None
        for test in info.events:
            if test.unit == unit and test.name == name:
                event = test
                break
        if event is None:
            print(f'Unrecognized event: {args.event}')
        else:
            event_chart(context, event)
    if args.full:
        full_chart(context)


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
    Events are assumed to be in chronological order first to last top to bottom.
    The first column specifies the unit number (e.g. 'Unit 3'). After a unit is specified, it is assumed
    to be the same in all following events until another unit is specified.
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
    options.add_argument('-full', action='store_true', help='''Creates a chart showing all events,
    their topics taught and required, as well as all relations between events and topics.''')
    main(parser.parse_args())
