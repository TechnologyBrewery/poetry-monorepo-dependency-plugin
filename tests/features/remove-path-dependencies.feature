Feature: Remove path dependencies from Poetry projects

  Scenario Outline: Remove project dependencies with paths 
    Given a project with a local path dependencies to other Poetry projects
    When the project is built using the plugin's command-line mode
    Then the path dependencies for "<dependency name>" are no longer present in the pyproject.toml
    Examples:
      | dependency name
      | spam
      | spam
      | spam
      | ham
      | ham
      | ham
      | eggs
