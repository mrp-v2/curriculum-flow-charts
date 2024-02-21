from util import DependencyInfo, Event, qualify

from graphviz import Digraph


def specific_event_dependencies(info: DependencyInfo, filename_out: str, event: Event):
    graph = Digraph(filename_out)
    graph.attr(label=f'{event.unit}, {event.name} Dependencies')

    event_graphs: dict[Event, Digraph] = {}

    event_sub_graph = Digraph(event.name)
    event_sub_graph.attr(cluster='True')
    event_sub_graph.attr(label=f'{event.name} Requirements')

    event_graphs[event] = event_sub_graph

    nodes_drawn: list[str] = []
    edges_drawn: list[tuple[str, str]] = []

    def add_topic(topic: str, parent_event: Event, include_start: bool = True, parent_topic: str | None = None):
        topic_event = info.get_most_recent_taught_time(parent_event, topic, include_start)
        if parent_topic is None:
            parent_topic = topic
        if topic_event is None:
            print('WARNING: topic \'{dependency}\' is not taught before it is required in {event.unit}, {event.name}!')
        else:
            if topic_event not in event_graphs:
                temp = Digraph(topic_event.name)
                temp.attr(cluster='True')
                temp.attr(label=topic_event.name)
                event_graphs[topic_event] = temp
            sub_graph = event_graphs[topic_event]
            qualified_name = qualify(topic, topic_event)
            if qualified_name not in nodes_drawn:
                sub_graph.node(qualified_name, topic)
                nodes_drawn.append(qualified_name)
            parent_qualified_name = qualify(parent_topic, parent_event)
            if (qualified_name, parent_qualified_name) not in edges_drawn:
                graph.edge(qualified_name, parent_qualified_name)
                edges_drawn.append((qualified_name, parent_qualified_name))
            add_dependencies(topic, topic_event)

    def add_dependencies(topic: str, parent_event: Event):
        for dependency in info.topics[topic].dependencies:
            add_topic(dependency, parent_event, dependency is not topic, topic)

    for required_topic in event.topics_required:
        event_sub_graph.node(qualify(required_topic, event), required_topic)
        add_topic(required_topic, event)
    for cluster_graph in event_graphs.values():
        graph.subgraph(cluster_graph)
    graph.view()
