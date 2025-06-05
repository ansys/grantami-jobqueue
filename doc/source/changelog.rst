.. _ref_release_notes:

Release notes
#############

This document contains the release notes for the project.

.. vale off

.. towncrier release notes start

`1.2.0rc0 <https://github.com/ansys/grantami-jobqueue/releases/tag/v1.2.0rc0>`_ - June 05, 2025
===============================================================================================

.. tab-set::


  .. tab-item:: Dependencies

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Update jinja2 to 3.1.6, cryptography to 44.0.1
          - `#188 <https://github.com/ansys/grantami-jobqueue/pull/188>`_

        * - Update ansys-openapi-common to v2.2.2
          - `#190 <https://github.com/ansys/grantami-jobqueue/pull/190>`_

        * - Bump version to 1.2.0.dev1
          - `#196 <https://github.com/ansys/grantami-jobqueue/pull/196>`_

        * - Tighten serverapi-openapi version specifier
          - `#219 <https://github.com/ansys/grantami-jobqueue/pull/219>`_

        * - Remove private PyPI references
          - `#220 <https://github.com/ansys/grantami-jobqueue/pull/220>`_


  .. tab-item:: Documentation

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Bump serverapi-openapi to 2025 R2 development version
          - `#178 <https://github.com/ansys/grantami-jobqueue/pull/178>`_

        * - Tidy up changelog entries
          - `#207 <https://github.com/ansys/grantami-jobqueue/pull/207>`_

        * - Add additional detail to 'output_file_names' docstring
          - `#208 <https://github.com/ansys/grantami-jobqueue/pull/208>`_

        * - Improve documentation for Granta MI version support
          - `#215 <https://github.com/ansys/grantami-jobqueue/pull/215>`_

        * - Include changelog in documentation
          - `#228 <https://github.com/ansys/grantami-jobqueue/pull/228>`_


  .. tab-item:: Maintenance

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Fix version number on main branch
          - `#168 <https://github.com/ansys/grantami-jobqueue/pull/168>`_

        * - chore: update CHANGELOG for v1.1.0
          - `#169 <https://github.com/ansys/grantami-jobqueue/pull/169>`_

        * - Bump codespell to 2.3.0 and fix issues
          - `#176 <https://github.com/ansys/grantami-jobqueue/pull/176>`_

        * - Support dependabot PRs while in development
          - `#180 <https://github.com/ansys/grantami-jobqueue/pull/180>`_

        * - Shutdown all VMs after CI is complete
          - `#184 <https://github.com/ansys/grantami-jobqueue/pull/184>`_

        * - Allow External Code Execution for Dependabot
          - `#185 <https://github.com/ansys/grantami-jobqueue/pull/185>`_

        * - Run integration tests on previous releases
          - `#186 <https://github.com/ansys/grantami-jobqueue/pull/186>`_

        * - Add Granta MI 2024 R1 integration tests
          - `#189 <https://github.com/ansys/grantami-jobqueue/pull/189>`_

        * - Use PyPI-authored publish action
          - `#210 <https://github.com/ansys/grantami-jobqueue/pull/210>`_

        * - Generate provenance attestations
          - `#211 <https://github.com/ansys/grantami-jobqueue/pull/211>`_

        * - Use git SHA to pin action version
          - `#217 <https://github.com/ansys/grantami-jobqueue/pull/217>`_

        * - Add integration checks completeness check
          - `#224 <https://github.com/ansys/grantami-jobqueue/pull/224>`_

        * - Move release branch to use 25R2 release VM
          - `#226 <https://github.com/ansys/grantami-jobqueue/pull/226>`_

        * - Prepare 1.2.0rc0 release
          - `#233 <https://github.com/ansys/grantami-jobqueue/pull/233>`_


`1.1.0 <https://github.com/ansys/grantami-jobqueue/releases/tag/v1.1.0>`_ - 2024-12-13
======================================================================================

