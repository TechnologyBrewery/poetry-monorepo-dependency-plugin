"""
Custom exporter that filters out path dependencies from export output.

This addresses issue #47 where poetry-plugin-export 1.9.0+ reads from poetry.lock
instead of the in-memory dependency group, causing path dependencies to appear
in the export output even when using export-without-path-deps.
"""

from pathlib import Path

from poetry_plugin_export.exporter import Exporter


class PathFilteringExporter(Exporter):
    """
    An Exporter that filters out path dependencies (directory and file dependencies)
    from the exported requirements.

    Path dependencies are identified by checking if the output contains file:// URLs.
    """

    def _filter_path_dependencies(self, content: str) -> str:
        """
        Filter out lines containing file:// URLs (path dependencies).

        Args:
            content: The export content to filter

        Returns:
            Filtered content with path dependencies removed
        """
        filtered_lines = []
        for line in content.splitlines():
            if "file://" not in line:
                filtered_lines.append(line)

        return "\n".join(filtered_lines) + "\n" if filtered_lines else ""

    def _export_requirements_txt(self, out_dir: Path) -> str:
        """
        Export dependencies to requirements.txt format, filtering out path dependencies.

        This overrides the parent method because partialmethod binds to the parent's
        _export_generic_txt at class definition time, so we must override the final
        method directly.
        """
        content = super()._export_generic_txt(
            out_dir, with_extras=True, allow_editable=True
        )
        return self._filter_path_dependencies(content)

    def _export_constraints_txt(self, out_dir: Path) -> str:
        """
        Export dependencies to constraints.txt format, filtering out path dependencies.
        """
        content = super()._export_generic_txt(
            out_dir, with_extras=False, allow_editable=False
        )
        return self._filter_path_dependencies(content)
