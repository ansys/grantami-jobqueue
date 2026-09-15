.. _ref_grantami_jobqueue_models:

Models
=======

Job requests
------------

.. autoclass:: ansys.grantami.jobqueue.JobRequest
   :members:


.. autoclass:: ansys.grantami.jobqueue.ExcelExportJobRequest
   :members:


.. autoclass:: ansys.grantami.jobqueue.ExcelImportJobRequest
   :members:


.. autoclass:: ansys.grantami.jobqueue.TextImportJobRequest
   :members:


.. autoclass:: ansys.grantami.jobqueue.ExcelValidateJobRequest
   :members:


Jobs
----

.. autoclass:: ansys.grantami.jobqueue.AsyncJob
   :members:


.. autoclass:: ansys.grantami.jobqueue.ImportJob
   :members:


.. autoclass:: ansys.grantami.jobqueue.ExportJob
   :members:


Other models
------------

.. autoclass:: ansys.grantami.jobqueue.JobFile


.. autoclass:: ansys.grantami.jobqueue.ExportRecord


.. autoclass:: ansys.grantami.jobqueue.JobQueueProcessingConfiguration
   :members:


.. autoclass:: ansys.grantami.jobqueue.JobStatus
   :exclude-members: Pending, Running, Succeeded, Failed, Cancelled, Deleted

.. autodata:: ansys.grantami.jobqueue.JobStatus.Pending

.. autodata:: ansys.grantami.jobqueue.JobStatus.Running

.. autodata:: ansys.grantami.jobqueue.JobStatus.Succeeded

.. autodata:: ansys.grantami.jobqueue.JobStatus.Failed

.. autodata:: ansys.grantami.jobqueue.JobStatus.Cancelled

.. autodata:: ansys.grantami.jobqueue.JobStatus.Deleted


.. autoclass:: ansys.grantami.jobqueue.JobType
   :members:
