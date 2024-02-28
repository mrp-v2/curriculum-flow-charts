from pathlib import Path

from graphviz import Digraph

from util import DependencyInfo, Event, qualify

from chart_builder import ChartBuilder


def topic_chart(info: DependencyInfo, file_out: Path):
    graph = Digraph(str(file_out))
    graph.attr(label='Topic Dependencies')

    for topic in info.topics.values():
        graph.node(topic.name)
        for dependency in topic.dependencies:
            graph.edge(dependency, topic.name)
    graph.view()


def topic_by_event_chart(info: DependencyInfo, file_out: Path):
    graph = Digraph(str(file_out))
    graph.attr(label='Event Based Topic Dependencies')

    for event in info.events:
        sub_graph = Digraph(event.name)
        sub_graph.attr(cluster='True')
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


def event_chart(info: DependencyInfo, file_out: Path, focus_event: Event):
    """
    Makes a graph showing the dependencies and dependents (recursively) of a specific event.
    Dependencies are based on the topics required for the event,
    and dependents are based on the topics taught in the event.
    """
    builder: ChartBuilder = ChartBuilder(file_out, info)
    builder.label(f'{focus_event.unit}, {focus_event.name} Dependencies')
    __draw_event_relations(builder, focus_event)
    builder.finish().view()


def __draw_event_relations(builder, focus_event):
    if focus_event.topics_taught:
        if focus_event.topics_required:
            for topic in focus_event.topics_required:
                builder.draw_topic_and_dependencies(topic, focus_event)
            for topic in focus_event.topics_taught:
                builder.draw_topic_and_dependencies(topic, focus_event)
            builder.draw_dependent_tree(focus_event)
        else:
            for topic in focus_event.topics_taught:
                builder.draw_topic_and_dependencies(topic, focus_event)
            builder.draw_dependent_tree(focus_event)
    else:
        if focus_event.topics_required:
            for topic in focus_event.topics_required:
                builder.draw_topic_and_dependencies(topic, focus_event)
        else:
            print(f'ERROR: event {focus_event} has no topics taught or required')


def full_chart(info: DependencyInfo, file_out: Path):
    builder = ChartBuilder(file_out, info)
    builder.label('Full Course Dependencies')
    for event in info.events:
        __draw_event_relations(builder, event)
    builder.finish().view()
