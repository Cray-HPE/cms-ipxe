# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

## [1.11.7] - 2024-02-29

Reverted most of the content from [1.11.2] through [1.11.6]. Specifically,
the content is now equivalent to [1.11.1] plus:

### Changed
- Spelling corrections.
- Enabled building of unstable artifacts
- Updated header of update_versions.conf to reflect new tool options
- Disabled concurrent Jenkins builds on same branch/commit
- Added build timeout to avoid hung builds

### Fixed
- Update Chart with correct image and chart version strings during builds.

### Dependencies
- Moved to `PyYAML` `6.0.1` to prevent build issue.

## [1.11.6] - 2023-10-26
### Changed
- Fixed a typecasting bug encountered during evaluation of token timeout
- Changed the resultant docker image to include an entrypoint consistent with default use of an x86-64 builder, for use with mercury.

## [1.11.5] - 2023-07-12
### Added
- Added helm chart passthrough variables for build kind

## [1.11.4] - 2023-06-29
### Added
- Support for undionly.kpxe builds for x86-64

## [1.11.3] - 2023-06-23
### Added
- Added support to allow two seperate deployments, one for aarch64 and one for x86-64
- Added aarch64 specific control variables and configmaps for aarch64 builds
- Added builder log level settings in global configmap
- Added support for x86 based undionly.kpxe build variant through configmap 'build_kind' variable.
### Changed
- Refactored liveness code to account for unified source of liveness information
- Threaded liveness probe heartbeat to detect failed containers
- Refactored crayipxe/service.py into new multitarchitecture entrant builds into crayipxe/builder.py
- Update the liveness thread to terminate when the main build thread terminates
- Correct mismatch in aarch64's referenced configmap (previously was still referencing x86's version)
### Removed
- Deprecated configuration variables with no viable or used method for configuration

## [1.11.2] - 2023-04-14

### Fixed

- Make the build architecture and kind configurable to allow use on platforms that require KPXE binaries.

### Changed

- Spelling corrections.
- Enabled building of unstable artifacts
- Updated header of update_versions.conf to reflect new tool options

### Fixed

- Update Chart with correct image and chart version strings during builds.

## [1.11.1] - 2022-12-20

### Added

- Add Artifactory authentication to Jenkinsfile

## [1.11.0] - 20222-08-10

### Fixed
- CASMCMS-8149 - Fixed cleanup of old debug binary leftover from upgrade

### Changed
- Update internal domain addresses

## [1.10.0] - 2022-06-22 

### Changed

- Convert to gitflow/gitversion.
- CASMCMS-7992 - Allow for changing ipxe binary names.
- Update internal domain addresses

## [1.9.4] - (no date)
