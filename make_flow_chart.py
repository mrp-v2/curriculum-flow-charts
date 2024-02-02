import csv
import sys

import os.path

from graphviz import Digraph


class Event:
    def __init__(self, unit: str, name: str, topics_taught: dict[str, list[str]], topics_required: list[str]):
        self.unit: str = unit
        self.name: str = name
        self.topics_taught: dict[str, list[str]] = topics_taught
        self.topics_required: list[str] = topics_required


class DependencyInfo:
    """
    Stores information about the course topics and events.\n
    topic_dependencies: a dictionary mapping each topic to a list of topics it depends on.\n
    topic_dependents: a dictionary mapping each topic to a list of topics that depend on it.\n
    events: a dictionary mapping from each unit to another dictionary mapping each event to a tuple,
    where each tuple contains first a list of topics taught in the event,
    and second a list of topics required for the event.
    """

    def __init__(self):
        self.__topic_dependencies: dict[str, list[str]] = {}
        self.__topic_dependents: dict[str, list[str]] = {}
        self.__events: list[Event] = []

    def add_topic_dependencies(self, topic: str, dependencies: list[str]):
        if topic in self.__topic_dependencies:
            print(f'WARNING: redefining the dependencies for topic {topic}')
        self.__topic_dependencies[topic] = dependencies
        for dependency in dependencies:
            self.add_topic_dependent(dependency, topic)

    def add_topic_dependent(self, topic: str, dependent: str):
        if topic not in self.__topic_dependents:
            self.__topic_dependents[topic] = [dependent]
        else:
            self.__topic_dependents[topic].append(dependent)

    def add_event(self, event: Event):
        self.__events.append(event)

    def is_topic_dependent_on(self, topic: str, dependency: str) -> bool:
        """
        Returns True if dependency is a dependency of topic. Probes depth as well.
        """
        if dependency not in self.__topic_dependents:
            return False
        for dependent in self.__topic_dependents[dependency]:
            if dependent == topic:
                return True
            if self.is_topic_dependent_on(topic, dependent):
                return True
        return False

    def finalize(self):
        for event in self.get_events():
            required = event.topics_required
            i: int = 0
            while i < len(required):
                for other in required:
                    if other == required[i]:
                        continue
                    if self.is_topic_dependent_on(other, required[i]):
                        required.remove(required[i])
                        i -= 1
                        break
                i += 1

    def get_events(self) -> list[Event]:
        return self.__events

    def get_most_recent_taught_time(self, start: Event, topic: str) -> Event | None:
        index: int = self.__events.index(start) - 1
        while topic not in self.__events[index].topics_taught and index >= 0:
            index -= 1
        if index == -1:
            return None
        return self.__events[index]


def trim_topic(topic: str) -> str:
    """
    Trim the topic of its dependencies
    >>> trim_topic('')
    ''
    >>> trim_topic('test')
    'test'
    >>> trim_topic('test{hi}')
    'test'
    """
    if '{' in topic:
        return topic[:topic.index('{')]
    else:
        return topic


def split_tokens(tokens_str: str, ignore_groups: dict[str, str], delimiter: str = ',') -> list[str]:
    tokens_list: list[str] = []
    last_token_end_index: int = -1
    index: int = 1

    def add_token():
        token: str = tokens_str[last_token_end_index + 1:index].strip()
        if token:
            tokens_list.append(token)

    while index < len(tokens_str):
        char = tokens_str[index]
        if char in ignore_groups:
            index = tokens_str.index(ignore_groups[char], index)
            pass
        elif char == delimiter:
            add_token()
            last_token_end_index = index
        index += 1
    add_token()
    return tokens_list


def split_dependencies(topic: str) -> list[str]:
    """
    Get the dependencies of a topic
    >>> split_dependencies('test{dependency}')
    ['dependency']
    >>> split_dependencies('test{d1, d2}')
    ['d1', 'd2']
    """
    if '{' not in topic:
        return []
    dependency_str = topic[topic.index('{') + 1:topic.index('}')]
    return split_tokens(dependency_str, {'(': ')'})


def split_topics(topics: str) -> list[str]:
    """
    Split the topics
    >>> split_topics('topic1')
    ['topic1']
    >>> split_topics('topic1, topic2')
    ['topic1', 'topic2']
    >>> split_topics('topic1{d1, d2}, topic2')
    ['topic1{d1, d2}', 'topic2']
    >>> split_topics('topic1{d1}, topic2{d1, d2}')
    ['topic1{d1}', 'topic2{d1, d2}']
    """
    return split_tokens(topics, {'(': ')', '{': '}'})


def cluster(topic: str) -> str:
    return f'cluster_{topic}'


def make_topic_dependency_chart(info: DependencyInfo, filename_out: str):
    graph = Digraph(filename_out)
    graph.attr(label='Topic Dependencies')

    def handle_event():
        sub_graph = Digraph(cluster(event.name))
        sub_graph.attr(label=event.name)
        for topic in event.topics_taught:
            qualified_topic = f"{event.unit}${event.name}${topic}"
            sub_graph.node(qualified_topic, label=topic)
            for dependency in event.topics_taught[topic]:
                dependency_event = info.get_most_recent_taught_time(event, dependency)
                if dependency_event is not None:
                    graph.edge(f"{dependency_event.unit}${dependency_event.name}${dependency}", qualified_topic)
            last_event_for_topic = info.get_most_recent_taught_time(event, topic)
            if last_event_for_topic is not None and last_event_for_topic != event:
                graph.edge(f"{last_event_for_topic.unit}${last_event_for_topic.name}${topic}", qualified_topic)
        graph.subgraph(sub_graph)

    for event in info.get_events():
        handle_event()
    graph.view()


def read_tsv(tsv_file_in: str) -> DependencyInfo:
    info = DependencyInfo()
    with open(tsv_file_in) as tsv_text:
        csvreader = csv.reader(tsv_text, delimiter='\t')
        first_row = True
        current_unit = None
        for row in csvreader:
            if first_row:
                first_row = False
                continue
            if row[0]:
                current_unit = row[0]
            topics_taught = split_topics(row[2])
            trimmed_topics_taught: dict[str, list[str]] = {}
            for topic in topics_taught:
                trimmed = trim_topic(topic)
                trimmed_topics_taught[trimmed] = split_dependencies(topic)
            topics_needed = split_topics(row[3])
            info.add_event(Event(current_unit, row[1], trimmed_topics_taught, topics_needed))
    info.finalize()
    return info


def main(tsv_file_in: str, args: list[str]):
    info = read_tsv(tsv_file_in)
    for flag in args:
        if flag.startswith('--topic-dependencies='):
            make_topic_dependency_chart(info, flag[len('--topic-dependencies='):])
        else:
            print(f'Unrecognized flag: {flag}')


if __name__ == '__main__':
    if len(sys.argv) == 2 and '--help' in sys.argv:
        print('make_flow_chart takes at least two arguments:\n'
              '1. The path to a tsv file containing course information\n'
              '2. One or more of the following flags:\n'
              '  --topic-dependencies=<filename>   Creates a chart showing the flow of topic dependencies,\n'
              '                                      and saves it to <filename>\n')
    if len(sys.argv) < 3:
        print('make_flow_chart requires at least two arguments')
        exit(1)
    if os.path.isfile(sys.argv[1]):
        main(sys.argv[1], sys.argv[2:])
    else:
        print(f'Invalid file: {sys.argv[2]}')
        exit(2)
