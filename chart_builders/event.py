from graphviz import Digraph

from chart_builders.base_chart_builder import BaseChartBuilder
from util import Event, Side, qualify
from util.chart_context import ChartContext


class EventChartBuilder(BaseChartBuilder):
    """Draws charts that focus on a single event, drawing all things related to that event."""

    def __init__(self, context: ChartContext, event: Event = None, chart_name: str = None):
        super().__init__(context, f'{event.unit}_{event.name}' if event else chart_name)
        self._event_graphs: dict[Event, tuple[Digraph | None, Digraph | None]] = {}
        """Stores the sub-graphs for each event as a tuple: (required graph, taught graph)."""

    def __draw_sided_topic(self, topic: str, event: Event, side: Side, attrs) -> str:
        """
        Draws a topic under the specified graph of an event.
        :param topic: The name of the topic to draw.
        :param event: The event to draw the topic under.
        :param side: The sub-graph of the event to draw the topic in. Either 'taught' or 'required'.
        :return: The qualified name of the topic.
        """
        qualified_name = qualify(topic, event, side)
        required, taught = self._event_graphs[event]
        temp = (required if side == 'required' else taught)
        if temp is None:
            temp = Digraph(f'{event.name}${side}')
            temp.attr(cluster='True')
            if side == 'required':
                required = temp
            else:
                taught = temp
        self._event_graphs[event] = (required, taught)
        self._draw_node(qualified_name, topic, temp, attrs)
        return qualified_name

    def _draw_topic_only(self, topic: str, event: Event,
                         default_side: Side = None, force_draw: bool = False, **attrs) -> str:
        """
        Draws a topic under an event.
        :param topic: The topic to draw.
        :param event: The event to draw the topic under.
        :param default_side: If the topic is both taught and required by the event,
                             specifies which graph to draw it under.
        :param force_draw: Forces drawing the topic even if it isn't related to event.
                           Requires default_side to be specified.
        :return: The qualified name of the topic's node.
        """
        qualified_name: str
        if topic in event.topics_taught and topic in event.topics_required:
            if default_side == 'taught':
                qualified_name = qualify(topic, event, 'taught')
            elif default_side == 'required':
                qualified_name = qualify(topic, event, 'required')
            else:
                raise ValueError('If a topic is both taught and required by an event, '
                                 'a default side must be specified')
        elif topic in event.topics_taught:
            qualified_name = qualify(topic, event, 'taught')
        elif topic in event.topics_required:
            qualified_name = qualify(topic, event, 'required')
        elif not force_draw:
            raise ValueError('Given topic and event aren\'t related')
        else:
            if default_side is None:
                raise ValueError('If force_draw is True, then default_side must be specified')
            qualified_name = qualify(topic, event, default_side)
        if event not in self._event_graphs:
            self._event_graphs[event] = (None, None)
        if topic in event.topics_taught and topic in event.topics_required:
            if default_side == 'taught':
                self.__draw_sided_topic(topic, event, 'taught', attrs)
            elif default_side == 'required':
                self.__draw_sided_topic(topic, event, 'required', attrs)
            else:
                raise ValueError('If a topic is both taught and required by an event, '
                                 'a default side must be specified')
        elif topic in event.topics_taught:
            self.__draw_sided_topic(topic, event, 'taught', attrs)
        elif topic in event.topics_required:
            self.__draw_sided_topic(topic, event, 'required', attrs)
        else:
            self.__draw_sided_topic(topic, event, default_side, attrs)
        return qualified_name

    def _draw_topic_helper(self, topic: str, event: Event) -> tuple[str, str, Event]:
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
        name = self._draw_topic_only(topic, event, 'taught')
        previous_taught_time = self._context.info.get_most_recent_taught_time(event, topic)
        if previous_taught_time is not None and previous_taught_time != event:
            recent_qualified_name, first_name, first_event = self._draw_topic_helper(topic, previous_taught_time)
            self._draw_edge(recent_qualified_name, name)
            return name, first_name, first_event
        else:
            return name, name, event

    def _draw_topic(self, topic: str, event: Event) -> Event:
        """
        Draws a topic, and redraws for every time it has been taught before.
        :param topic: The topic to draw.
        :param event: The event to draw it under.
        :return: The first event where the topic is taught.
        """
        name, first_name, first_event = self._draw_topic_helper(topic, event)
        return first_event

    def _draw_dependencies(self, topic: str, parent_event: Event):
        """
        Draws nodes for all the dependencies of a topic.
        :param topic: The topic to draw the dependencies of.
        :param parent_event: The event to use as both the default event and parent event when calling add_topic.
        """
        for dependency in self._context.info.topics[topic].dependencies:
            self.__draw_sided_topic_and_dependencies_depth(dependency, parent_event, dependency is not topic,
                                                           qualify(topic, parent_event, 'taught'))

    def __draw_sided_topic_and_dependencies_depth(self, topic: str, default_event: Event, include_start: bool = True,
                                                  parent_node: str | None = None):
        """
        Draws a node for a topic, and recursively draws nodes for its dependencies and draws edges connecting it to its
        dependencies.
        :param topic: The topic to draw.
        :param default_event: Specifies the default event to draw topic under.
        :param include_start: If parent_node is specified, specifies whether to include search_start
                              in the search for the event where topic is most recently taught.
        :param parent_node: If specified, connects the topic's node to parent_node.
                            Also triggers a search for the event where topic is most recently taught,
                            starting at search_start.
        """
        if parent_node:
            topic_event = self._context.info.get_most_recent_taught_time(default_event, topic, include_start)
        else:
            topic_event = default_event
        if topic_event is None:
            print(f'WARNING: topic \'{topic}\' is not taught before it is required '
                  f'in {default_event.unit}, {default_event.name}!')
        else:
            original_event = self._draw_topic(topic, topic_event)
            if parent_node is not None:
                name = qualify(topic, topic_event, 'taught')
                self._draw_edge(name, parent_node)
            self._draw_dependencies(topic, original_event)

    def _draw_dependent_tree_helper(self, event: Event, topics_of_interest: dict[str, str]):
        """
        Recursively draws all events/topics that involve topics in the topics_of_interest dictionary.
        :param event: The current event being drawn.
        :param topics_of_interest: Tracks relevant topics for the dependent tree and their latest qualified name.
        """
        for topic in event.topics_taught:
            if topic in topics_of_interest:
                name = self._draw_topic_only(topic, event, 'taught')
                last_taught_time = self._context.info.get_most_recent_taught_time(event, topic)
                tail_name = qualify(topic, last_taught_time, 'taught')
                self._draw_edge(tail_name, name)
                topics_of_interest[topic] = name
            to_add: list[tuple[str, str]] = []
            for topic_of_interest in topics_of_interest:
                if topic_of_interest in self._context.info.topics[topic].dependencies:
                    name = self._draw_topic_only(topic, event, 'taught')
                    last_taught_time = self._context.info.get_most_recent_taught_time(event, topic_of_interest, True)
                    tail_name = qualify(topic_of_interest, last_taught_time, 'taught')
                    self._draw_edge(tail_name, name)
                    to_add.append((topic, name))
            for topic_to_set, qualified_name in to_add:
                topics_of_interest[topic_to_set] = qualified_name
        for topic in event.topics_required:
            if topic in topics_of_interest:
                name = self._draw_topic_only(topic, event, 'required')
                self._draw_edge(topics_of_interest[topic], name)
                topics_of_interest[topic] = name
        if event.next:
            self._draw_dependent_tree_helper(event.next, topics_of_interest)

    def _draw_dependent_tree(self, event: Event):
        """
        Draws all the events/topics that depend on the topics taught by event.
        :param event: The event to draw all dependents of.
        """
        topics_of_interest: dict[str, str] = {}
        """Tracks relevant topics for the dependent tree and their latest qualified name."""
        for topic in event.topics_taught:
            topics_of_interest[topic] = qualify(topic, event, 'taught')
        self._draw_dependent_tree_helper(event.next, topics_of_interest)

    def draw_event_relations(self, event: Event):
        if event.topics_taught:
            if event.topics_required:
                for topic in event.topics_required:
                    self.__draw_sided_topic_and_dependencies_depth(topic, event)
                for topic in event.topics_taught:
                    self.__draw_sided_topic_and_dependencies_depth(topic, event)
                self._draw_dependent_tree(event)
            else:
                for topic in event.topics_taught:
                    self.__draw_sided_topic_and_dependencies_depth(topic, event)
                self._draw_dependent_tree(event)
        else:
            if event.topics_required:
                for topic in event.topics_required:
                    self.__draw_sided_topic_and_dependencies_depth(topic, event)
            else:
                print(f'ERROR: event {event} has no topics taught or required')

    def _finish_event(self, event: Event, parent_graph: Digraph, **attr):
        required_graph, taught_graph = self._event_graphs[event]
        if required_graph is not None and taught_graph is not None:
            required_graph.attr(label='Required', style='dotted', penwidth='1')
            taught_graph.attr(label='Taught', style='dotted', penwidth='1')
            event_graph = Digraph(event.name)
            event_graph.attr(_attributes=attr, cluster='True', label=event.name)
            event_graph.subgraph(required_graph)
            event_graph.subgraph(taught_graph)
            parent_graph.subgraph(event_graph)
        elif required_graph is not None:
            required_graph.attr(_attributes=attr, label=event.name)
            parent_graph.subgraph(required_graph)
        elif taught_graph is not None:
            taught_graph.attr(_attributes=attr, label=event.name)
            parent_graph.subgraph(taught_graph)
        else:
            raise RuntimeError('Event in event_graphs has no sub-graphs! This should never happen.')

    def finish(self):
        """
        Finalizes the graph and returns it.
        """
        for event in self._event_graphs:
            self._finish_event(event, self._graph)
        return self._graph
