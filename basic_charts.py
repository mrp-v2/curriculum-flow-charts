from graphviz import Digraph

from util import DependencyInfo, qualify


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
