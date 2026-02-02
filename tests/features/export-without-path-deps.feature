Feature: Export requirements without path dependencies

  The export-without-path-deps command should produce a requirements.txt
  that excludes all path dependencies (local directory references).
  This is essential for creating portable requirements files that can be
  used in environments where the local path dependencies don't exist.

  Issue #47: poetry-plugin-export 1.9.0+ reads from poetry.lock instead of
  the in-memory dependency group, so path dependencies must be filtered
  at the export level.

  Test data: The test project (project-with-local-dependencies) has path
  dependencies to local sibling directories (ham, eggs, spam) plus a
  regular PyPI dependency (packaging). Path dependencies appear as
  file:// URLs in the export output and must be filtered out, while
  regular dependencies must be preserved.

  Scenario: Exported requirements.txt should not contain path dependencies
    Given a Poetry project with path dependencies and a lock file
    When the project is exported to requirements.txt using export-without-path-deps
    Then the exported output should not contain any file:// URLs
    And the exported output should contain non-path dependencies

  Scenario: Exported constraints.txt should not contain path dependencies
    Given a Poetry project with path dependencies and a lock file
    When the project is exported to constraints.txt using export-without-path-deps
    Then the exported output should not contain any file:// URLs
    And the exported output should contain non-path dependencies
