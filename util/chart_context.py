from pathlib import Path
from typing import Literal

from util import Event, Topic
from util.dependency_info import DependencyInfo

Flag = Literal['verbose_graph']
"""The different option flags that can be used."""


class ChartContext:
    """
    Stores information about the context for a chart.
    """

    def __init__(self, info: DependencyInfo, output_dir: Path, output_prefix: str | None, flags: list[Flag],
                 focus_event: Event | None = None, focus_topic: Topic | None = None):
        """
        :param info: The `DependencyInfo` to use to create the chart.
        :param output_dir: The directory to save the chart to.
        :param output_prefix: An optional prefix to prepend the chart's filename with.
        :param flags: A list of `Flag` to use when creating the chart.
        :param focus_event: An optional event to focus on. Only relevant for some chart types.
        :param focus_topic: An optional topic to focus on. Only relevant for some chart types.
        """
        self.info = info
        """The DependencyInfo for the chart."""
        self.output_dir = output_dir
        """The output directory for the chart."""
        self.__output_prefix = output_prefix
        """A prefix to prepend to the output file."""
        self.focus_event = focus_event
        """The focus event of the chart, if applicable."""
        self.focus_topic = focus_topic
        """The focus topic of the chart, if applicable."""
        self.verbose_graph = 'verbose_graph' in flags
        """Whether to draw extra debug information on in the chart. Only has an effect on charts that support it."""

    def get_chart_file(self, chart_name: str) -> str:
        """
        Determines the output file for a chart.
        :param chart_name: The name of the chart.
        :return: The name of the output file.
        """
        return (self.__output_prefix if self.__output_prefix else '') + chart_name
