.. _ref_migration:

.. currentmodule:: ansys.grantami.jobqueue

User guide
##########

Migrate from AsyncJobs
======================

The import and export tools in PyGranta JobQueue were previously available in the Granta MI
Scripting Toolkit AsyncJobs submodule, which this documentation refers to as AnsyncJobs. As
of the Granta MI 2024 R2 release, however, these import and export tools are available only
in PyGranta JobQueue.

In addition to providing a summary of the differences between AsyncJobs and PyGranta JobQueue,
this section shows how to modify your existing AsyncJobs scripts to work in PyGranta JobQueue.

.. note::
  Because PyGranta JobQueue is `PEP 561 <PEP561_>`_-compliant, you can use `Mypy <https://pypi.org/project/mypy/>`_
  or most modern Python IDEs to statically validate AsyncJobs scripts against PyGranta JobQueue. This
  highlights issues without needing to run the code.

.. _PEP561: https://peps.python.org/pep-0561/

Connect to Granta MI
====================

.. highlight:: python

AsyncJobs relied on an existing Granta MI Scripting Toolkit connection to connect to the job queue.
PyGranta JobQueue uses the PyGranta approach to creating a client.

Your existing AsyncJobs code looks like this::

   from GRANTA_MIScriptingToolkit import granta as mpy

   mi = mpy.connect('http://my_grantami_server/mi_servicelayer', autologon=True)
   job_queue = mi.get_async_job_queue()

Replace the preceding code with this code::

   from ansys.grantami.jobqueue import Connection

   server_url = "http://my_grantami_server/mi_servicelayer"
   client = Connection(server_url).with_autologon().connect()

For information on how to connect to Granta MI using other authentication
methods, see :ref:`ref_grantami_jobqueue_connection` in the API reference documentation.


Create a job request
====================

There are some minor modifications to the :class:`JobRequest` object and its concrete subclasses:

.. vale off

* Only the :class:`pathlib.Path` object and string values for file inputs are permitted.
  File objects are no longer allowed.
* The ``templates`` keyword argument has changed to ``template`` and only accepts a single
  value.

.. vale on


Submit a job request to the queue
=================================

The ``AsyncJobQueue`` methods for creating jobs are renamed to reflect that jobs can
be import or export jobs:

* ``AsyncJobQueue.create_import_job_and_wait`` is renamed to :meth:`JobQueueApiClient.create_job_and_wait`.
* ``AsyncJobQueue.create_import_job`` is renamed to :meth:`JobQueueApiClient.create_job`.

Query the job queue
===================

Two ``AsyncJob`` attributes for querying the job queue have changed type:

* The :attr:`AsyncJob.status` attribute returns a member of the :class:`JobStatus` class instead of a string.
* The :attr:`AsyncJob.type` attribute returns a member of the :class:`JobType` class instead of a string.

The :meth:`~JobQueueApiClient.jobs_where` method, which accepted :class:`str` values for the
``job_type`` and ``status`` keyword arguments, are changed to enumerations. Thus, you must
provide members of the :class:`JobType` and :class:`JobStatus` classes.
