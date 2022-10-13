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

from .path_dependency_rewriter import PathDependencyRewriter

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
'semver' and '=1.2.3' for 'exact'.  'mixed' mode switches versioning strategies based on whether or not the dependency
Poetry project version is an in-flight development version or a release - if a development version (i.e. '1.2.3.dev456'),
'semver' is applied (i.e. '^1.2.3dev'), and if a release version (i.e. '1.2.3'), 'exact' is applied (i.e. '=1.2.3').   
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
    options = [
        *PublishCommand.options,
        option(
            "rewrite-path-dependencies",
            None,
            "Rewrites any path dependencies as versioned dependencies",
        ),
    ]

    def handle(self) -> int:
        path_dependency_writer = PathDependencyRewriter(
            self.option("version-pinning-strategy")
        )
        path_dependency_writer.update_dependency_group(
            self.io, self.poetry.pyproject, self.poetry.package.dependency_group("main")
        )
        return super().handle()


class MonorepoDependencyPlugin(poetry.plugins.application_plugin.ApplicationPlugin):
    COMMANDS = (
        BuildCommand,
        PublishCommand,
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

        plugin_config = _merge_dicts(
            _default_plugin_config(), application.poetry.pyproject.data
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
        if not isinstance(event.command, self.COMMANDS):
            return

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
