import csv
import sys

import os.path

from graphviz import Digraph


class Event:
    """
    Stores information about an event: its unit, name, the topics taught, and the topics required
    """

    def __init__(self, unit: str, name: str, topics_taught: list[str], topics_required: list[str]):
        self.unit: str = unit
        self.name: str = name
        self.topics_taught: list[str] = topics_taught
        self.topics_required: list[str] = topics_required

    def __str__(self):
        return self.name


class Topic:
    """
    Stores information about a topic: its name, dependencies, and description
    """

    def __init__(self, name: str, dependencies: list[str], description: str):
        self.name: str = name
        self.dependencies: list[str] = dependencies
        self.description: str = description

    def __str__(self):
        return self.name


class DependencyInfo:
    """
    Stores information about the course topics and events
    """

    def __init__(self):
        self.events: list[Event] = []
        # Stores Topics by their name
        self.topics: dict[str, Topic] = {}

    def is_topic_dependent_on(self, topic: str, dependency: str) -> bool:
        """
        Returns True if dependency is a dependency - or a sub-dependency - of topic.
        """
        try:
            topic = self.topics[topic]
        except KeyError:
            return False
        if dependency in topic.dependencies:
            return True
        for test_dependency in topic.dependencies:
            if self.is_topic_dependent_on(test_dependency, dependency):
                return True
        return False

    def finalize(self):
        """
        For each event, removes required topics that are dependencies of other required topics for that event.
        For each topic, removes dependencies that are dependencies of other dependencies for that topic.
        Prints information regarding removals to the console.
        """
        for topic in self.topics.values():
            dependencies = topic.dependencies
            i: int = 0
            while i < len(dependencies):
                for other in dependencies:
                    if other == dependencies[i]:
                        continue
                    if self.is_topic_dependent_on(other, dependencies[i]):
                        print(f'INFO: ignoring dependency {dependencies[i]} from {topic} because '
                              f'it is a dependency of {other}, which is also a dependency of {topic}')
                        dependencies.remove(dependencies[i])
                        i -= 1
                        break
                i += 1
        unused_topics = [item for item in self.topics]
        for event in self.events:
            required = event.topics_required
            i: int = 0
            while i < len(required):
                for other in required:
                    if other == required[i]:
                        continue
                    if self.is_topic_dependent_on(other, required[i]):
                        print(f'INFO: ignoring required topic {required[i]} from {event} because '
                              f'it is a dependency of {other}, which is also required by {event}')
                        required.remove(required[i])
                        i -= 1
                        break
                i += 1
            for topic in event.topics_taught:
                if topic in unused_topics:
                    unused_topics.remove(topic)
            for topic in required:
                if topic in unused_topics:
                    unused_topics.remove(topic)
        for topic in unused_topics:
            print(f'INFO: topic \'{topic}\' is not used in any event')

    def get_most_recent_taught_time(self, start: Event, topic: str, include_start: bool = False) -> Event | None:
        index: int = self.events.index(start)
        if not include_start:
            index -= 1
        while topic not in self.events[index].topics_taught and index >= 0:
            index -= 1
        if index == -1:
            return None
        return self.events[index]


def cluster(topic: str) -> str:
    return f'cluster_{topic}'


def qualify(topic: str, event: Event, modifier: None | str = None) -> str:
    return f"{event.unit}${event.name}${'' if modifier is None else f'{modifier}$'}{topic}"


def make_topic_dependency_chart(info: DependencyInfo, filename_out: str):
    graph = Digraph(filename_out)
    graph.attr(label='Topic Dependencies')

    for topic in info.topics.values():
        graph.node(topic.name)
        for dependency in topic.dependencies:
            graph.edge(dependency, topic.name)
    graph.view()


def make_event_topic_dependency_chart(info: DependencyInfo, filename_out: str):
    graph = Digraph(filename_out)
    graph.attr(label='Event Based Topic Dependencies')

    for event in info.events:
        sub_graph = Digraph(cluster(event.name))
        sub_graph.attr(label=event.name)
        for topic in event.topics_taught:
            sub_graph.node(qualify(topic, event), label=topic)
            taught_time = info.get_most_recent_taught_time(event, topic)
            if taught_time:
                graph.edge(qualify(topic, taught_time), qualify(topic, event))
            for dependency in info.topics[topic].dependencies:
                dependency_taught_time = info.get_most_recent_taught_time(event, dependency, True)
                graph.edge(qualify(dependency, dependency_taught_time), qualify(topic, event))
        graph.subgraph(sub_graph)

    graph.view()