.. tab-set::


  .. tab-item:: Added

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Add support for virtual paths
          - `#147 <https://github.com/ansys/grantami-jobqueue/pull/147>`_


  .. tab-item:: Changed

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Don't generate changelog fragments for dependabot PRs
          - `#90 <https://github.com/ansys/grantami-jobqueue/pull/90>`_

        * - Update version to v1.1
          - `#92 <https://github.com/ansys/grantami-jobqueue/pull/92>`_

        * - chore: update CHANGELOG for v1.0.1
          - `#104 <https://github.com/ansys/grantami-jobqueue/pull/104>`_

        * - Don't create changelog fragments for pre-commit updates
          - `#121 <https://github.com/ansys/grantami-jobqueue/pull/121>`_


  .. tab-item:: Fixed

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Fix 1.0.2 changelog
          - `#144 <https://github.com/ansys/grantami-jobqueue/pull/144>`_


  .. tab-item:: Dependencies

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Bump ServerAPI to 25R1
          - `#132 <https://github.com/ansys/grantami-jobqueue/pull/132>`_

        * - Upgrade serverapi-openapi to 4.0.0rc0
          - `#148 <https://github.com/ansys/grantami-jobqueue/pull/148>`_

        * - Bump grantami-serverapi-openapi to 4.0.0
          - `#149 <https://github.com/ansys/grantami-jobqueue/pull/149>`_


  .. tab-item:: Documentation

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Fix link to Issues on contribution page
          - `#156 <https://github.com/ansys/grantami-jobqueue/pull/156>`_


  .. tab-item:: Maintenance

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Auto-approve pre-commit-ci pull requests
          - `#130 <https://github.com/ansys/grantami-jobqueue/pull/130>`_

        * - Add job to release to private PyPI
          - `#133 <https://github.com/ansys/grantami-jobqueue/pull/133>`_

        * - chore: update CHANGELOG for v1.0.2
          - `#141 <https://github.com/ansys/grantami-jobqueue/pull/141>`_

        * - Add release environment in CI and prevent release without successful changelog step
          - `#143 <https://github.com/ansys/grantami-jobqueue/pull/143>`_

        * - Use Production VM for CI on release branch
          - `#154 <https://github.com/ansys/grantami-jobqueue/pull/154>`_

        * - Prepare for v1.1.0 release
          - `#167 <https://github.com/ansys/grantami-jobqueue/pull/167>`_


`1.0.2 <https://github.com/ansys/grantami-jobqueue/releases/tag/v1.0.2>`_ - 2024-10-03
======================================================================================

.. tab-set::


  .. tab-item:: Changed

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Use Release VM
          - `#105 <https://github.com/ansys/grantami-jobqueue/pull/105>`_


  .. tab-item:: Fixed

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Handle lack of job specific outputs
          - `#139 <https://github.com/ansys/grantami-jobqueue/pull/139>`_

        * - Prepare 1.0.2 release
          - `#140 <https://github.com/ansys/grantami-jobqueue/pull/140>`_


  .. tab-item:: Documentation

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Fix installation example for git dependency
          - `#134 <https://github.com/ansys/grantami-jobqueue/pull/134>`_

        * - Add link to supported authentication schemes
          - `#135 <https://github.com/ansys/grantami-jobqueue/pull/135>`_

        * - Add link to PyGranta version compatibility documentation
          - `#136 <https://github.com/ansys/grantami-jobqueue/pull/136>`_


  .. tab-item:: Maintenance

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Improve VM management in CI
          - `#137 <https://github.com/ansys/grantami-jobqueue/pull/137>`_


`1.0.1 <https://github.com/ansys/grantami-jobqueue/releases/tag/v1.0.1>`_ - 2024-06-10
======================================================================================

.. tab-set::


  .. tab-item:: Added

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Clarify meaning of JobStatus enum and ensure more import failures result in 'Failed' status
          - `#98 <https://github.com/ansys/grantami-jobqueue/pull/98>`_


  .. tab-item:: Changed

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - CI - 64 - Add doc-changelog action
          - `#78 <https://github.com/ansys/grantami-jobqueue/pull/78>`_

        * - Use trusted publisher
          - `#102 <https://github.com/ansys/grantami-jobqueue/pull/102>`_

        * - Cherry pick PR #102
          - `#103 <https://github.com/ansys/grantami-jobqueue/pull/103>`_


  .. tab-item:: Dependencies

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Prepare 1.0.1 release
          - `#101 <https://github.com/ansys/grantami-jobqueue/pull/101>`_


.. vale on