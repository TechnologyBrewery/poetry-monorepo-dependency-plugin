import unittest.mock
from pathlib import Path

import cleo.events.console_command_event
import cleo.events.event_dispatcher
import cleo.io.io
import poetry.core.factory
from behave import given, when, then
from poetry.console.commands.build import BuildCommand
from poetry.console.commands.publish import PublishCommand
from poetry_plugin_export.command import ExportCommand

from poetry_monorepo_dependency_plugin.plugin import (
    MonorepoDependencyPlugin,
    BuildWithVersionedPathDepsCommand,
    PublishWithVersionedPathDepsCommand,
    ExportWithoutPathDepsCommand,
)


# Concrete stub classes for testing isinstance checks
# These are minimal subclasses that work correctly with isinstance()
class StubBuildWithVersionedPathDepsCommand(BuildWithVersionedPathDepsCommand):
    """Test stub for BuildWithVersionedPathDepsCommand."""

    def __init__(self):
        pass  # Skip parent __init__ to avoid Poetry dependencies


class StubPublishWithVersionedPathDepsCommand(PublishWithVersionedPathDepsCommand):
    """Test stub for PublishWithVersionedPathDepsCommand."""

    def __init__(self):
        pass


class StubExportWithoutPathDepsCommand(ExportWithoutPathDepsCommand):
    """Test stub for ExportWithoutPathDepsCommand."""

    def __init__(self):
        pass


class StubBuildCommand(BuildCommand):
    """Test stub for standard BuildCommand."""

    def __init__(self):
        pass


class StubPublishCommand(PublishCommand):
    """Test stub for standard PublishCommand."""

    def __init__(self):
        pass


class StubExportCommand(ExportCommand):
    """Test stub for standard ExportCommand."""

    def __init__(self):
        pass


@given("a plugin instance with an enabled configuration")
def given_plugin_with_enabled_config(context):
    """Set up a plugin instance with enabled configuration."""
    plugin = MonorepoDependencyPlugin()

    # Load test project
    project_with_local_deps = poetry.core.factory.Factory().create_poetry(
        Path(__file__).parents[2] / "resources/project-with-local-dependencies"
    )

    plugin.poetry = project_with_local_deps
    plugin.plugin_config = {
        "enable": True,
        "version-pinning-strategy": "mixed",
    }

    context.plugin = plugin
    context.project_with_local_deps = project_with_local_deps


@given("a mock BuildWithVersionedPathDepsCommand event")
def given_mock_build_custom_command_event(context):
    """Create a mock event with BuildWithVersionedPathDepsCommand."""
    context.mock_event = _create_mock_event(StubBuildWithVersionedPathDepsCommand())


@given("a mock PublishWithVersionedPathDepsCommand event")
def given_mock_publish_custom_command_event(context):
    """Create a mock event with PublishWithVersionedPathDepsCommand."""
    context.mock_event = _create_mock_event(StubPublishWithVersionedPathDepsCommand())


@given("a mock ExportWithoutPathDepsCommand event")
def given_mock_export_custom_command_event(context):
    """Create a mock event with ExportWithoutPathDepsCommand."""
    context.mock_event = _create_mock_event(StubExportWithoutPathDepsCommand())


@given("a mock standard BuildCommand event")
def given_mock_standard_build_command_event(context):
    """Create a mock event with standard BuildCommand."""
    context.mock_event = _create_mock_event(StubBuildCommand())


@given("a mock standard PublishCommand event")
def given_mock_standard_publish_command_event(context):
    """Create a mock event with standard PublishCommand."""
    context.mock_event = _create_mock_event(StubPublishCommand())


@given("a mock standard ExportCommand event")
def given_mock_standard_export_command_event(context):
    """Create a mock event with standard ExportCommand."""
    context.mock_event = _create_mock_event(StubExportCommand())


@when("the event listener processes the event")
def when_event_listener_processes_event(context):
    """Call the event listener with the mock event."""
    mock_dispatcher = unittest.mock.create_autospec(
        cleo.events.event_dispatcher.EventDispatcher
    )

    # Track if PathDependencyRewriter or PathDependencyRemover was called
    with (
        unittest.mock.patch(
            "poetry_monorepo_dependency_plugin.plugin.PathDependencyRewriter"
        ) as mock_rewriter,
        unittest.mock.patch(
            "poetry_monorepo_dependency_plugin.plugin.PathDependencyRemover"
        ) as mock_remover,
    ):
        context.plugin.event_listener(
            context.mock_event,
            "console.command",
            mock_dispatcher,
        )
        context.rewriter_called = mock_rewriter.called
        context.remover_called = mock_remover.called


@then("the event listener should return early without modifying dependencies")
def then_event_listener_returns_early(context):
    """Verify the event listener did not modify dependencies."""
    assert not context.rewriter_called and not context.remover_called, (
        "Neither PathDependencyRewriter nor PathDependencyRemover should have been called for custom commands"
    )


@then("the event listener should intercept and modify dependencies")
def then_event_listener_intercepts(context):
    """Verify the event listener intercepted and modified dependencies."""
    assert context.rewriter_called, (
        "PathDependencyRewriter should have been called for standard commands"
    )


@then("the event listener should intercept and remove path dependencies")
def then_event_listener_removes_deps(context):
    """Verify the event listener intercepted and removed path dependencies."""
    assert context.remover_called, (
        "PathDependencyRemover should have been called for standard export command"
    )


def _create_mock_event(command):
    """Helper to create a mock ConsoleCommandEvent with a real command instance."""
    mock_event = unittest.mock.create_autospec(
        cleo.events.console_command_event.ConsoleCommandEvent
    )
    mock_event.command = command
    mock_event.io = unittest.mock.create_autospec(cleo.io.io.IO)
    return mock_event
