# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)

## [Unreleased]


## [2.1.0] - 2023-04-17

### Added
- CHANGELOG.md file to document all notable changes to this project.
- README.md section on how to get started with gitlab2prov.
- README.md note that gitlab2prov requires a git installation.
- README.md section on dependencies and their respective licenses. See #91 for more details.
- pyproject.toml comments documenting the license information of all dependencies. See #91 for more details.
- Project documentation on how to obtain a GitLab API token.

### Changed
- Tool will check for a git installation and exit with an error message if none is found. See #93 for more details.

### Fixed
- Click package is now listed as a dependency in pyproject.toml. Thank you [@daniel-mohr](https://github.com/daniel-mohr) for reporting this oversight.


## [2.0.0] - 2022-10-31
### Added
- New command line interface composed of multiple subcommands that can be chained together to build any desired gitlab2prov pipeline.
- New YAML configuration file format to specify gitlab2prov pipelines in textual format and save them for later reruns or simple on-the-fly edits.
- JSON-Schema file to check the config file for syntactical errors.
- `bumpversion` support to change the version number with a single command.

### Changed
- New build system that minimizes the number of necessary metadata files.
- New CLI replaces the old CLI.
- New config file format replaces the old config file format.
- Deprecate setup.py, setup.cfg in favor of pyproject.toml. See #70 for more details.

### Fixed
- Tool runs on Windows should no longer trigger WinError 5/267. See #67.
- Special characters such as emojis no longer trigger a UnicodeEncodeError when serializing files. See #66.


## [1.1.4] - 2022-07-18

### Added
- A GitHub workflow to validate the citation file on changes.

### Changed
- Current version and release date in citation file.
 
### Fixed
- Update the start- and endpoint of relations during pseudonymization.  
- User details and agent IDs are pseudonymized using hashing for flexible pseudonymization and merging of provenance graphs (#62).


## [1.1.3] - 2022-07-03

### Fixed
- FileRevision objects that do not have a previous revision no longer lead to a TypeError when serializing the modification model. (see #64)

## [1.1.2] - 2022-07-01

### Fixed
- Disable project features no longer lead to a 403 Forbidden. (see #61)
- Default annotation classifier no longer keys into a dictionary resulting in a KeyError (#63)

## [1.1.1] - 2022-06-27

### Fixed
- Fix a memory bloating issue by not using mutable objects as function argument default value (see #60)
- Fix a spelling mistake in `config.formats` to `config.format`

## [1.1] - 2022-06-12

### Added
- Multi-format support for provenance graph serialization supported by the `multi-format` subcommand. (see #54)
- `outfile` option to section `OUTPUT` in the config file to specify the output file name.
 
### Changed
- README now includes a section about multi-format serialization.
 
## [1.0] - 2022-06-12

### Added
- Qualified relations for relationship types `wasGeneratedBy`, `wasInvalidatedBy`, `used`, `wasAssociatedWith` (see #52)
- Command line flag `--v` enables logging to the console.
- Command line flag `--profile` enables profiling of a tool run.
- Test suite.
- Documentation for config file options in the config file example.
- Model documentation including descriptions of each node and relationship with their respective properties.
- `requirements_dev.txt` to install development dependencies.
 
### Fixed
- Releases without evidence no longer lead to IndexError. (see #53)
- Processing parent commits no longer leads to errors. (#37)
- Missing event classifiers are now handled gracefully. (#38)

### Changed
- Support comma-seperated lists of URLs for config file option `project_urls`.
- Rename `aliases` to `double_agents` in the config file and command line interface.
- Rename `pseudonymize` to `pseudonymous` in the config file and command line interface.
- Rename the config file sections to match the new CLI subcommands
- Stop manual file history computation. Each file revision now has exactly one previous revision instead of one or more.
- Use the modification model for commit statuses: MODIFIED, RENAMED, COPIED, CHANGED.
- Ignore file revisions with unkown commit status.
- Change event classification to use the package `regex` that supports branch reset expressions.
- Change build process to use `pyproject.toml` aswell as `setup.cfg`
- Change architecture to messagebus in anticipation of future features.
- Bump minimum required `prov` version to 2.0.0

### Removed
- Rate limit flag/option `--r`/`rate_limit`. Asynchronicity during retrieval is no longer supported.
- Quiet flag/option `--q`/`quiet`. Default behavior is to be quiet by default unless the `--v` flag is set.
  

## [0.5] - 2021-06-21

### Added
- Support for 'tags' and 'releases' to PROV model (see #39)
- CITATION file in Citation File Format (CFF) (see #49)

### Changed
- Revisions (changes) of files expressed in PROV model (see #40)
 
### Fixed
- API client pagination (see #41)
- 'wasGeneratedBy' relation for 'tags' corrected (see #51)

### Removed
- Resource names from attributes (see #47, #48)

## [0.4.1] - 2021-04-23
### Added
- Support for wider range of GitLab events.
- Documentation for all new supported events.
  
### Fixed
- Errors when requesting deactivated API endpoints are now handled gracefully.

## [0.4] Pre-release - 2021-04-23
### Added
- Support for additional GitLab events.
  
### Fixed
- Error handling hotfix for requests to deactivated API endpoints.

## [0.3] - 2020-10-15

### Changed
- Updated PROV models in /docs to reflect changes in the PROV model.
- Updated config file example.
- Update usage section in README.
 
### Fixed
- Updated `setup.py` to resolve an issue for python versions below 3.8.
- Configuration errors are now handled gracefully.

### Removed
- Dependency on `prov-db-connector`. Neo4j import functionality is no longer part of this package.

## [0.2] - 2020-08-01

### Changed
- Project status marked for `gitlab2prov` usage in [@cdboer's](https://github.com/cdboer) bachelor thesis.

## [0.1] - 2020-01-22

### Added
- Revised README to provide a comprehensive overview of the project's objectives and instructions for usage.
- Initial public version of the gitlab2prov package.
- Preset queries tailored for use on the property graphs produced by the tool, implemented in Neo4j.
- `requirements.txt` file specifying the list of dependencies required to run the tool.

[unreleased]: https://github.com/dlr-sc/gitlab2prov/compare/v2.1.0...HEAD
[2.1.0]: https://github.com/dlr-sc/gitlab2prov/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/dlr-sc/gitlab2prov/compare/v1.1.4...v2.0.0
[1.1.4]: https://github.com/dlr-sc/gitlab2prov/compare/v1.1.3...v1.1.4
[1.1.3]: https://github.com/dlr-sc/gitlab2prov/compare/v1.1.2...v1.1.3
[1.1.2]: https://github.com/dlr-sc/gitlab2prov/compare/v1.1.1...v1.1.2
[1.1.1]: https://github.com/dlr-sc/gitlab2prov/compare/v1.1...v1.1.1
[1.1]: https://github.com/dlr-sc/gitlab2prov/compare/v1.0...v1.1
[1.0]: https://github.com/dlr-sc/gitlab2prov/compare/v0.5...v1.0
[0.5]: https://github.com/dlr-sc/gitlab2prov/compare/v0.4.1...v0.5
[0.4.1]: https://github.com/dlr-sc/gitlab2prov/compare/v0.4...v0.4.1
[0.4]: https://github.com/dlr-sc/gitlab2prov/compare/v0.3...v0.4
[0.3]: https://github.com/dlr-sc/gitlab2prov/compare/v0.2...v0.3
[0.2]: https://github.com/dlr-sc/gitlab2prov/compare/v0.1...v0.2
[0.1]: https://github.com/dlr-sc/gitlab2prov/releases/tag/v0.1