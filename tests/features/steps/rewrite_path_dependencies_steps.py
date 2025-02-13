import unittest.mock
from pathlib import Path
import json

import cleo.io.io
import poetry.core.factory
from behave import given, when, then  # pylint: disable=no-name-in-module
import nose.tools as nt

from poetry_monorepo_dependency_plugin.path_dependency_rewriter import (
    PathDependencyRewriter,
)


@given("a project with a local path dependencies to other Poetry projects")
def step_impl(context):
    project_with_local_deps = poetry.core.factory.Factory().create_poetry(
        Path(__file__).parents[2] / "resources/project-with-local-dependencies"
    )
    context.project_with_local_deps = project_with_local_deps


@when(
    'the project is built using the plugin\'s command-line mode with the configured "{version_pinning_strategy}"'
)
def step_impl(context, version_pinning_strategy):
    path_dependency_rewriter = PathDependencyRewriter(version_pinning_strategy)
    mock_io = unittest.mock.create_autospec(cleo.io.io.IO)
    path_dependency_rewriter.update_dependency_group(
        mock_io,
        context.project_with_local_deps.pyproject,
        context.project_with_local_deps.package.dependency_group("main"),
    )


@then(
    'the re-written dependency version for "{dependency_name}" becomes "{pinned_version}", optional ("{optional}"), with extras: "{extras}"'
)
def step_impl(context, dependency_name, pinned_version, optional, extras):
    rewritten_dependency = None
    for dependency in context.project_with_local_deps.package.dependency_group(
        "main"
    ).dependencies:
        if dependency.name == dependency_name:
            rewritten_dependency = dependency
            break

    nt.assert_is_not_none(
        rewritten_dependency,
        f"Could not find dependency on {dependency_name}",
    )
    nt.assert_equal(
        rewritten_dependency.pretty_constraint,
        pinned_version,
        f"Re-written pinned dependency version for {dependency_name} ({rewritten_dependency.pretty_constraint}) "
        f"did not equal the expected value of {pinned_version}",
    )

    nt.assert_equal(
        rewritten_dependency._in_extras,
        json.loads(extras),
        f"Re-written extra dependency for {dependency_name} ({rewritten_dependency._in_extras}) "
        f"did not equal the expected value of {extras}",
    )

    nt.assert_equal(
        rewritten_dependency._optional,
        json.loads(optional),
        f"Re-written optional status for {dependency_name} ({rewritten_dependency._optional}) "
        f"did not equal the expected value of {optional}",
    )