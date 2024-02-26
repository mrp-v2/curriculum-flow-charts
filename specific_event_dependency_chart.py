from typing import Literal

from util import DependencyInfo, Event, qualify

from graphviz import Digraph


class ChartBuilder:
    """
    Helper class that provides functions for creating a chart.
    """

    def __init__(self, filename_out: str, info: DependencyInfo):
        self.__info: DependencyInfo = info
        """The DependencyInfo used for building the chart."""
        self.__graph: Digraph = Digraph(filename_out)
        """The main graph object for the chart."""
        self.__event_graphs: dict[Event, tuple[Digraph | None, Digraph | None]] = {}
        """Stores the sub-graphs for each event as a tuple: (required graph, taught graph)."""
        self.__nodes_drawn: list[str] = []
        """Tracks all the nodes drawn to prevent duplicate nodes."""
        self.__edges_drawn: list[tuple[str, str]] = []
        """Tracks all edges drawn to prevent duplicate edges."""

    def graph_label(self, label: str):
        """
        Sets the label for the graph.
        :param label: The label for the graph.
        """
        self.__graph.attr(label=label)

    def draw_edge(self, tail: str, head: str):
        """
        Draws an edge connecting two nodes. Does nothing if the edge has already been drawn.
        :param tail: The qualified name of the tail node.
        :param head: The qualified name of the head node.
        """
        if (tail, head) not in self.__edges_drawn:
            self.__graph.edge(tail, head)
            self.__edges_drawn.append((tail, head))

    def __draw_taught(self, event: Event, topic: str) -> str:
        """
        Draws a topic under the taught graph of an event.
        :param event: The event to draw the topic under.
        :param topic: The name of the topic.
        :return: The qualified name of the topic's node.
        """
        qualified_name = qualify(topic, event)
        required, taught = self.__event_graphs[event]
        if taught is None:
            taught = Digraph(f'{event.name}$taught')
            taught.attr(cluster='True')
            self.__event_graphs[event] = (required, taught)
        taught.node(qualified_name, topic)
        self.__nodes_drawn.append(qualified_name)
        return qualified_name

    def __draw_required(self, event: Event, topic: str) -> str:
        """
        Draws a topic under the required graph of an event.
        :param event: The event to draw the topic under.
        :param topic: The name of the topic.
        :return: The qualified name of the topic's node.
        """
        qualified_name = qualify(topic, event)
        required, taught = self.__event_graphs[event]
        if required is None:
            required = Digraph(f'{event.name}$required')
            required.attr(cluster='True')
            self.__event_graphs[event] = (required, taught)
        required.node(qualified_name, topic)
        self.__nodes_drawn.append(qualified_name)
        return qualified_name

    def draw_topic_only(self, topic: str, event: Event, default_side: Literal['taught', 'required'] = None) -> str:
        """
        Draws a topic under an event.
        :param topic: The topic to draw.
        :param event: The event to draw the topic under.
        :param default_side: If the topic is both taught and required by the event,
                             specifies which graph to draw it under.
        :return: The qualified name of the topic's node.
        """
        qualified_name = qualify(topic, event)
        if qualified_name not in self.__nodes_drawn:
            if event not in self.__event_graphs:
                self.__event_graphs[event] = (None, None)
            if topic in event.topics_taught and topic in event.topics_required:
                if default_side == 'taught':
                    self.__draw_taught(event, topic)
                elif default_side == 'required':
                    self.__draw_required(event, topic)
                else:
                    raise ValueError('If a topic is both taught and required by an event, '
                                     'a default side must be specified')
            elif topic in event.topics_taught:
                self.__draw_taught(event, topic)
            elif topic in event.topics_required:
                self.__draw_required(event, topic)
            else:
                raise ValueError('Given topic and event aren\'t related!')
        return qualified_name

    def __draw_topic_helper(self, topic: str, event: Event) -> tuple[str, str, Event]:
        """
        Draws a topic.
        Then checks if the topic has been taught previous to event.
        If it has, then recursively:\n
        -Draw the topic under the event where it was previously taught\n
        -Draw an edge connecting the two places the topics was drawn.
        :return: A tuple containing the qualified name of the node drawn,
                 the qualified name of the first node where the topic was taught,
                 and the first event where the topic was taught
        """
        name = self.draw_topic_only(topic, event, 'taught')
        previous_taught_time = self.__info.get_most_recent_taught_time(event, topic)
        if previous_taught_time is not None and previous_taught_time != event:
            recent_qualified_name, first_name, first_event = self.__draw_topic_helper(topic, previous_taught_time)
            self.draw_edge(recent_qualified_name, name)
            return name, first_name, first_event
        else:
            return name, name, event

    def draw_topic(self, topic: str, event: Event) -> Event:
        """
        Draws a topic, and redraws for every time it has been taught before.
        :param topic: The topic to draw.
        :param event: The event to draw it under.
        :return: The first event where the topic is taught.
        """
        name, first_name, first_event = self.__draw_topic_helper(topic, event)
        return first_event

    def __add_dependencies(self, topic: str, parent_event: Event):
        """
        Draws nodes for all the dependencies of a topic.
        :param topic: The topic to draw the dependencies of.
        :param parent_event: The event to use as both the default event and parent event when calling add_topic.
        """
        for dependency in self.__info.topics[topic].dependencies:
            self.add_topic(dependency, parent_event, dependency is not topic, qualify(topic, parent_event))

    def add_topic(self, topic: str, default_event: Event, include_start: bool = True, parent_node: str | None = None):
        """
        Draws a node for a topic, and recursively draws nodes for its dependencies and draws edges connecting it to its dependencies.
        :param topic: The topic to draw.
        :param default_event: Specifies the default event to draw topic under.
        :param include_start: If parent_node is specified, specifies whether to include search_start
                              in the search for the event where topic is most recently taught.
        :param parent_node: If specified, connects the topic's node to parent_node.
                            Also triggers a search for the event where topic is most recently taught,
                            starting at search_start.
        """
        if parent_node:
            topic_event = self.__info.get_most_recent_taught_time(default_event, topic, include_start)
        else:
            topic_event = default_event
        if topic_event is None:
            print(f'WARNING: topic \'{topic}\' is not taught before it is required '
                  f'in {default_event.unit}, {default_event.name}!')
        else:
            original_event = self.draw_topic(topic, topic_event)
            if parent_node is not None:
                name = qualify(topic, topic_event)
                self.draw_edge(name, parent_node)
            self.__add_dependencies(topic, original_event)

    def __add_dependent_tree_helper(self, event: Event, topics_of_interest: dict[str, Event]):
        for topic in event.topics_taught:
            if topic in topics_of_interest:
                self.draw_topic_only(topic, event, 'taught')
                self.draw_edge(qualify(topic, topics_of_interest[topic]), qualify(topic, event))
                topics_of_interest[topic] = event
            to_add: list[tuple[str, Event]] = []
            for topic_of_interest in topics_of_interest:
                if topic_of_interest in self.__info.topics[topic].dependencies:
                    self.draw_topic_only(topic, event, 'taught')
                    last_taught_time = self.__info.get_most_recent_taught_time(event, topic_of_interest, True)
                    self.draw_edge(qualify(topic_of_interest, last_taught_time), qualify(topic, event))
                    to_add.append((topic, event))
            for topic_to_set, event_to_set in to_add:
                topics_of_interest[topic_to_set] = event_to_set
        for topic in event.topics_required:
            if topic in topics_of_interest:
                self.draw_topic_only(topic, event, 'required')
                self.draw_edge(qualify(topic, topics_of_interest[topic]), qualify(topic, event))
                topics_of_interest[topic] = event
        if event.next:
            self.__add_dependent_tree_helper(event.next, topics_of_interest)

    def add_dependent_tree(self, event: Event):
        topics_of_interest: dict[str, Event] = {}
        """Tracks relevant topics for the dependent tree and when they were last required."""
        for topic in event.topics_taught:
            topics_of_interest[topic] = event
        self.__add_dependent_tree_helper(event.next, topics_of_interest)

    def finish(self):
        """
        Finalizes the graph and returns it.
        """
        for event in self.__event_graphs:
            required_graph, taught_graph = self.__event_graphs[event]
            if required_graph is not None and taught_graph is not None:
                required_graph.attr(label='Required')
                taught_graph.attr(label='Taught')
                event_graph = Digraph(event.name)
                event_graph.attr(cluster='True')
                event_graph.attr(label=event.name)
                event_graph.subgraph(required_graph)
                event_graph.subgraph(taught_graph)
                self.__graph.subgraph(event_graph)
            elif required_graph is not None:
                required_graph.attr(label=event.name)
                self.__graph.subgraph(required_graph)
            elif taught_graph is not None:
                taught_graph.attr(label=event.name)
                self.__graph.subgraph(taught_graph)
            else:
                raise RuntimeError('Event in event_graphs has no sub-graphs! This should never happen.')
        return self.__graph


def specific_event_dependencies(info: DependencyInfo, filename_out: str, focus_event: Event):
    """
    Makes a graph showing the dependencies and dependents (recursively) of a specific event.
    Dependencies are based on the topics required for the event,
    and dependents are based on the topics taught in the event.
    """
    builder: ChartBuilder = ChartBuilder(filename_out, info)
    builder.graph_label(f'{focus_event.unit}, {focus_event.name} Dependencies')
    if focus_event.topics_taught:
        if focus_event.topics_required:
            pass
        else:
            for topic in focus_event.topics_taught:
                builder.add_topic(topic, focus_event)
            builder.add_dependent_tree(focus_event)
    else:
        if focus_event.topics_required:
            for required_topic in focus_event.topics_required:
                builder.add_topic(required_topic, focus_event)
        else:
            pass
    graph = builder.finish()
    graph.view()
