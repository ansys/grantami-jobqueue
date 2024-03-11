.. _ref_migration:

.. currentmodule:: ansys.grantami.jobqueue

Migrating from AsyncJobs
########################

Overview
========

The import and export tools available in PyGranta JobQueue was previously available in the Granta MI
Scripting Toolkit AsyncJobs submodule. As of the 2024 R2 release, this capability is now only
available in the PyGranta JobQueue module. The current page provides a summary of the differences
between these two packages, and shows how to modify existing code to work against the new package.

In addition, this package is `PEP 561 <PEP561_>`_ compliant, and so mypy or most modern Python IDEs
can be used to statically validate ``AsyncJobs`` scripts against this package. This highlights
issues without needing to run the code.

.. _PEP561: https://peps.python.org/pep-0561/

Connecting to Granta MI
=======================

.. highlight:: python

AsyncJobs relied on an existing Scripting Toolkit connection to connect to the job queue. Instead,
JobQueue uses the PyGranta approach to creating a client. Replace your existing code::

   from GRANTA_MIScriptingToolkit import granta as mpy

   mi = mpy.connect('http://my_grantami_server/mi_servicelayer', autologon=True)
   job_queue = mi.get_async_job_queue()

with the equivalent::

   from ansys.grantami.jobqueue import Connection

   server_url = "http://my_grantami_server/mi_servicelayer"
   client = Connection(server_url).with_autologon().connect()

See the :ref:`examples/0_Getting_started` example for more detail on how to connect to Granta MI
using other authentication methods.


Creating a ``JobRequest``
=========================

Minor modifications have been made to the :class:`JobRequest` object and its concrete subclasses:

.. vale off

* Only :class:`pathlib.Path` and string values for file inputs are now permitted. File objects
  are no longer allowed.
* The ``templates`` keyword argument has changed to ``template`` and now only accepts a single
  value.

.. vale on


Submitting a ``JobRequest`` to the queue
========================================

The methods formerly available on the ``AsyncJobQueue`` that were used to create jobs have been
renamed to reflect that jobs may now be import or export jobs:

* ``AsyncJobQueue.create_import_job_and_wait`` is now :meth:`JobQueueApiClient.create_job_and_wait`
* ``AsyncJobQueue.create_import_job`` is now :meth:`JobQueueApiClient.create_job`


``AsyncJob`` properties
=======================

Two ``AsyncJob`` properties have changed type:

* :attr:`AsyncJob.status` now returns a :class:`JobStatus` member instead of a string
* :attr:`AsyncJob.type` now returns a :class:`JobType` member instead of a string


Querying the job queue (``jobs_where()``)
=========================================

The :meth:`~JobQueueApiClient.jobs_where` method previously accepted :class:`str` values for the
``job_type`` and ``status`` keyword arguments. These are now enumerations, and members of the
:class:`JobType` and :class:`JobStatus` classes should be provided instead.
