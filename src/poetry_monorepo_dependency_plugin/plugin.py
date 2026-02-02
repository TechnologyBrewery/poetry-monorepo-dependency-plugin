import copy
from typing import Mapping

import cleo.events.console_command_event
import cleo.events.console_events
import cleo.events.event_dispatcher
import cleo.io.io
import poetry.console.application
import poetry.plugins.application_plugin

from cleo.helpers import option
from poetry.console.commands.build import BuildCommand
from poetry.console.commands.publish import PublishCommand
from poetry_plugin_export.command import ExportCommand

from .path_dependency_rewriter import PathDependencyRewriter
from .path_dependency_remover import PathDependencyRemover
from .path_filtering_exporter import PathFilteringExporter

_version_pinning_strategy = option(
    "version-pinning-strategy",
    "s",
    "Stategy to use for rewriting any path dependencies to other Poetry projects "
    "as versioned dependencies",
    flag=False,
    default="mixed",
)
"""
Strategy by which path dependencies to other Poetry projects will be versioned in generated archives.  Valid options 
include 'semver', 'exact', and 'mixed', with the default being 'mixed'.  Given a path dependency to a Poetry project 
with version '1.2.3', the version of the dependency referenced in the generated archive is '^1.2.3' for 
'semver' and '=1.2.3' for 'exact'.  

'mixed' mode switches versioning strategies based on whether or not the dependency
Poetry project version is an in-flight development version or a release:

If a development version (i.e. '1.2.3.dev456'), a variant of 'semver' is used that applies an upper-bound of the next 
patch version (i.e. '>=1.2.3.dev,<1.2.4') 
If a release version (i.e. '1.2.3'), 'exact' is applied (i.e. '=1.2.3').   
"""


class BuildWithVersionedPathDepsCommand(BuildCommand):
    name = "build-rewrite-path-deps"
    description = (
        "Extends the 'build' command to generate archives in which path dependencies to "
        "other Poetry projects are re-written as versioned package dependencies that are "
        "resolvable via a private package repository source"
    )
    options = [*BuildCommand.options, _version_pinning_strategy]

    def handle(self) -> int:
        path_dependency_writer = PathDependencyRewriter(
            self.option("version-pinning-strategy")
        )
        path_dependency_writer.update_dependency_group(
            self.io, self.poetry.pyproject, self.poetry.package.dependency_group("main")
        )
        return super().handle()


class PublishWithVersionedPathDepsCommand(PublishCommand):
    name = "publish-rewrite-path-deps"
    description = (
        "Extends the 'publish' command to build (if specified via the --build option) and publish archives "
        "in which path dependencies to other Poetry projects are re-written as versioned package "
        "dependencies that are resolvable via a private package repository source"
    )
    options = [*PublishCommand.options, _version_pinning_strategy]

    def handle(self) -> int:
        path_dependency_writer = PathDependencyRewriter(
            self.option("version-pinning-strategy")
        )
        path_dependency_writer.update_dependency_group(
            self.io, self.poetry.pyproject, self.poetry.package.dependency_group("main")
        )
        return super().handle()


class ExportWithoutPathDepsCommand(ExportCommand):
    name = "export-without-path-deps"
    description = (
        "Extends the 'export' command to generate exports in which path dependencies to "
        "other Poetry projects are removed from package dependencies."
    )

    # Supported export formats for this command. pylock.toml is not supported because
    # it embeds path dependencies as structured TOML data rather than file:// URLs,
    # requiring different filtering logic that is not yet implemented.
    SUPPORTED_FORMATS = (
        PathFilteringExporter.FORMAT_REQUIREMENTS_TXT,
        PathFilteringExporter.FORMAT_CONSTRAINTS_TXT,
    )

    def handle(self) -> int:
        """
        Handle the export command using PathFilteringExporter to exclude path dependencies.

        This overrides the parent's handle() method to use a custom exporter that
        filters out file:// URLs (path dependencies) from the export output.
        This is necessary because poetry-plugin-export 1.9.0+ reads from poetry.lock
        instead of the in-memory dependency group.

        Note: This method largely duplicates ExportCommand.handle() because the parent
        class does not provide a factory method or hook for customizing the Exporter
        class. Changes to the parent's handle() in future poetry-plugin-export versions
        may need to be manually synchronized here.
        """
        from pathlib import Path

        from packaging.utils import NormalizedName
        from packaging.utils import canonicalize_name

        fmt = self.option("format")

        if fmt not in self.SUPPORTED_FORMATS:
            supported = ", ".join(self.SUPPORTED_FORMATS)
            self.line_error(
                f"<error>export-without-path-deps only supports: {supported}</error>"
            )
            return 1

        if not PathFilteringExporter.is_format_supported(fmt):
            raise ValueError(f"Invalid export format: {fmt}")

        output = self.option("output")

        locker = self.poetry.locker
        if not locker.is_locked():
            self.line_error("<comment>The lock file does not exist. Locking.</comment>")
            options = []
            if self.io.is_debug():
                options.append(("-vvv", None))
            elif self.io.is_very_verbose():
                options.append(("-vv", None))
            elif self.io.is_verbose():
                options.append(("-v", None))

            self.call("lock", " ".join(options))

        if not locker.is_fresh():
            self.line_error(
                "<error>"
                "pyproject.toml changed significantly since poetry.lock was last"
                " generated. Run `poetry lock` to fix the lock file."
                "</error>"
            )
            return 1

        if self.option("extras") and self.option("all-extras"):
            self.line_error(
                "<error>You cannot specify explicit"
                " `<fg=yellow;options=bold>--extras</>` while exporting"
                " using `<fg=yellow;options=bold>--all-extras</>`.</error>"
            )
            return 1

        extras: list[NormalizedName]
        if self.option("all-extras"):
            extras = list(self.poetry.package.extras.keys())
        else:
            extras = [
                canonicalize_name(extra)
                for extra_opt in self.option("extras")
                for extra in extra_opt.split()
            ]
            invalid_extras = set(extras) - self.poetry.package.extras.keys()
            if invalid_extras:
                raise ValueError(
                    f"Extra [{', '.join(sorted(invalid_extras))}] is not specified."
                )

        if (
            self.option("with") or self.option("without") or self.option("only")
        ) and self.option("all-groups"):
            self.line_error(
                "<error>You cannot specify explicit"
                " `<fg=yellow;options=bold>--with</>`, "
                "`<fg=yellow;options=bold>--without</>`, "
                "or `<fg=yellow;options=bold>--only</>` "
                "while exporting using `<fg=yellow;options=bold>--all-groups</>`.</error>"
            )
            return 1

        groups = (
            self.poetry.package.dependency_group_names(include_optional=True)
            if self.option("all-groups")
            else self.activated_groups
        )

        # Use PathFilteringExporter instead of the default Exporter
        exporter = PathFilteringExporter(self.poetry, self.io)
        exporter.only_groups(list(groups))
        exporter.with_extras(extras)
        exporter.with_hashes(not self.option("without-hashes"))
        exporter.with_credentials(self.option("with-credentials"))
        exporter.with_urls(not self.option("without-urls"))
        exporter.export(fmt, Path.cwd(), output or self.io)

        return 0


