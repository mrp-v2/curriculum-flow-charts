from util import DependencyInfo, Event, qualify

from graphviz import Digraph


def dependencies_only(info: DependencyInfo, filename_out: str, focus_event: Event):
    # main graph
    graph = Digraph(filename_out)
    graph.attr(label=f'{focus_event.unit}, {focus_event.name} Dependencies')
    # map of each event to its subgraph
    event_graphs: dict[Event, Digraph] = {}
    # the focus event's subgraph for required topics
    event_required_graph = Digraph(focus_event.name)
    event_required_graph.attr(cluster='True')
    event_required_graph.attr(label=focus_event.name)
    event_graphs[focus_event] = event_required_graph
    # keep track of what's been drawn, so we don't re-draw it
    nodes_drawn: list[str] = []
    edges_drawn: list[tuple[str, str]] = []

    def draw_edge(qualified_tail: str, qualified_head: str):
        if (qualified_tail, qualified_head) not in edges_drawn:
            graph.edge(qualified_tail, qualified_head)
            edges_drawn.append((qualified_tail, qualified_head))

    def draw_topic_helper(topic: str, event: Event) -> tuple[str, str, Event]:
        qualified_name = qualify(topic, event)
        if event not in event_graphs:
            temp = Digraph(event.name)
            temp.attr(cluster='True')
            temp.attr(label=event.name)
            event_graphs[event] = temp
        if qualified_name not in nodes_drawn:
            sub_graph = event_graphs[event]
            sub_graph.node(qualified_name, topic)
            nodes_drawn.append(qualified_name)
        previous_taught_time = info.get_most_recent_taught_time(event, topic)
        if previous_taught_time is not None and previous_taught_time != event:
            recent_qualified_name, first_qualified_name, first_event = draw_topic_helper(topic, previous_taught_time)
            draw_edge(recent_qualified_name, qualified_name)
            return qualified_name, first_qualified_name, first_event
        else:
            return qualified_name, qualified_name, event

    def draw_topic(topic: str, event: Event) -> Event:
        """
        Draws the node for a topic.
        If the topic is taught previously, draws again for each previous event teaching the topic.

        :return: The event where the topic is taught for the first time
        """
        recent, qualified_first, first_event = draw_topic_helper(topic, event)
        return first_event

    def add_topic(topic: str, search_start: Event, include_start: bool = True, qualified_parent: str | None = None):
        """
        Adds a topic to its corresponding graph and then adds its dependencies as well
        """
        if qualified_parent:
            topic_event = info.get_most_recent_taught_time(search_start, topic, include_start)
        else:
            topic_event = search_start
        if topic_event is None:
            print('WARNING: topic \'{dependency}\' is not taught before it is required in {event.unit}, {event.name}!')
        else:
            original_event = draw_topic(topic, topic_event)
            if qualified_parent is not None:
                qualified_name = qualify(topic, topic_event)
                draw_edge(qualified_name, qualified_parent)
            add_dependencies(topic, original_event)

    def add_dependencies(topic: str, parent_event: Event):
        for dependency in info.topics[topic].dependencies:
            add_topic(dependency, parent_event, dependency is not topic, qualify(topic, parent_event))

    # add all the topics required by the event
    for required_topic in focus_event.topics_required:
        add_topic(required_topic, focus_event)
    # finish by adding all the sub-graphs to the main graph
    for cluster_graph in event_graphs.values():
        graph.subgraph(cluster_graph)
    graph.view()


def dependents_only(info: DependencyInfo, filename_out: str, focus_event: Event):
    # main graph
    graph = Digraph(filename_out)
    graph.attr(label=f'{focus_event.unit}, {focus_event.name} Dependencies')
    # map of each event to its subgraph
    event_graphs: dict[Event, Digraph] = {}
    # the focus event's subgraph for required topics
    event_required_graph = Digraph(focus_event.name)
    event_required_graph.attr(cluster='True')
    event_required_graph.attr(label=focus_event.name)
    event_graphs[focus_event] = event_required_graph
    # keep track of what's been drawn, so we don't re-draw it
    nodes_drawn: list[str] = []
    edges_drawn: list[tuple[str, str]] = []

    def draw_edge(qualified_tail: str, qualified_head: str):
        if (qualified_tail, qualified_head) not in edges_drawn:
            graph.edge(qualified_tail, qualified_head)
            edges_drawn.append((qualified_tail, qualified_head))

    def draw_topic_helper(topic: str, event: Event) -> tuple[str, str, Event]:
        qualified_name = qualify(topic, event)
        if event not in event_graphs:
            temp = Digraph(event.name)
            temp.attr(cluster='True')
            temp.attr(label=event.name)
            event_graphs[event] = temp
        if qualified_name not in nodes_drawn:
            sub_graph = event_graphs[event]
            sub_graph.node(qualified_name, topic)
            nodes_drawn.append(qualified_name)
        previous_taught_time = info.get_most_recent_taught_time(event, topic)
        if previous_taught_time is not None and previous_taught_time != event:
            recent_qualified_name, first_qualified_name, first_event = draw_topic_helper(topic, previous_taught_time)
            draw_edge(recent_qualified_name, qualified_name)
            return qualified_name, first_qualified_name, first_event
        else:
            return qualified_name, qualified_name, event

    def draw_topic(topic: str, event: Event) -> Event:
        """
        Draws the node for a topic.
        If the topic is taught previously, draws again for each previous event teaching the topic.

        :return: The event where the topic is taught for the first time
        """
        recent, qualified_first, first_event = draw_topic_helper(topic, event)
        return first_event

    def add_topic(topic: str, search_start: Event, include_start: bool = True, qualified_parent: str | None = None):
        """
        Adds a topic to its corresponding graph and then adds its dependencies as well
        """
        if qualified_parent:
            topic_event = info.get_most_recent_taught_time(search_start, topic, include_start)
        else:
            topic_event = search_start
        if topic_event is None:
            print('WARNING: topic \'{dependency}\' is not taught before it is required in {event.unit}, {event.name}!')
        else:
            original_event = draw_topic(topic, topic_event)
            if qualified_parent is not None:
                qualified_name = qualify(topic, topic_event)
                draw_edge(qualified_name, qualified_parent)
            add_dependencies(topic, original_event)

    def add_dependencies(topic: str, parent_event: Event):
        for dependency in info.topics[topic].dependencies:
            add_topic(dependency, parent_event, dependency is not topic, qualify(topic, parent_event))

    # add all the topics taught by the event
    for taught_topic in focus_event.topics_taught:
        add_topic(taught_topic, focus_event)
    # TODO add dependents of the event. both topic dependents (grouped by event) and event dependents.
    # finish by adding all the sub-graphs to the main graph
    for cluster_graph in event_graphs.values():
        graph.subgraph(cluster_graph)
    graph.view()


def specific_event_dependencies(info: DependencyInfo, filename_out: str, focus_event: Event):
    """
    Makes a graph showing the dependencies and dependents (recursively) of a specific event.
    Dependencies are based on the topics required for the event,
    and dependents are based on the topics taught in the event.
    """
    if focus_event.topics_taught:
        if focus_event.topics_required:
            pass
        else:
            dependents_only(info, filename_out, focus_event)
    else:
        if focus_event.topics_required:
            dependencies_only(info, filename_out, focus_event)
        else:
            pass
