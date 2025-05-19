.. _ref_release_notes:

Release notes
#############

This document contains the release notes for the project. See release notes for v1.1.0 and earlier
in `CHANGELOG.md <https://github.com/ansys/grantami-jobqueue/blob/main/CHANGELOG.md>`_.

.. vale off

.. towncrier release notes start

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