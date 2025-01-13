# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.15.2] - 2025-1-10
### Fixed
- Assigning unique name to cms-ipxe job to avoid following upgrade issue:
  `post-upgrade cms-ipxe/templates/post-upgrade.yaml failed: jobs.batch "cms-ipxe" already exists chart=cms-ipxe`

## [1.15.1] - 2025-1-6
### Changed
- Added additional logic to correct for whitespace characters in helm options file

## [1.15.0] - 2024-12-16
### Added
- Added passthrough option for affecting global build options through the associated configset (global_additional_build_options).

## [1.14.2] - 2024-09-05

### Dependencies
- CSM 1.6 moved to Kubernetes 1.24, so use client v24.x to ensure compatability
- Bump `tj-actions/changed-files` from 44 to 45 ([#107](https://github.com/Cray-HPE/cms-ipxe/pull/107))
- Move to `cray-services` base chart version v11.0

## [1.14.1] - 2024-08-20

### Changed
- updated cray-ipxe-tpsw docker (ipxe-tpsw-clone repo) version

## [1.14.0] - 2024-08-20

### Changed
- Makes use of the new `--timeout` parameter for `ifconf -c dhcp` to stretch the window of time iPXE waits for packets to route when an MLAG is in play. This flag is only available after the recent adoption of newer iPXE source from [MTL-2104](https://jira-pro.it.hpe.com:8443/browse/MTL-2104).
- Updated `.gitignore` to ignore `Chart.lock` files created when running chart commands locally.

## [1.13.1] - 2024-07-24

### Dependencies
- Bump `certifi` and `PyJWT` dependency versions to resolve CVEs

## [1.13.0] - 2024-07-17

### Fixed
- MTL-2104 - refresh iPXE codebase.

### Dependencies
- Bump `tj-actions/changed-files` from 42 to 44 ([#93](https://github.com/Cray-HPE/cms-ipxe/pull/93), [#94](https://github.com/Cray-HPE/cms-ipxe/pull/94))

## [1.12.1] - 2024-02-29

### Fixed
- MTL-2380 Fix carriage returns when block lives in `>` for BSS iPXE scripts.

## [1.12.0] - 2024-02-08

### Changed
- MTL-2371 Refactored BSS iPXE network interface loop
- Disabled concurrent Jenkins builds on same branch/commit
- Added build timeout to avoid hung builds

### Dependencies
- Bump `tj-actions/changed-files` from 37 to 42 ([#74](https://github.com/Cray-HPE/cms-ipxe/pull/74), [#76](https://github.com/Cray-HPE/cms-ipxe/pull/76), [#79](https://github.com/Cray-HPE/cms-ipxe/pull/79), [#81](https://github.com/Cray-HPE/cms-ipxe/pull/81), [#83](https://github.com/Cray-HPE/cms-ipxe/pull/83))
- Bump `actions/checkout` from 3 to 4 ([#75](https://github.com/Cray-HPE/cms-ipxe/pull/75))
- Bump `stefanzweifel/git-auto-commit-action` from 4 to 5 ([#77](https://github.com/Cray-HPE/cms-ipxe/pull/77))
- Bump `kubernetes` from 10.0.1 to 22.6.0 to match CSM 1.6 Kubernetes version
- Bump dependency patch versions:
  
    | Package                  | From    | To       |
    |--------------------------|---------|----------|
    | `google-auth`            | 1.6.1   | 1.6.3    |
    | `pyasn1`                 | 0.4.4   | 0.4.8    |
    | `pyasn1-modules`         | 0.2.2   | 0.2.8    |
    | `python-dateutil`        | 2.8.1   | 2.8.2    |
    | `rsa`                    | 4.7     | 4.7.2    |
    | `urllib3`                | 1.25.9  | 1.25.11  |
    | `websocket-client`       | 1.5.1   | 1.5.3    |

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
