import unittest.mock

import cleo.io.io
from behave import when, then

from poetry_monorepo_dependency_plugin.path_dependency_remover import (
    PathDependencyRemover,
)


@when("the project is exported using the plugin's command-line mode")
def when_step_impl(context):
    path_dependency_remover = PathDependencyRemover()
    mock_io = unittest.mock.create_autospec(cleo.io.io.IO)
    path_dependency_remover.update_dependency_group(
        mock_io,
        context.project_with_local_deps.pyproject,
        context.project_with_local_deps.package.dependency_group("main"),
    )


@then(
    'the path dependencies for "{dependency_name}" are removed from poetry dependencies'
)
def then_step_impl(context, dependency_name):
    mydependencies = context.project_with_local_deps.package.dependency_group(
        "main"
    ).dependencies

    dependency_names = [dep.name for dep in mydependencies]
    assert dependency_name not in dependency_names, (
        f"Found the path dependency {dependency_name}"
    )
