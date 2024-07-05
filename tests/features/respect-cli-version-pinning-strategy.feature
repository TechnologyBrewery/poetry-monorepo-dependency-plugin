Feature: Respect command-line version pinning strategy for custom commands

  The plugin provides custom commands (build-rewrite-path-deps, publish-rewrite-path-deps)
  that accept a --version-pinning-strategy option. When the plugin is enabled in
  pyproject.toml, the event listener should NOT intercept these custom commands,
  allowing the command-line strategy to take effect.

  Scenario: Event listener skips custom build command
    Given a plugin instance with an enabled configuration
    And a mock BuildWithVersionedPathDepsCommand event
    When the event listener processes the event
    Then the event listener should return early without modifying dependencies

  Scenario: Event listener skips custom publish command
    Given a plugin instance with an enabled configuration
    And a mock PublishWithVersionedPathDepsCommand event
    When the event listener processes the event
    Then the event listener should return early without modifying dependencies

  Scenario: Event listener still intercepts standard build command
    Given a plugin instance with an enabled configuration
    And a mock standard BuildCommand event
    When the event listener processes the event
    Then the event listener should intercept and modify dependencies

  Scenario: Event listener still intercepts standard publish command
    Given a plugin instance with an enabled configuration
    And a mock standard PublishCommand event
    When the event listener processes the event
    Then the event listener should intercept and modify dependencies

  Scenario: Event listener skips custom export command
    Given a plugin instance with an enabled configuration
    And a mock ExportWithoutPathDepsCommand event
    When the event listener processes the event
    Then the event listener should return early without modifying dependencies

  Scenario: Event listener still intercepts standard export command
    Given a plugin instance with an enabled configuration
    And a mock standard ExportCommand event
    When the event listener processes the event
    Then the event listener should intercept and remove path dependencies