class MonorepoDependencyPlugin(poetry.plugins.application_plugin.ApplicationPlugin):
    # Standard Poetry commands that this plugin intercepts when enabled
    COMMANDS = (
        BuildCommand,
        PublishCommand,
        ExportCommand,
    )

    # Custom commands provided by this plugin that handle their own rewriting
    # and should not be intercepted by the event listener
    CUSTOM_COMMANDS = (
        BuildWithVersionedPathDepsCommand,
        PublishWithVersionedPathDepsCommand,
        ExportWithoutPathDepsCommand,
    )

    def __init__(self):
        self.plugin_config = None
        self.poetry = None

    def activate(self, application: poetry.console.application.Application):
        application.command_loader.register_factory(
            "build-rewrite-path-deps", lambda: BuildWithVersionedPathDepsCommand()
        )
        application.command_loader.register_factory(
            "publish-rewrite-path-deps", lambda: PublishWithVersionedPathDepsCommand()
        )
        application.command_loader.register_factory(
            "export-without-path-deps", lambda: ExportWithoutPathDepsCommand()
        )

        try:
            local_poetry_proj_config = application.poetry.pyproject.data
        except Exception:
            # We're not in a valid Poetry project directory
            return

        plugin_config = _merge_dicts(
            _default_plugin_config(), local_poetry_proj_config
        )["tool"]["poetry-monorepo-dependency-plugin"]

        # If the [tool.poetry-monorepo-dependency-plugin.enable] flag has not been set
        # in pyproject.toml, do *not* intercept and modify build/publish commands
        if not plugin_config["enable"]:
            return

        application.event_dispatcher.add_listener(
            cleo.events.console_events.COMMAND,
            self.event_listener,
        )
        self.poetry = application.poetry
        self.plugin_config = plugin_config

    def event_listener(
        self,
        event: cleo.events.console_command_event.ConsoleCommandEvent,
        event_name: str,
        dispatcher: cleo.events.event_dispatcher.EventDispatcher,
    ) -> None:
        # Don't intercept our own custom commands (that handle their own rewriting)
        if isinstance(event.command, self.CUSTOM_COMMANDS):
            return

        if not isinstance(event.command, self.COMMANDS):
            return

        event.io.write_line(
            "Intercepting the command: " + str(event.command.__class__),
            verbosity=cleo.io.outputs.output.Verbosity.DEBUG,
        )

        if isinstance(event.command, ExportCommand):
            path_dependency_remover = PathDependencyRemover()
            path_dependency_remover.update_dependency_group(
                event.io,
                self.poetry.pyproject,
                self.poetry.package.dependency_group("main"),
            )
        else:
            path_dependency_writer = PathDependencyRewriter(
                self.plugin_config["version-pinning-strategy"]
            )
            path_dependency_writer.update_dependency_group(
                event.io,
                self.poetry.pyproject,
                self.poetry.package.dependency_group("main"),
            )


def _default_plugin_config() -> Mapping:
    """
    Provides the default pyproject.toml configuration for this plugin, automatically
    opting out projects and (if enabled) setting the pinning strategy to "mixed"
    :return:
    """
    return {
        "tool": {
            "poetry-monorepo-dependency-plugin": {
                "enable": False,
                "version-pinning-strategy": "mixed",
            }
        }
    }


def _merge_dicts(base: Mapping, addition: Mapping) -> Mapping:
    """
    Helper method for merging pyproject.toml configurations together. This allows us to
    easily overlay a developer-specified pyproject.toml configuration with the default
    configurations provided by _default_plugin_config().

    :param base: base configuration dictionary into which the other given dictionary will be merged.
    :param addition: dictionary that will be merged into the base and overwrite as necessary.
    :return: dictionary in which the addition is merged on top of the base.
    """
    result = dict(copy.deepcopy(base))
    for key, value in addition.items():
        if isinstance(value, dict) and key in base and isinstance(base[key], dict):
            result[key] = _merge_dicts(base[key], value)
        else:
            result[key] = value
    return result
