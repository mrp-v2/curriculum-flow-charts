import sys

import os.path

from util import Event, read_info

from charts import topic_dependencies, topic_event_dependencies, full_event_dependencies, specific_event_dependencies, full_chart


def main(topics_file: str, events_file: str, args: list[str]):
    info = read_info(topics_file, events_file)
    output_path: str = ''
    focus_event: str = ''
    for flag in args:
        if flag.startswith('--output='):
            output_path = flag[len('--output='):]
        elif flag.startswith('--focus-event='):
            focus_event = flag[len('--focus-event='):]
    if '--topic-dependencies' in args:
        topic_dependencies(info, f'{output_path}topic-dependencies')
    if '--topic-event-dependencies' in args:
        topic_event_dependencies(info, f'{output_path}event-topic-dependencies')
    if '--event-dependencies' in args:
        if focus_event:
            unit, name = focus_event.split('$')
            event: Event | None = None
            for test in info.events:
                if test.unit == unit and test.name == name:
                    event = test
                    break
            if event is None:
                print(f'Unrecognized event: {focus_event}')
            else:
                specific_event_dependencies(info, f'{output_path}{unit}_{name}event-dependencies', event)
        else:
            full_event_dependencies(info, f'{output_path}full-event-dependencies')
    if '--full' in args:
        full_chart(info, f'{output_path}full')


if __name__ == '__main__':
    if '--help' in sys.argv:
        print('make_flow_chart takes at least three arguments:\n'
              '1. The path to a tsv file containing topic information\n'
              '     One topic per row - the first row is assumed to be a header and is ignored.\n'
              '     The first column is the topic name.\n'
              '     The second column is a semicolon seperated list of topics the topic depends on.\n'
              '     The third column is a description of the topic.\n'
              '2. The path to a tsv file containing event information\n'
              '     One event per row - the first row is assumed to be a header and is ignored.\n'
              '     Events are assumed to be in chronological order first to last top to bottom.\n'
              '     The first column specifies the unit. After a unit is specified, it is assumed\n'
              '     to be the same in all following events until another unit is specified.\n'
              '     The second column is a semicolon seperated list of topics taught in the event.\n'
              '     The third column is a semicolon seperated list of topics required for the event.\n'
              '3. One or more of the following flags:\n'
              '  --output=<path>                        Specifies where to save output files to. Can be a directory,\n'
              '                                           and can include a prefix for any produced files.\n'
              '                                           Defaults to the current working directory.\n'
              '  --topic-dependencies                   Creates a chart showing what topics build off of each topic.\n'
              '                                           Saves to f\'{output_path}topic-dependencies\'\n'
              '  --topic-event-dependencies             Creates a chart showing what topics each event teaches,\n'
              '                                           and what topics build off of each topic\n'
              '                                           Saves to f\'{output_path}event-topic-dependencies\'\n'
              '  --event-dependencies                   Creates a chart showing what topics each event teaches,\n'
              '                                           and which events require each topic.\n'
              '                                           Saves to f\'{output_path}full-event-dependencies\'\n'
              '  --focus-event=<unit>$<event>           When used in conjunction with --event-dependencies,\n'
              '                                           only shows topics required for the specified event.\n'
              '                                           Saves to f\'{output_path}{unit}_{event}-dependencies\'\n')
    elif len(sys.argv) < 3:
        print('make_flow_chart requires at least three arguments')
        exit(1)
    elif os.path.isfile(sys.argv[1]) and os.path.isfile(sys.argv[2]):
        main(sys.argv[1], sys.argv[2], sys.argv[3:])
    else:
        if not os.path.isfile(sys.argv[1]):
            print(f'Invalid file: {sys.argv[1]}')
        if not os.path.isfile(sys.argv[2]):
            print(f'Invalid file: {sys.argv[2]}')
        exit(2)
