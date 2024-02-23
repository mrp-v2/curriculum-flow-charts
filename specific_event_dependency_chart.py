from typing import Literal

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
    # map of each event to its sub-graphs of required and taught topics
    event_graphs: dict[Event, tuple[Digraph | None, Digraph | None]] = {}
    # keep track of what's been drawn, so we don't re-draw it
    nodes_drawn: list[str] = []
    edges_drawn: list[tuple[str, str]] = []

    def draw_edge(qualified_tail: str, qualified_head: str):
        if (qualified_tail, qualified_head) not in edges_drawn:
            graph.edge(qualified_tail, qualified_head)
            edges_drawn.append((qualified_tail, qualified_head))

    def draw_topic_only(topic: str, event: Event, default_side: Literal['taught', 'required'] = None) -> str:
        qualified_name = qualify(topic, event)
        if qualified_name not in nodes_drawn:
            if event not in event_graphs:
                event_graphs[event] = (None, None)
            required, taught = event_graphs[event]

            def draw_taught():
                if taught is None:
                    temp = Digraph(f'{event.name}$taught')
                    temp.attr(cluster='True')
                    event_graphs[event] = (required, temp)
                _, sub_graph = event_graphs[event]
                sub_graph.node(qualified_name, topic)
                nodes_drawn.append(qualified_name)

            def draw_required():
                if required is None:
                    temp = Digraph(f'{event.name}$required')
                    temp.attr(cluster='True')
                    event_graphs[event] = (temp, taught)
                sub_graph, _ = event_graphs[event]
                sub_graph.node(qualified_name, topic)
                nodes_drawn.append(qualified_name)

            if topic in event.topics_taught and topic in event.topics_required:
                if default_side == 'taught':
                    draw_taught()
                elif default_side == 'required':
                    draw_required()
                else:
                    raise ValueError('')  # TODO message
            elif topic in event.topics_taught:
                draw_taught()
            elif topic in event.topics_required:
                draw_required()
            else:
                raise ValueError('Given topic and event aren\'t related!')
        return qualified_name

    def draw_topic_helper(topic: str, event: Event) -> tuple[str, str, Event]:
        qualified_name = draw_topic_only(topic, event)
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

    def add_dependent_tree(event: Event):
        for topic in event.topics_taught:
            if topic in topics_of_interest:
                draw_topic_only(topic, event, 'taught')
                draw_edge(qualify(topic, topics_of_interest[topic]), qualify(topic, event))
                topics_of_interest[topic] = event
            to_add: list[tuple[str, Event]] = []
            for topic_of_interest in topics_of_interest:
                if topic_of_interest in info.topics[topic].dependencies:
                    draw_topic_only(topic, event, 'taught')
                    last_taught_time = info.get_most_recent_taught_time(event, topic_of_interest, True)
                    draw_edge(qualify(topic_of_interest, last_taught_time), qualify(topic, event))
                    to_add.append((topic, event))
            for topic_to_set, event_to_set in to_add:
                topics_of_interest[topic_to_set] = event_to_set
        for topic in event.topics_required:
            if topic in topics_of_interest:
                draw_topic_only(topic, event, 'required')
                draw_edge(qualify(topic, topics_of_interest[topic]), qualify(topic, event))
                topics_of_interest[topic] = event
        if event.next:
            add_dependent_tree(event.next)

    # tracks topics we are interested in and the last time they appeared
    topics_of_interest: dict[str, Event] = {}
    for taught_topic in focus_event.topics_taught:
        add_topic(taught_topic, focus_event)
        topics_of_interest[taught_topic] = focus_event
    add_dependent_tree(focus_event.next)
    # finish by adding all the sub-graphs to the main graph
    for event in event_graphs:
        required_graph, taught_graph = event_graphs[event]
        if required_graph is not None and taught_graph is not None:
            required_graph.attr(label='Required')
            taught_graph.attr(label='Taught')
            sub_graph = Digraph(event.name)
            sub_graph.attr(cluster='True')
            sub_graph.attr(label=event.name)
            sub_graph.subgraph(required_graph)
            sub_graph.subgraph(taught_graph)
            graph.subgraph(sub_graph)
        elif required_graph is not None:
            required_graph.attr(label=event.name)
            graph.subgraph(required_graph)
        elif taught_graph is not None:
            taught_graph.attr(label=event.name)
            graph.subgraph(taught_graph)
        else:
            raise RuntimeError('Event in event_graphs has no sub-graphs!')
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
