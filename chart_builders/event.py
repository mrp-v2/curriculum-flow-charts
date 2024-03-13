from graphviz import Digraph

from chart_builders.base_chart_builder import BaseChartBuilder
from util import Event, Side, qualify
from util.chart_context import ChartContext


class EventChartBuilder(BaseChartBuilder):
    """
    Draws charts that focus on a single event, drawing all things related to that event.
    """

    def __init__(self, context: ChartContext, chart_name: str = None):
        """
        :param context: The ChartContext to use for this builder.
        :param chart_name: The name of this chart. Defaults to the event name
        """
        super().__init__(context, chart_name if chart_name else context.focus_event.name)
        self._event_graphs: dict[Event, Digraph] = {}
        """Stores the sub-graphs for each event."""
        self._event_id_graphs: dict[int, dict[str | None, Digraph]] = {}
        """Stores the parent graph for sub-graphs for each event id"""
        self._latest_required_times: dict[str, tuple[Event, str]] = {}
        """Stores the last event in which a topic was required, and the qualified name of the node."""
        self._rank_nodes: dict[int, str] = {}
        """Stores the qualified name of the rank node for each rank"""
        self._last_rank: int | None = None
        """Tracks the number of the last rank node drawn"""
        self._node_ranks: dict[str, int] = {}
        """Tracks the rank of each node"""

    def __draw_sided_topic(self, topic: str, event: Event, side: Side, attrs) -> str:
        """
        Draws a topic under the specified graph of an event.
        :param topic: The name of the topic to draw.
        :param event: The event to draw the topic under.
        :param side: The sub-graph of the event to draw the topic in. Either 'taught' or 'required'.
        :return: The qualified name of the topic.
        """
        qualified_name = qualify(topic, event)
        graph = self._event_graphs.get(event)
        if graph is None:
            graph = Digraph(f'{event.name}')
            graph.attr(cluster='True')
        self._event_graphs[event] = graph
        self._draw_node(qualified_name, topic, graph, attrs, color=f'{"blue" if side == "taught" else ""}')
        return qualified_name

    def _draw_topic_only(self, topic: str, event: Event, **attrs) -> str:
        """
        Draws a topic under an event.
        :param topic: The topic to draw.
        :param event: The event to draw the topic under.
        :return: The qualified name of the topic's node.
        """
        qualified_name = qualify(topic, event)
        if topic in event.topics_taught:
            self.__draw_sided_topic(topic, event, 'taught', attrs)
        else:
            self.__draw_sided_topic(topic, event, 'required', attrs)
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
        name = self._draw_topic_only(topic, event)
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
                                                           qualify(topic, parent_event))

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
                  f'in Unit {default_event.unit}, {default_event.name}!')
        else:
            original_event = self._draw_topic(topic, topic_event)
            if parent_node is not None:
                name = qualify(topic, topic_event)
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
                name = self._draw_topic_only(topic, event)
                last_taught_time = self._context.info.get_most_recent_taught_time(event, topic)
                tail_name = qualify(topic, last_taught_time)
                self._draw_edge(tail_name, name)
                topics_of_interest[topic] = name
            to_add: list[tuple[str, str]] = []
            for topic_of_interest in topics_of_interest:
                if topic_of_interest in self._context.info.topics[topic].dependencies:
                    name = self._draw_topic_only(topic, event)
                    last_taught_time = self._context.info.get_most_recent_taught_time(event, topic_of_interest, True)
                    tail_name = qualify(topic_of_interest, last_taught_time)
                    self._draw_edge(tail_name, name)
                    to_add.append((topic, name))
            for topic_to_set, qualified_name in to_add:
                topics_of_interest[topic_to_set] = qualified_name
        for topic in event.topics_required:
            if topic in topics_of_interest:
                name = self._draw_topic_only(topic, event)
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
            topics_of_interest[topic] = qualify(topic, event)
        self._draw_dependent_tree_helper(event.next, topics_of_interest)

    def _draw_unit(self, unit: int, start_rank: int) -> int:
        for event_id in self._context.info.grouped_events[unit]:
            start_rank = self._draw_id(event_id, start_rank, unit)
        return start_rank

    def draw(self):
        """
        TODO
        :return:
        """
        start_rank: int = 0
        for unit in self._context.info.grouped_events:
            start_rank = self._draw_unit(unit, start_rank)
        # TODO remove everything after this
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
        self._event_graphs[event].attr(_attributes=attr, label=event.name)
        parent_graph.subgraph(self._event_graphs[event])

    def finish(self):
        """
        Finalizes the graph and returns it.
        """
        for event in self._event_graphs:
            self._finish_event(event, self._graph)
        return self._graph

    def __get_tail_node(self, topic: str, event: Event, include_start: bool) -> str | None:
        """
        Decides which node should be the tail.
        :param topic: The topic of the head node.
        :param event: The event of the head node.
        :return: The node where topic was most recently taught or required.
        """
        last_taught_time = self._context.info.get_most_recent_taught_time(event, topic, include_start)
        if topic not in self._latest_required_times and last_taught_time is None:
            return None
        if topic not in self._latest_required_times:
            return qualify(topic, last_taught_time)
        if last_taught_time is None:
            return self._latest_required_times[topic][1]
        # return which is more recent
        if self._latest_required_times[topic][0] < last_taught_time:
            return qualify(topic, last_taught_time)
        else:
            return self._latest_required_times[topic][1]

    def __draw_rank_node(self) -> str:
        return self._draw_node(f'rank_node_{self._last_rank}',
                               shape='ellipse' if self._context.verbose_graph else 'point',
                               style='' if self._context.verbose_graph else 'invis')

    def __ensure_rank_exists(self, rank: int):
        """Ensures there are sufficient rank nodes to use the specified rank."""
        if self._last_rank is None:
            self._last_rank = 0
            name = self.__draw_rank_node()
            self._rank_nodes[self._last_rank] = name
        while self._last_rank < rank:
            self._last_rank += 1
            name = self.__draw_rank_node()
            self._rank_nodes[self._last_rank] = name
            if self._last_rank > 0:
                self._draw_edge(self._rank_nodes[self._last_rank - 1], name,
                                style='' if self._context.verbose_graph else 'invis')

    def __draw_rank_edge(self, node: str, topic: str, event: Event, base_rank: int, adjust_depth: bool) -> int:
        rank: int = base_rank
        if adjust_depth:
            rank += self._context.info.get_topic_taught_depth(topic, event)
        self._node_ranks[node] = rank
        if rank > 0:
            self.__ensure_rank_exists(rank - 1)
            self._draw_edge(self._rank_nodes[rank - 1], node, style='' if self._context.verbose_graph else 'invis')
        return rank

    def _draw_event(self, event: Event, start_rank: int) -> int:
        max_rank: int | None = None
        return max_rank

    def _draw_id(self, event_id, start_rank, unit) -> int:
        max_rank: int | None = None
        for event in self._context.info.grouped_events[unit][event_id].values():
            rank = self._draw_event(event, start_rank)
            if max_rank is None or rank > max_rank:
                max_rank = rank
        if max_rank is None:
            raise ValueError('Rank error: event id had no rank')
        return max_rank + 1
