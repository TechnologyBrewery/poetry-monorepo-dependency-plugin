from pathlib import Path

from behave import given, when, then
from poetry.factory import Factory

from poetry_monorepo_dependency_plugin.path_filtering_exporter import (
    PathFilteringExporter,
)


@given("a Poetry project with path dependencies and a lock file")
def given_project_with_path_deps_and_lock(context):
    """Set up a Poetry project that has path dependencies and a lock file."""
    project_path = (
        Path(__file__).parents[2] / "resources/project-with-local-dependencies"
    )

    # Use the full Poetry factory to get a Poetry instance with locker support
    context.poetry = Factory().create_poetry(project_path)

    # Verify the lock file exists
    assert context.poetry.locker.is_locked(), (
        f"Lock file not found at {project_path}. Run 'poetry lock' in the test project."
    )


def _create_exporter_and_export(context, export_format):
    """Helper to create exporter and run export in specified format."""
    from cleo.io.io import IO
    from cleo.io.inputs.string_input import StringInput
    from cleo.io.outputs.buffered_output import BufferedOutput

    # Create a proper Cleo IO object with buffered output
    input_obj = StringInput("")
    output_obj = BufferedOutput()
    error_output_obj = BufferedOutput()
    cleo_io = IO(input_obj, output_obj, error_output_obj)

    # Create the path-filtering exporter (the fix for issue #47)
    exporter = PathFilteringExporter(context.poetry, cleo_io)
    exporter.only_groups(["main"])
    exporter.with_hashes(False)

    # Export to specified format - pass cleo_io as output target
    exporter.export(
        export_format,
        context.poetry.pyproject_path.parent,
        cleo_io,
    )

    context.export_output = output_obj.fetch()


@when("the project is exported to requirements.txt using export-without-path-deps")
def when_export_requirements_txt(context):
    """Run the export to requirements.txt format and capture the output."""
    _create_exporter_and_export(context, PathFilteringExporter.FORMAT_REQUIREMENTS_TXT)


@when("the project is exported to constraints.txt using export-without-path-deps")
def when_export_constraints_txt(context):
    """Run the export to constraints.txt format and capture the output."""
    _create_exporter_and_export(context, PathFilteringExporter.FORMAT_CONSTRAINTS_TXT)


@then("the exported output should not contain any file:// URLs")
def then_no_file_urls(context):
    """Verify no file:// URLs are in the export output."""
    assert "file://" not in context.export_output, (
        f"Export output contains file:// URLs (path dependencies):\n{context.export_output}"
    )


@then("the exported output should contain non-path dependencies")
def then_contains_non_path_deps(context):
    """Verify that non-path dependencies (regular PyPI packages) survive filtering."""
    # The test project has 'packaging' as a regular PyPI dependency
    assert "packaging" in context.export_output, (
        f"Export output should contain 'packaging' dependency but got:\n{context.export_output}"
    )
