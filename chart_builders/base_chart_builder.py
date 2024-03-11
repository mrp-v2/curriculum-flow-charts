from graphviz import Digraph

from util.chart_context import ChartContext


class BaseChartBuilder:
    """The base class for chart builders."""

    def __init__(self, context: ChartContext, chart_name: str):
        """
        :param context: The ChartContext to use for this builder.
        :param chart_name: The name of this chart.
        """
        self._context = context
        """The ChartContext for this chart builder."""
        self._graph: Digraph = Digraph(chart_name)
        """The main graph object for the chart."""
        self.__nodes_drawn: list[str] = []
        """Tracks all the nodes drawn to prevent duplicate nodes."""
        self.__edges_drawn: list[tuple[str, str]] = []
        """Tracks all edges drawn to prevent duplicate edges."""

    def _draw_node(self, node: str, label: str = None, parent_graph: Digraph = None, _attributes=None, **attrs) -> str:
        """
        Draws a node inside parent_graph, after making sure the node hasn't already been drawn.
        :param node: The qualified name of the node to draw.
        :param label: The display name of the node. Defaults to the name of the node.
        :param parent_graph: The graph to draw the node under. Defaults to the main graph.
        :param _attributes: Any attributes to give the node.
        :param attrs: More attributes to give the node.
        :return: The qualified name of the node.
        """
        if parent_graph is None:
            parent_graph = self._graph
        if node not in self.__nodes_drawn:
            parent_graph.node(node, label if label else node, _attributes if _attributes else attrs)
        return node

    def _draw_edge(self, tail: str, head: str, **attrs):
        """
        Draws an edge connecting two nodes. Does nothing if the edge has already been drawn.
        :param tail: The qualified name of the tail node.
        :param head: The qualified name of the head node.
        """
        if (tail, head) not in self.__edges_drawn:
            self._graph.edge(tail, head, None, attrs)
            self.__edges_drawn.append((tail, head))

    def label(self, label: str):
        """
        Sets the label for the graph.
        :param label: The label for the graph.
        """
        self._graph.attr(label=label)

    def finish(self):
        """
        Finalizes the graph and returns it.
        """
        return self._graph
