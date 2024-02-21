import sys

import os.path

from util import Event, read_info

from basic_charts import topic_dependencies, topic_event_dependencies, full_event_dependencies

from specific_event_dependency_chart import specific_event_dependencies


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


if __name__ == '__main__':
    if '--help' in sys.argv:
        print('make_flow_chart takes at least three arguments:\n'
              '1. The path to a tsv file containing topic information\n'
              '2. The path to a tsv file containing event information\n'
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
