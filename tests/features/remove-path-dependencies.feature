Feature: Remove path dependencies from Poetry projects

  Scenario Outline: Remove project dependencies with paths 
    Given a project with a local path dependencies to other Poetry projects
    When the project is built using the plugin's command-line mode
    Then the path dependencies for "<dependency name>" are no longer present in the pyproject.toml
    Examples:
      | dependency name | version pinning strategy | pinned version     |
      | spam            | mixed                    | >=1.2.3.dev,<1.2.4 |
      | spam            | exact                    | 1.2.3.dev          |
      | spam            | semver                   | ^1.2.3.dev         |
      | ham             | mixed                    | 4.5.6              |
      | ham             | exact                    | 4.5.6              |
      | ham             | semver                   | ^4.5.6             |
      | eggs            | mixed                    | >=1.0rc4,<1.0.1    |
