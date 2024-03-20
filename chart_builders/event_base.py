from abc import ABCMeta, abstractmethod
from typing import Callable

from graphviz import Digraph

from chart_builders.base import Base
from util import Event, Topic, qualify
from util.chart_context import ChartContext


class EventBase(Base, metaclass=ABCMeta):
    """
    The base class for chart builders that group topics by event, group id, and unit.
    Provides common functions and behaviors.
    """

    def __init__(self, context: ChartContext, chart_name: str):
        super().__init__(context, chart_name)
        self._graph.attr(splines='ortho', ranksep='1')
        self._event_graphs: dict[Event, Digraph] = {}
        """Stores the sub-graphs for each event."""
        self._group_graphs: dict[int, dict[str | None, Digraph]] = {}
        """Stores the parent graph for sub-graphs for each event id"""
        self._unit_graphs: dict[int, Digraph] = {}
        """Stores the graph for each unit."""
        self._latest_required_times: dict[Topic, tuple[Event, str]] = {}
        """Stores the last event in which a topic was required, and the qualified name of the node."""
        self._rank_nodes: dict[int, str] = {}
        """Stores the qualified name of the rank node for each rank"""
        self._last_rank: int | None = None
        """Tracks the number of the last rank node drawn"""
        self._node_ranks: dict[str, int] = {}
        """Tracks the rank of each node"""

    @abstractmethod
    def _draw_event(self, event, start_rank) -> int | None:
        """
        Draws an event.
        :param event: The event to draw.
        :param start_rank: The rank to start drawing the event on.
        :return: The maximum rank used to draw the event, if anything is drawn.
        """
        pass

    def _draw_group(self, group_id, start_rank, unit) -> int | None:
        """
        Draws an event group.
        :param group_id: The group id to draw.
        :param start_rank: The rank to start drawing the group on.
        :param unit: The unit the group id is in.
        :return: The maximum rank used to draw the group, if anything is drawn.
        """
        max_rank: int | None = None
        for event in self._context.info.grouped_events[unit][group_id].values():
            rank = self._draw_event(event, start_rank)
            if rank is not None and (max_rank is None or rank > max_rank):
                max_rank = rank
        return max_rank

    def _draw_unit(self, unit: int, start_rank: int) -> int | None:
        """
        Draws a unit.
        :param unit: The unit to draw.
        :param start_rank: The rank to start drawing the unit on.
        :return: The maximum rank used to draw the unit, if anything is drawn.
        """
        max_rank: int | None = None
        for event_id in self._context.info.grouped_events[unit]:
            rank = self._draw_group(event_id, start_rank, unit)
            if rank is not None:
                start_rank = rank + 1
                if max_rank is None or rank > max_rank:
                    max_rank = rank
        return max_rank

    def _finish_event(self, event: Event):
        """
        Finalizes the graph for an event, adding it to its group graph.
        Ensures a group graph exists for the event.
        """
        if event.unit not in self._group_graphs:
            self._group_graphs[event.unit] = {}
        if event.group_id not in self._group_graphs[event.unit]:
            temp = Digraph(f'{event.unit}{event.group_id}')
            temp.attr(cluster='True', newrank='true', style='invis')
            self._group_graphs[event.unit][event.group_id] = temp
        graph = self._event_graphs[event]
        graph.attr(style='dashed', label=event.name)
        self._group_graphs[event.unit][event.group_id].subgraph(graph)

    def _finish_group(self, group_id: str, unit: int):
        """
        Finalizes the graph for a group, adding it to its unit graph.
        Ensures a unit graph exists for the group.
        """
        if unit not in self._unit_graphs:
            unit_graph = Digraph(f'Unit {unit}')
            unit_graph.attr(cluster='true', margin='16', penwidth='3', newrank='true', label=f'Unit {unit}',
                            style='rounded')
            self._unit_graphs[unit] = unit_graph
        self._unit_graphs[unit].subgraph(self._group_graphs[unit][group_id])

    def _finish_unit(self, unit: int):
        """
        Finalizes the graph for a unit, adding it to the main graph.
        """
        self._graph.subgraph(self._unit_graphs[unit])

    def __ensure_rank_exists(self, rank: int):
        """
        Ensures there are sufficient rank nodes to use the specified rank.
        :param rank: The rank to ensure exists.
        """
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
                                color='red' if self._context.verbose_graph else 'invis')

    def __draw_rank_node(self) -> str:
        """
        Draws a rank node for the current last rank.
        """
        return self._draw_node(f'rank_node_{self._last_rank}',
                               shape='ellipse' if self._context.verbose_graph else 'point',
                               color='red' if self._context.verbose_graph else 'invis')

    def _draw_rank_edge(self, node: str, base_rank: int, adjust_depth: bool, topic: Topic = None,
                        event: Event = None) -> int:
        """
        Draws an edge setting the rank of a node.
        :param node: The node to set the rank of.
        :param base_rank: The rank to set the node to.
        :param adjust_depth: If true, adjusts the rank based on the topic depth within event.
        :param topic: The topic to use to find the topic depth.
        :param event: The event to use to find the topic depth.
        """
        rank: int = base_rank
        if adjust_depth:
            if topic is None:
                raise ValueError('If adjust_depth is True, topic should not be None')
            if event is None:
                raise ValueError('If adjust_depth is True, event should not be None')
            rank += event.calc_topic_depth(topic)
        self._node_ranks[node] = rank
        if rank > 0:
            self.__ensure_rank_exists(rank - 1)
            self._draw_edge(self._rank_nodes[rank - 1], node, color='red' if self._context.verbose_graph else 'invis')
        return rank

    def finish(self):
        for event in self._event_graphs:
            self._finish_event(event)
        for unit in self._group_graphs:
            for group_id in self._group_graphs[unit]:
                self._finish_group(group_id, unit)
            self._finish_unit(unit)
        return self._graph

    def draw(self):
        start_rank: int = 0
        for unit in self._context.info.grouped_events:
            rank = self._draw_unit(unit, start_rank)
            if rank is not None and (start_rank is None or rank + 1 > start_rank):
                start_rank = rank + 1

    def _draw_topic(self, topic: Topic, event: Event, **attrs) -> str:
        """
        Draws a topic under an event.
        :param topic: The topic to draw.
        :param event: The event to draw the topic under.
        :param attrs: Attributes to add to the topic's node.
        :return: The qualified name of the topic's node.
        """
        qualified_name = qualify(topic, event)
        graph = self._event_graphs.get(event)
        if graph is None:
            graph = Digraph(event.name)
            graph.attr(cluster='True')
            self._event_graphs[event] = graph
        attrs['color'] = 'blue' if topic in event.topics_taught else ''
        return self._draw_node(qualified_name, topic.name, graph, **attrs)

    def _draw_topic_and_dependencies(self, topic: Topic, event: Event, base_rank: int,
                                     dependency_predicate: Callable[[Topic], bool] = None) -> int:
        """
        Draws a node for a topic, and draws edges connecting it to its dependencies.
        :param topic: The topic to draw.
        :param event: The event to draw the topic under.
        :param base_rank: The rank used to start drawing event.
        :param dependency_predicate: An optional predicate to use when deciding whether to draw a connection to a
                                     dependency.
        """
        head = self._draw_topic(topic, event)
        rank = self._draw_rank_edge(head, base_rank, topic in event.topics_taught, topic, event)
        for dependency in topic.dependencies:
            if dependency_predicate is not None and not dependency_predicate(dependency):
                continue
            last_taught_time = self._context.info.get_most_recent_taught_time(event, dependency, True)
            if last_taught_time is not None:
                self._draw_edge(qualify(dependency, last_taught_time), head, constraint='false')
        return rank

    def _get_tail_node(self, topic: Topic, event: Event, include_start: bool) -> str:
        """
        Decides which node should be the tail.
        :param topic: The topic of the head node.
        :param event: The event of the head node.
        :return: The node where topic was most recently taught or required.
        """
        last_taught_time = self._context.info.get_most_recent_taught_time(event, topic, include_start)
        if topic not in self._latest_required_times and last_taught_time is None:
            raise ValueError('topic \'{topic}\' is not in the latest required times list and hasn\'t been taught yet')
        if topic not in self._latest_required_times:
            return qualify(topic, last_taught_time)
        if last_taught_time is None:
            return self._latest_required_times[topic][1]
        # return which is more recent
        if self._latest_required_times[topic][0] < last_taught_time:
            return qualify(topic, last_taught_time)
        else:
            return self._latest_required_times[topic][1]

    def _draw_event_full(self, event, start_rank) -> int:
        """
        Draws an event.
        If a topic is taught, connects it to the last time it was taught or its dependencies.
        If a topic is required, connects it to the last time it was required or the last time it was taught.
        :param event: The event to draw.
        :param start_rank: The rank to start drawing the event on.
        """
        max_rank: int | None = None
        for topic in event.get_all_topics():
            if topic in event.topics_taught:
                rank = self._draw_topic_and_dependencies(topic, event, start_rank)
                if max_rank is None or rank > max_rank:
                    max_rank = rank
            else:
                rank = self._draw_required_topic(event, start_rank, topic)
                if max_rank is None or rank > max_rank:
                    max_rank = rank
        return max_rank

    def _draw_required_topic(self, event, start_rank, topic):
        """
        Draws a topic required by an event.
        Connects it to the last time it was required or the the last time it was taught.
        """
        head = self._draw_topic(topic, event)
        rank = self._draw_rank_edge(head, start_rank, False)
        tail = self._get_tail_node(topic, event, False)
        self._draw_edge(tail, head, constraint='false')
        self._latest_required_times[topic] = event, head
        return rank
