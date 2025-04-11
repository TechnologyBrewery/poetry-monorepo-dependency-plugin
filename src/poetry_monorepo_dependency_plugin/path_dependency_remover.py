import typing

from cleo.io.io import IO as cleoIO
import cleo.io.outputs.output
from poetry.core.pyproject.toml import PyProjectTOML
from poetry.core.constraints.version import Version
from poetry.core.packages.dependency import Dependency
from poetry.core.packages.directory_dependency import DirectoryDependency
from poetry.core.packages.file_dependency import FileDependency
from poetry.core.packages.dependency_group import DependencyGroup


class PathDependencyRemover:
    """
    Exposes core functionality for gathering a pyproject.toml's path dependencies,
    determining if they are Poetry projects, and if so, extracting the corresponding
    dependency. Handles both directory dependencies (wheels) and file dependencies (sdists).
    """

    def update_dependency_group(
        self,
        io: cleoIO,
        pyproject: PyProjectTOML,
        dependency_group: DependencyGroup,
    ) -> None:
        """
        Removes all path dependencies to Poetry projects.

        :param io: instance of Cleo IO that may be used for logging diagnostic output during
        plugin execution
        :param pyproject: encapsulates the pyproject.toml of the current project for which
        path dependencies will be rewritten
        :param dependency_group: specifies the dependency group from which to pin path
        dependencies, this will usually be "main"
        :return: none
        """
        io.write_line(
            "Updating dependency constraints...",
            verbosity=cleo.io.outputs.output.Verbosity.DEBUG,
        )

        for dependency in dependency_group.dependencies:
            # Handle both DirectoryDependency (wheels) and FileDependency (sdists)
            if not (
                isinstance(dependency, DirectoryDependency)
                or (
                    isinstance(dependency, FileDependency)
                    and dependency.path.endswith(".tar.gz")
                )
            ):
                continue

            io.write_line(
                f"  • Removing {dependency.name} path dependency)",
                verbosity=cleo.io.outputs.output.Verbosity.DEBUG,
            )

            dependency_group.remove_dependency(dependency.name)
