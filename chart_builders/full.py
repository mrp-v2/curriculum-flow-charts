from graphviz import Digraph

from chart_builders.event import EventChartBuilder
from util import Event, qualify, Side
from util.chart_context import ChartContext


class FullChartBuilder(EventChartBuilder):
    def __init__(self, context: ChartContext):
        super().__init__(context, chart_name='full')
        self._graph.attr(splines='ortho', ranksep='1')

    def __draw_sided_topic_and_dependencies(self, topic: str, event: Event, default_side: Side, base_rank: int) -> \
            tuple[str, int]:
        head = self._draw_topic_only(topic, event, color=f'{"blue" if default_side == "taught" else ""}')
        rank = self.__draw_rank_edge(head, topic, event, base_rank, default_side == 'taught')
        tail = self.__get_tail_node(topic, event, default_side == 'required')
        if tail is not None:
            rank_dif = rank - self._node_ranks[tail]
            self._draw_edge(tail, head, constraint='False', weight=f'{2 if abs(rank_dif) <= 1 else 1}')
        if default_side == 'taught':
            for dependency in self._context.info.topics[topic].dependencies:
                last_dependency_taught_time = self._context.info.get_most_recent_taught_time(event, dependency, True)
                if last_dependency_taught_time is not None:
                    self._draw_edge(qualify(dependency, last_dependency_taught_time), head,
                                    constraint='False')
        return head, rank

    def _draw_event(self, event: Event, start_rank: int) -> int:
        max_rank: int | None = None
        for topic in event.topics_taught:
            name, rank = self.__draw_sided_topic_and_dependencies(topic, event, 'taught', start_rank)
            if max_rank is None or rank > max_rank:
                max_rank = rank
        for topic in event.topics_required:
            name, rank = self.__draw_sided_topic_and_dependencies(topic, event, 'required', start_rank)
            if max_rank is None or rank > max_rank:
                max_rank = rank
            self._latest_required_times[topic] = event, name
        return max_rank

    def draw_full(self):
        start_rank: int = 0
        for unit in self._context.info.grouped_events:
            start_rank = self._draw_unit(unit, start_rank)

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
