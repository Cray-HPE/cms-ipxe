# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- Added support to allow two seperate containers, one for aarch64 and one for x86-64
- Added aarch64 specific control variables and configmaps for aarch64 builds
- Added builder log level settings in global configmap
### Changed
- Refactored liveness code to account for unified source of liveness information
- Threaded livevess probe heartbeat to detect failed containers
- Refactored crayipxe/service.py into new multitarchitecture entrant builds into crayupxe/builder.py
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
