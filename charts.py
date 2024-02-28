from graphviz import Digraph

from util import DependencyInfo, Event, qualify

from specific_event_dependency_chart import ChartBuilder


def topic_dependencies(info: DependencyInfo, filename_out: str):
    graph = Digraph(filename_out)
    graph.attr(label='Topic Dependencies')

    for topic in info.topics.values():
        graph.node(topic.name)
        for dependency in topic.dependencies:
            graph.edge(dependency, topic.name)
    graph.view()


def topic_event_dependencies(info: DependencyInfo, filename_out: str):
    graph = Digraph(filename_out)
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


def full_event_dependencies(info: DependencyInfo, filename_out: str):
    graph = Digraph(filename_out, engine='fdp')
    graph.attr(label='Event Dependencies')
    for event in info.events:
        taught_graph = Digraph(f'{event.name}$taught')
        taught_graph.attr(cluster='True')
        taught_graph.attr(label='Taught')
        for topic in event.topics_taught:
            qualified_topic = qualify(topic, event, 'taught')
            taught_graph.node(qualified_topic, label=topic)
        required_graph = Digraph(f'{event.name}$required')
        required_graph.attr(cluster='True')
        required_graph.attr(label='Required')
        for topic in event.topics_required:
            topic_taught_event = info.get_most_recent_taught_time(event, topic, True)
            qualified_topic = qualify(topic, event, 'required')
            required_graph.node(qualified_topic, label=topic)
            if topic_taught_event is None:
                print(f'WARNING: topic \'{topic}\' is not taught before it is required in {event.unit}, {event.name}!')
            else:
                graph.edge(qualify(topic, topic_taught_event, 'taught'), qualified_topic)
        sub_graph = Digraph(event.name)
        sub_graph.attr(cluster='True')
        sub_graph.attr(label=event.name)
        sub_graph.subgraph(taught_graph)
        sub_graph.subgraph(required_graph)
        graph.subgraph(sub_graph)
    graph.view()


def specific_event_dependencies(info: DependencyInfo, filename_out: str, focus_event: Event):
    """
    Makes a graph showing the dependencies and dependents (recursively) of a specific event.
    Dependencies are based on the topics required for the event,
    and dependents are based on the topics taught in the event.
    """
    builder: ChartBuilder = ChartBuilder(filename_out, info)
    builder.label(f'{focus_event.unit}, {focus_event.name} Dependencies')
    draw_event_relations(builder, focus_event)
    builder.finish().view()


def draw_event_relations(builder, focus_event):
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


def full_chart(info: DependencyInfo, filename_out: str):
    builder = ChartBuilder(filename_out, info)
    builder.label('Full Course Dependencies')
    for event in info.events:
        draw_event_relations(builder, event)
    builder.finish().view()
