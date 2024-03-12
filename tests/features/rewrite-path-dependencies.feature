Feature: Re-write path dependencies to Poetry projects as versioned package dependencies

  Scenario Outline: Re-written dependency version changes based on selected version pinning strategy
    Given a project with a local path dependencies to other Poetry projects
    When the project is built using the plugin's command-line mode with the configured "<version pinning strategy>"
    Then the re-written dependency version for "<dependency name>" becomes "<pinned version>"
    Examples:
      | dependency name | version pinning strategy | pinned version     |
      | spam            | mixed                    | >=1.2.3.dev,<1.2.4 |
      | spam            | exact                    | 1.2.3.dev          |
      | spam            | semver                   | ^1.2.3.dev         |
      | ham             | mixed                    | 4.5.6              |
      | ham             | exact                    | 4.5.6              |
      | ham             | semver                   | ^4.5.6             |
      | eggs            | mixed                    | >=1.0rc4,<1.0.1    |