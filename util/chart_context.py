from pathlib import Path

from util.dependency_info import DependencyInfo


class ChartContext:
    def __init__(self, info: DependencyInfo, output_dir: Path, output_prefix: str | None, flags: list[str]):
        self.info = info
        self.output_dir = output_dir
        self.output_prefix = output_prefix
        self.verbose_graph = 'verbose_graph' in flags

    def get_chart_path(self, chart_name: str) -> Path:
        return self.output_dir / ((self.output_prefix if self.output_prefix else '') + chart_name)
