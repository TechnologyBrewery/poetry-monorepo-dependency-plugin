# Poetry Monorepo Dependency Plugin

[![PyPI](https://img.shields.io/pypi/v/poetry-monorepo-dependency-plugin)](https://pypi.org/project/poetry-monorepo-dependency-plugin/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/poetry-monorepo-dependency-plugin)
![PyPI - Wheel](https://img.shields.io/pypi/wheel/poetry-monorepo-dependency-plugin)
[![License](https://img.shields.io/github/license/mashape/apistatus.svg)](https://opensource.org/licenses/mit)

Forked and inspired by the [poetry-stickywheel-plugin](https://github.com/artisanofcode/poetry-stickywheel-plugin), this
Poetry[poetry] plugin facilitates the usage of more complex monorepo project structures by pinning version dependencies when 
building and publishing archives with local path dependencies to other Poetry projects within the same monorepo.

## Installation

```
poetry self add poetry-monorepo-dependency-plugin
```

If you want to activate `poetry-monorepo-dependency-plugin` for all [build][poetry-build] and
[publish][poetry-publish] command invocations, add the following to your project's `pyproject.toml`
that has path dependencies to other Poetry projects:

```toml
[tool.poetry-monorepo-dependency-plugin]
enable = true
```

## Usage

During archive building or publishing, this plugin will rewrite [path dependencies](https://python-poetry.org/docs/dependency-specification/#path-dependencies) 
to other Poetry projects using the corresponding pinned version dependency extracted from the referenced project's `pyproject.toml`.
The extracted dependency version will be applied to the generated archive using the strategy specified in the `version-pinning-strategy`
configuration.  By referencing pinned version dependencies in published archive files, package consumers may more easily depend on
and install packages that are built within complex monorepos, without needing to replicate the exact folder structure utilized within
the monorepo for that project's dependencies.

For example, assume that `spam` and `ham` Poetry projects exist within the same monorepo and use the following `pyproject.toml`
configurations.

`spam/pyproject.toml`:
```toml
[tool.poetry]
name = "spam"
version = "0.1.0"

[tool.poetry.dependencies]
ham = {path = "../ham", develop = true}
```

`ham/pyproject.toml`:
```
[tool.poetry]
name = "ham"
version = "1.2.3"
```
When generating `wheel` or `sdist` archives for the `spam` project through Poetry's [build][poetry-build] or 
[publish][poetry-publish] commands, the corresponding `spam` package will be constructed as if its dependency on the
`ham` project were declared as `ham = "1.2.3"`.  As a result, package metadata in archives for `spam` will shift from
`Requires-Dist: ham @ ../ham` to `Requires-Dist: ham (==1.2.3)`

### Command line mode

If you need greater control over when `poetry-monorepo-dependency-plugin` is activated, this plugin exposes new `build-rewrite-path-deps`
and `publish-rewrite-path-deps` Poetry commands for on-demand execution.  For example, it may be desirable to only use this
plugin during CI to support a monorepo's artifact deployment and/or release process.  When these custom Poetry commands are invoked, 
any configuration defined in the project's `pyproject.toml` `[tool.poetry-monorepo-dependency-plugin]` section is ignored and all options
(other than `enable`) are exposed as command line options.  For example:
```commandline
poetry build-rewrite-path-deps --version-pinning-strategy=semver
```

### Configuration

The following configuration options are supported within your project's `pyproject.toml` configuration:

* `[tool.poetry-monorepo-dependency-plugin]`: Parent-level container for plugin
  * `enable` (`boolean`, default: `false`): Since Poetry plugins are globally installed, this configuration allows projects
to opt-in to this plugin's modifications of the archives built and/or published Poetry
  * `version-pinning-strategy` (`string`, default: `mixed`, options: `mixed`, `semver`, `exact`): Strategy by which path 
dependencies to other Poetry projects will be versioned in generated archives. Given a path dependency to a Poetry project 
with version `1.2.3`, the version of the dependency referenced in the generated archive is `^1.2.3` for 
`semver` and `=1.2.3` for `exact`.  `mixed` mode switches versioning strategies based on whether the dependency
Poetry project version is an in-flight development version or a release - if a development version (i.e. `1.2.3.dev456`),
`semver` is applied (i.e. `^1.2.3dev`), and if a release version (i.e. `1.2.3`), `exact` is applied (i.e. `=1.2.3`).
  
## Licence

`poetry-monorepo-dependency-plugin` is available under the [MIT licence][mit_licence].

## Releasing to PyPI

Releasing `poetry-monorepo-dependency-plugin` relies on the [maven-release-plugin](https://maven.apache.org/maven-release/maven-release-plugin/)
to automate manual release activities and [Habushu](https://bitbucket.org/cpointe/habushu/) to automate the execution of a
Poetry-based DevOps workflow via a custom Maven lifecycle.  During Maven's `deploy` phase, the appropriate plugin packages
will be published to PyPI.  

A [PyPI account](https://pypi.org/account/register/) with access to the [poetry-monorepo-dependency-plugin](https://pypi.org/project/poetry-monorepo-dependency-plugin/) 
project is required. PyPI account credentials should be specified in your `settings.xml` under the `<id>pypi</id>` `<server>` entry:

```xml
<settings>
  <servers>
    <server>
      <id>pypi</id>
      <username>pypi-username</username>
      <password>{encrypted-pypi-password}</password>
    </server>
  </servers>
</settings>
```
Execute `mvn release:clean release:prepare`, answer the prompts for the versions and tags, and execute `mvn release:perform` to publish
the package to PyPI. 

[poetry]: https://python-poetry.org/
[poetry-build]: https://python-poetry.org/docs/cli/#build
[poetry-publish]: https://python-poetry.org/docs/cli/#publish
[mit_licence]: http://dan.mit-license.org/