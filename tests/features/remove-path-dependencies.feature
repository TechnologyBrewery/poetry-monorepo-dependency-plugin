Feature: Remove path dependencies from Poetry projects

  Scenario Outline: Remove project dependencies with paths 
    Given a project with a local path dependencies to other Poetry projects
    When the project is exported using the plugin's command-line mode
    Then the path dependencies for "<dependency name>" are removed from poetry dependencies
    Examples:
      | dependency name
      | spam
      | spam
      | spam
      | ham
      | ham
      | ham
      | eggs
