# ---
# jupyter:
#   granta:
#     clean_database: true
#   jupytext:
#     notebook_metadata_filter: granta
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.14.1
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# # Scheduling and modifying jobs

# This example shows the steps required to create a job request, schedule it for execution in the
# future, and modify the scheduled job before it completes.
#
# This example uses an Excel import job, but the functionality demonstrated here can be applied
# to text import and Excel export jobs.

# ## Connecting to Granta MI

# Import the ``Connection`` class and create the connection. See the
# [Getting started](0_Getting_started.ipynb) example for more detail.

# + tags=[]
from ansys.grantami.jobqueue import Connection

server_url = "http://my_grantami_server/mi_servicelayer"
client = Connection(server_url).with_credentials("user_name", "password").connect()
# -

# ## Create an Excel import job request object

# This cell creates an Excel import job request and schedules it for execution tomorrow.
# This example does not contain a full description of the Excel import job request object. See the
# [Excel import job](1_Excel_import_job.ipynb) example for more details.

# +
import datetime
import pathlib

try:
    # Python 3.11+
    from datetime import UTC as utc
except ImportError:
    # Python 3.9 and 3.10
    from datetime import timezone

    utc = timezone.utc

from ansys.grantami.jobqueue import ExcelImportJobRequest

tomorrow = datetime.datetime.now(utc) + datetime.timedelta(days=1)
combined_excel_import_request = ExcelImportJobRequest(
    name="Excel Import (combined template and data file)",
    description="An example excel import job",
    combined_files=[pathlib.Path("combined_import_file.xlsx")],
    scheduled_execution_date=tomorrow,
)

combined_excel_import_request
# -

# ## Submit the job
# Next, submit the jobs to the server. There are two ways to submit the job:
#
# * ``create_job()``: Submit the job request to the server and immediately return an
#   ``AsyncJob`` object in the 'pending' state.
# * ``create_job_and_wait()``: Submit the job request to the server and block until the job
#    either completes or fails. Return an ``AsyncJob`` object in the 'succeeded' or 'failed' state.
#
# Since we have configured the Excel job request object to execute tomorrow, we must use the
# ``create_job()`` method. If we used the ``create_job_and_wait()`` method, it would block until
# the job completed, and so this script would take 24 hours to complete!

# +
deferred_job = client.create_job(combined_excel_import_request)
deferred_job
# -

# ## List jobs
# Use the ``.jobs`` property to list the jobs on the server.

client.jobs

# Note that only jobs the current user has access to are included in this property.  Non-admin users
# can only access and modify their own jobs. Admin users can access and modify all jobs on the
# server.

# ## Edit existing jobs
# The properties of a running or completed job can be edited with the associated ``AsyncJob``
# object. The cell below shows updating the name and description of the job, and changing the
# scheduled execution to occur immediately.

# +
deferred_job.update_name("Combined Excel Import (modified)")
deferred_job.update_description("A new description for a combined Excel import job")

now = datetime.datetime.now(utc)
deferred_job.update_scheduled_execution_date_time(now)

client.jobs
# -

# ## Retrieve long-running jobs
# If the job is expected to take a long time to complete, the Job ID could be saved to disk and
# used to check the status of the job later using the ``client.get_job_by_id()`` method.

# +
job_id = deferred_job.id
retrieved_job = client.get_job_by_id(job_id)
retrieved_job
# -

# Wait for the pending job to complete.

# +
import time

from ansys.grantami.jobqueue import JobStatus

while deferred_job.status not in [JobStatus.Succeeded, JobStatus.Failed]:
    time.sleep(1)
    deferred_job.update()

deferred_job.status
# -

# ## Access output files
# The job is now complete, and the files generated by the job can be accessed in the same way as for
# jobs that execute immediately.

log_file_name = next(name for name in deferred_job.output_file_names if "log" in name)
log_file_content = deferred_job.get_file_content(log_file_name)
log_file_string = log_file_content.decode("utf-8")
print(f"{log_file_name} (first 200 characters):")
print(f"{log_file_string[:500]}...")

# ## Deleting a job
# Jobs can be deleted from the job queue by using the ``.delete_jobs()`` method. This method
# accepts a list of jobs, so multiple jobs can be deleted with a single request if required.

client.delete_jobs([deferred_job])
client.jobs