def make_full_event_dependency_chart(info: DependencyInfo, filename_out: str):
    graph = Digraph(filename_out, engine='fdp')
    graph.attr(label='Event Dependencies')

    def handle_event():
        taught_graph = Digraph(cluster(f'{event.name}$taught'))
        taught_graph.attr(label='Taught')
        for topic in event.topics_taught:
            qualified_topic = qualify(topic, event, 'taught')
            taught_graph.node(qualified_topic, label=topic)
        required_graph = Digraph(cluster(f'{event.name}$required'))
        required_graph.attr(label='Required')
        for topic in event.topics_required:
            topic_taught_event = info.get_most_recent_taught_time(event, topic, True)
            qualified_topic = qualify(topic, event, 'required')
            required_graph.node(qualified_topic, label=topic)
            if topic_taught_event is None:
                print(f'WARNING: topic \'{topic}\' is not taught before it is required in {event.unit}, {event.name}!')
            else:
                graph.edge(qualify(topic, topic_taught_event, 'taught'), qualified_topic)

        sub_graph = Digraph(cluster(event.name))
        sub_graph.attr(label=event.name)
        sub_graph.subgraph(taught_graph)
        sub_graph.subgraph(required_graph)
        graph.subgraph(sub_graph)

    for event in info.events:
        handle_event()
    graph.view()


def make_event_dependency_chart(info: DependencyInfo, filename_out: str, event: Event):
    graph = Digraph(filename_out)
    graph.attr(label=f'{event.unit}, {event.name} Dependencies')

    event_graphs: dict[Event, Digraph] = {}

    event_sub_graph = Digraph(cluster(event.name))
    event_sub_graph.attr(label=f'{event.name} Requirements')

    event_graphs[event] = event_sub_graph

    def add_topic(topic: str, parent_event: Event, include_start: bool = True, parent_topic: str | None = None):
        topic_event = info.get_most_recent_taught_time(parent_event, topic, include_start)
        if topic_event is None:
            print('WARNING: topic \'{dependency}\' is not taught before it is required in {event.unit}, {event.name}!')
        else:
            if topic_event not in event_graphs:
                temp = Digraph(cluster(topic_event.name))
                temp.attr(label=topic_event.name)
                event_graphs[topic_event] = temp
            sub_graph = event_graphs[topic_event]
            qualified_name = f'{topic_event.unit}${topic_event.name}${topic}'
            sub_graph.node(qualified_name, topic)
            graph.edge(qualified_name,
                       f'{parent_event.unit}${parent_event.name}${topic if parent_topic is None else parent_topic}')
            add_dependencies(topic, topic_event)

    def add_dependencies(topic: str, parent_event: Event):
        for dependency in parent_event.topics_taught[topic]:
            add_topic(dependency, parent_event, dependency is not topic, topic)

    for required_topic in event.topics_required:
        event_sub_graph.node(f'{event.unit}${event.name}${required_topic}', required_topic)
        add_topic(required_topic, event)
    for cluster_graph in event_graphs.values():
        graph.subgraph(cluster_graph)
    graph.view()


def verify_topics(topics: list[str], event: str, prefix: str, info: DependencyInfo):
    for topic in topics:
        if topic not in info.topics:
            print(f'WARNING: {prefix} topic \'{topic}\' in \'{event}\' not in topics list')


def read_info(topics_file: str, events_file: str) -> DependencyInfo:
    info = DependencyInfo()
    with open(topics_file) as topics_text:
        topics_reader = csv.reader(topics_text, delimiter='\t')
        first_row: bool = True
        for row in topics_reader:
            if first_row:
                first_row = False
                continue
            topic = row[0].strip()
            dependencies = [item.strip() for item in row[1].split(';') if item]
            info.topics[topic] = Topic(topic, dependencies, row[2].strip())
    for topic in info.topics:
        for dependency in info.topics[topic].dependencies:
            if dependency not in info.topics:
                print(f'WARNING: dependency \'{dependency}\' of \'{topic}\' is not in the topic list')
    topic_taught_events: dict[str, str] = {}
    with open(events_file) as events_text:
        events_reader = csv.reader(events_text, delimiter='\t')
        first_row = True
        current_unit = None
        for row in events_reader:
            if first_row:
                first_row = False
                continue
            if row[0]:
                current_unit = row[0]
            event = row[1]
            topics_taught = [item.strip() for item in row[2].split(';') if item]
            for topic in topics_taught:
                if topic in topic_taught_events:
                    print(f'WARNING: topic \'{topic}\' is taught in \'{event}\','
                          f' but it is already taught in \'{topic_taught_events[topic]}\'')
                    topic_taught_events[topic] = event
                else:
                    topic_taught_events[topic] = event
            verify_topics(topics_taught, event, 'taught', info)
            topics_needed = [item.strip() for item in row[3].split(';') if item]
            verify_topics(topics_needed, event, 'required', info)
            info.events.append(Event(current_unit, event, topics_taught, topics_needed))
    info.finalize()
    return info


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
        make_topic_dependency_chart(info, f'{output_path}topic-dependencies')
    if '--event-topic-dependencies' in args:
        make_event_topic_dependency_chart(info, f'{output_path}event-topic-dependencies')
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
                make_event_dependency_chart(info, f'{output_path}{unit}_{name}event-dependencies', event)
        else:
            make_full_event_dependency_chart(info, f'{output_path}full-event-dependencies')


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
              '  --event-topic-dependencies             Creates a chart showing what topics each event teaches,\n'
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
