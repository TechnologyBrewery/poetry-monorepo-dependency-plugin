import unittest.mock
import unittest
from pathlib import Path

import cleo.io.io
import poetry.core.factory
from behave import *
import nose.tools as nt

from poetry_monorepo_dependency_plugin.path_dependency_remover import (
    PathDependencyRemover,
)


@given("a project with a local path dependencies to other Poetry projects")
def step_impl(context):
    project_with_local_deps = poetry.core.factory.Factory().create_poetry(
        Path(__file__).parents[2] / "resources/project-with-local-dependencies"
    )
    context.project_with_local_deps = project_with_local_deps


@when("the project is built using the plugin's command-line mode")
def step_impl(context):
    path_dependency_remover = PathDependencyRemover()
    mock_io = unittest.mock.create_autospec(cleo.io.io.IO)
    path_dependency_remover.update_dependency_group(
        mock_io,
        context.project_with_local_deps.pyproject,
        context.project_with_local_deps.package.dependency_group("main"),
    )


@then(
    'the path dependencies for "{dependency_name}" are no longer present in the pyproject.toml'
)
def step_impl(context, dependency_name):
    mydependencies = context.project_with_local_deps.package.dependency_group(
        "main"
    ).dependencies

    nt.assert_not_in(
        dependency_name,
        mydependencies,
        f"Found the path dependency {dependency_name}",
    )
