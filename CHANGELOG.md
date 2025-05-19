# Changelog

This project uses [towncrier](https://towncrier.readthedocs.io/) and the
changes for the upcoming release can be found in
<https://github.com/ansys/grantami-jobqueue/tree/main/doc/changelog.d/>.

<!-- towncrier release notes start -->

## [1.1.0](https://github.com/ansys/grantami-jobqueue/releases/tag/v1.1.0) - 2024-12-13


### Added

- Add support for virtual paths [#147](https://github.com/ansys/grantami-jobqueue/pull/147)


### Changed

- Don't generate changelog fragments for dependabot PRs [#90](https://github.com/ansys/grantami-jobqueue/pull/90)
- Update version to v1.1 [#92](https://github.com/ansys/grantami-jobqueue/pull/92)
- chore: update CHANGELOG for v1.0.1 [#104](https://github.com/ansys/grantami-jobqueue/pull/104)
- Don't create changelog fragments for pre-commit updates [#121](https://github.com/ansys/grantami-jobqueue/pull/121)


### Fixed

- Fix 1.0.2 changelog [#144](https://github.com/ansys/grantami-jobqueue/pull/144)


### Dependencies

- Bump ServerAPI to 25R1 [#132](https://github.com/ansys/grantami-jobqueue/pull/132)
- Upgrade serverapi-openapi to 4.0.0rc0 [#148](https://github.com/ansys/grantami-jobqueue/pull/148)
- Bump grantami-serverapi-openapi to 4.0.0 [#149](https://github.com/ansys/grantami-jobqueue/pull/149)


### Documentation

- Fix link to Issues on contribution page [#156](https://github.com/ansys/grantami-jobqueue/pull/156)


### Maintenance

- Auto-approve pre-commit-ci pull requests [#130](https://github.com/ansys/grantami-jobqueue/pull/130)
- Add job to release to private PyPI [#133](https://github.com/ansys/grantami-jobqueue/pull/133)
- chore: update CHANGELOG for v1.0.2 [#141](https://github.com/ansys/grantami-jobqueue/pull/141)
- Add release environment in CI and prevent release without successful changelog step [#143](https://github.com/ansys/grantami-jobqueue/pull/143)
- Use Production VM for CI on release branch [#154](https://github.com/ansys/grantami-jobqueue/pull/154)
- Prepare for v1.1.0 release [#167](https://github.com/ansys/grantami-jobqueue/pull/167)

## [1.0.2](https://github.com/ansys/grantami-jobqueue/releases/tag/v1.0.2) - 2024-10-03


### Changed

- Use Release VM [#105](https://github.com/ansys/grantami-jobqueue/pull/105)

### Documentation

- Fix installation example for git dependency [#134](https://github.com/ansys/grantami-jobqueue/pull/134)
- Add link to supported authentication schemes [#135](https://github.com/ansys/grantami-jobqueue/pull/135)
- Add link to PyGranta version compatibility documentation [#136](https://github.com/ansys/grantami-jobqueue/pull/136)

### Maintenance

- Improve VM management in CI [#137](https://github.com/ansys/grantami-jobqueue/pull/137)

### Fixed

- Handle lack of job specific outputs [#139](https://github.com/ansys/grantami-jobqueue/pull/139)
- Prepare 1.0.2 release [#140](https://github.com/ansys/grantami-jobqueue/pull/140)

## [1.0.1](https://github.com/ansys/grantami-jobqueue/releases/tag/v1.0.1) - 2024-06-10


### Added

- Clarify meaning of JobStatus enum and ensure more import failures result in 'Failed' status [#98](https://github.com/ansys/grantami-jobqueue/pull/98)


### Changed

- CI - 64 - Add doc-changelog action [#78](https://github.com/ansys/grantami-jobqueue/pull/78)
- Use trusted publisher [#102](https://github.com/ansys/grantami-jobqueue/pull/102)
- Cherry pick PR #102 [#103](https://github.com/ansys/grantami-jobqueue/pull/103)


### Dependencies

- Prepare 1.0.1 release [#101](https://github.com/ansys/grantami-jobqueue/pull/101)
