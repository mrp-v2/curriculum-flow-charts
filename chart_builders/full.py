from graphviz import Digraph

from chart_builders.event import EventChartBuilder
from util import Event, qualify, Side
from util.chart_context import ChartContext


class FullChartBuilder(EventChartBuilder):
    def __init__(self, context: ChartContext):
        super().__init__(context, chart_name='full')
        self._graph.attr(splines='ortho', ranksep='1')
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
            return qualify(topic, last_taught_time, 'taught')
        if last_taught_time is None:
            return self._latest_required_times[topic][1]
        # return which is more recent
        if self._latest_required_times[topic][0] < last_taught_time:
            return qualify(topic, last_taught_time, 'taught')
        else:
            return self._latest_required_times[topic][1]

    def __draw_rank_edge(self, node: str, topic: str, event: Event, base_rank: int, adjust_depth: bool) -> int:
        rank: int = base_rank
        if adjust_depth:
            rank += self._context.info.get_topic_taught_depth(topic, event)
        self._node_ranks[node] = rank
        if rank > 0:
            self.__ensure_rank_exists(rank - 1)
            self._draw_edge(self._rank_nodes[rank - 1], node, style='' if self._context.verbose_graph else 'invis')
        return rank

    def __draw_sided_topic_and_dependencies(self, topic: str, event: Event, default_side: Side, base_rank: int) -> \
            tuple[str, int]:
        head = self._draw_topic_only(topic, event, default_side, color=f'{"blue" if default_side == "taught" else ""}')
        rank = self.__draw_rank_edge(head, topic, event, base_rank, default_side == 'taught')
        tail = self.__get_tail_node(topic, event, default_side == 'required')
        if tail is not None:
            rank_dif = rank - self._node_ranks[tail]
            self._draw_edge(tail, head, constraint='False', weight=f'{2 if abs(rank_dif) <= 1 else 1}')
        if default_side == 'taught':
            for dependency in self._context.info.topics[topic].dependencies:
                last_dependency_taught_time = self._context.info.get_most_recent_taught_time(event, dependency)
                if last_dependency_taught_time is not None:
                    self._draw_edge(qualify(dependency, last_dependency_taught_time, 'taught'), head,
                                    constraint='False')
        return head, rank

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

    def __draw_unit(self, unit: int, start_rank: int) -> int:
        for event_id in self._context.info.grouped_events[unit]:
            start_rank = self.__draw_id(event_id, start_rank, unit)
        return start_rank

    def __draw_id(self, event_id, last_id_rank, unit) -> int:
        max_rank: int | None = None
        for event in self._context.info.grouped_events[unit][event_id].values():
            for topic in event.topics_taught:
                name, rank = self.__draw_sided_topic_and_dependencies(topic, event, 'taught', last_id_rank)
                if max_rank is None or rank > max_rank:
                    max_rank = rank
            for topic in event.topics_required:
                name, rank = self.__draw_sided_topic_and_dependencies(topic, event, 'required', last_id_rank)
                if max_rank is None or rank > max_rank:
                    max_rank = rank
                self._latest_required_times[topic] = event, name
        if max_rank is None:
            raise ValueError('Rank error: event id had no rank')
        return max_rank + 1

    def draw_full(self):
        start_rank: int = 0
        for unit in self._context.info.grouped_events:
            start_rank = self.__draw_unit(unit, start_rank)

    def _finish_event(self, event: Event, parent_graph: Digraph, margin: int = 8):
        if event.unit not in self._event_id_graphs:
            self._event_id_graphs[event.unit] = {}
        if event.group_id not in self._event_id_graphs[event.unit]:
            temp = Digraph(f'Unit {event.unit}{f"${event.group_id}" if event.group_id else ""}')
            temp.attr(cluster='True', margin='32', penwidth='3', newrank='True')
            if event.group_id:
                temp.attr(label=event.group_id, style='invis')
            else:
                temp.attr(label=f'Unit {event.unit}', style='rounded')
            self._event_id_graphs[event.unit][event.group_id] = temp
        graph = self._event_graphs[event]
        if graph is not None:
            graph.attr(margin='32', style='dotted')
        return super()._finish_event(event, self._event_id_graphs[event.unit][event.group_id], style='dashed')

    def finish(self):
        super().finish()
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
