from typing import Callable

from graphviz import Digraph

from chart_builders.base_chart_builder import BaseChartBuilder
from util import Event, qualify
from util.chart_context import ChartContext
from util.topic import Topic, get_dependent_topics


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
        self._graph.attr(splines='ortho', ranksep='1')
        self._event_graphs: dict[Event, Digraph] = {}
        """Stores the sub-graphs for each event."""
        self._event_id_graphs: dict[int, dict[str | None, Digraph]] = {}
        """Stores the parent graph for sub-graphs for each event id"""
        self._latest_required_times: dict[Topic, tuple[Event, str]] = {}
        """Stores the last event in which a topic was required, and the qualified name of the node."""
        self._rank_nodes: dict[int, str] = {}
        """Stores the qualified name of the rank node for each rank"""
        self._last_rank: int | None = None
        """Tracks the number of the last rank node drawn"""
        self._node_ranks: dict[str, int] = {}
        """Tracks the rank of each node"""

    def _draw_topic(self, topic: Topic, event: Event, **attrs) -> str:
        """
        Draws a topic under an event.
        :param topic: The topic to draw.
        :param event: The event to draw the topic under.
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

    def _draw_unit(self, unit: int, start_rank: int) -> int:
        for event_id in self._context.info.grouped_events[unit]:
            start_rank = self._draw_id(event_id, start_rank, unit)
        return start_rank

    def draw(self):
        start_rank: int = 0
        for unit in self._context.info.grouped_events:
            start_rank = self._draw_unit(unit, start_rank)

    def _finish_event(self, event: Event):
        if event.unit not in self._event_id_graphs:
            self._event_id_graphs[event.unit] = {}
        if None not in self._event_id_graphs[event.unit]:
            unit_graph = Digraph(f'Unit {event.unit}')
            unit_graph.attr(cluster='true', margin='16', penwidth='3', newrank='true', label=f'Unit {event.unit}',
                            style='rounded')
            self._event_id_graphs[event.unit][None] = unit_graph
        if event.group_id not in self._event_id_graphs[event.unit]:
            temp = Digraph(f'{event.unit}{event.group_id}')
            temp.attr(cluster='True', penwidth='3', newrank='True', label=event.group_id, style='invis')
            self._event_id_graphs[event.unit][event.group_id] = temp
        graph = self._event_graphs[event]
        graph.attr(style='dashed', label=event.name)
        self._event_id_graphs[event.unit][event.group_id].subgraph(graph)

    def finish(self):
        """
        Finalizes the graph and returns it.
        """
        for event in self._event_graphs:
            self._finish_event(event)
        for unit in self._event_id_graphs:
            if None not in self._event_id_graphs[unit]:
                temp = Digraph(f'Unit {unit}')
                temp.attr(cluster='True')
                temp.attr(label=f'Unit {unit}')
                self._event_id_graphs[unit][None] = temp
            for event_id in self._event_id_graphs[unit]:
                if event_id is None:
                    continue
                self._event_id_graphs[unit][None].subgraph(self._event_id_graphs[unit][event_id])
            self._graph.subgraph(self._event_id_graphs[unit][None])
        return self._graph

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

    def __draw_rank_node(self) -> str:
        return self._draw_node(f'rank_node_{self._last_rank}',
                               shape='ellipse' if self._context.verbose_graph else 'point',
                               color='red' if self._context.verbose_graph else 'invis')

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
                                color='red' if self._context.verbose_graph else 'invis')

    def _draw_rank_edge(self, node: str, base_rank: int, adjust_depth: bool, topic: Topic = None,
                        event: Event = None) -> int:
        rank: int = base_rank
        if adjust_depth:
            if topic is None:
                raise ValueError('If adjust_depth is True, topic should not be None')
            if event is None:
                raise ValueError('If adjust_depth is True, event should not be None')
            rank += event.topic_taught_depth(topic)
        self._node_ranks[node] = rank
        if rank > 0:
            self.__ensure_rank_exists(rank - 1)
            self._draw_edge(self._rank_nodes[rank - 1], node, color='red' if self._context.verbose_graph else 'invis')
        return rank

    def _draw_event(self, event: Event, start_rank: int) -> int | None:
        max_rank: int | None = None
        if event == self._context.focus_event:
            rank = self._draw_focus_event(event, start_rank)
            if rank is not None and (max_rank is None or rank > max_rank):
                max_rank = rank
        elif event < self._context.focus_event:
            rank = self._draw_pre_focus_event(event, start_rank)
            if rank is not None and (max_rank is None or rank > max_rank):
                max_rank = rank
        elif event > self._context.focus_event and not self._context.focus_event.topics_taught:
            return None
        else:
            rank = self._draw_post_focus_event(event, start_rank)
            if max_rank is None or rank > max_rank:
                max_rank = rank
        return max_rank

    def _draw_focus_event(self, event: Event, start_rank: int):
        max_rank: int | None = None
        for topic in event.get_all_topics():
            if topic in event.topics_taught:
                rank = self._draw_topic_and_dependencies(topic, event, start_rank)
                if max_rank is None or rank > max_rank:
                    max_rank = rank
            else:
                head = self._draw_topic(topic, event)
                rank = self._draw_rank_edge(head, start_rank, False)
                if max_rank is None or rank > max_rank:
                    max_rank = rank
                tail = self._get_tail_node(topic, event, False)
                self._draw_edge(tail, head, constraint='false')
                self._latest_required_times[topic] = event, head
        return max_rank

    def _draw_post_focus_event(self, event: Event, start_rank: int) -> int:
        max_rank: int | None = None
        for topic in get_dependent_topics(self._context.focus_event.topics_taught, event.get_all_topics()):
            if topic in event.topics_taught:
                def predicate(dep: Topic):
                    return dep.is_dependent_of_depth(self._context.focus_event.topics_taught)

                rank = self._draw_topic_and_dependencies(topic, event, start_rank, predicate)
                if max_rank is None or rank > max_rank:
                    max_rank = rank
            else:
                head = self._draw_topic(topic, event)
                rank = self._draw_rank_edge(head, start_rank, False)
                if max_rank is None or rank > max_rank:
                    max_rank = rank
                tail = self._get_tail_node(topic, event, False)
                self._draw_edge(tail, head, constraint='false')
                self._latest_required_times[topic] = event, head
        return max_rank

    def _draw_pre_focus_event(self, event: Event, start_rank: int) -> int | None:
        max_rank: int | None = None
        for topic in event.topics_taught:
            if topic.is_dependency_of_depth(self._context.focus_event.get_all_topics()):
                rank = self._draw_topic_and_dependencies(topic, event, start_rank)
                if max_rank is None or rank > max_rank:
                    max_rank = rank
        return max_rank

    def _draw_id(self, event_id, start_rank, unit) -> int:
        max_rank: int | None = None
        for event in self._context.info.grouped_events[unit][event_id].values():
            rank = self._draw_event(event, start_rank)
            if rank is not None and (max_rank is None or rank > max_rank):
                max_rank = rank
        return max_rank + 1 if max_rank is not None else start_rank
