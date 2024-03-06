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

# # Creating an Excel import job

# An Excel import job is used to import data from a properly formatted Excel spreadsheet.
#
# This example shows how to create an Excel import job request, submit it to the job queue, and to
# interact with the resulting Excel import job object returned by the server.
#
# The details of how to create a properly-formatted Excel spreadsheet are outside the scope of this
# example. Consult the Granta MI documentation or your ACE representative for information on the
# use of Excel in importing data into Granta MI.

# ## Connecting to Granta MI

# Import the ``Connection`` class and create the connection. See the
# [Getting started](0_Getting_started.ipynb) example for more detail.

# + tags=[]
from ansys.grantami.jobqueue import Connection

server_url = "http://my_grantami_server/mi_servicelayer"
client = Connection(server_url).with_credentials("user_name", "password").connect()
# -

# ## Create an Excel import job request object

# The first step in importing an Excel file with the job queue is to create an
# ``ExcelImportJobRequest`` object. When creating this object, specify the name of the job and the
# file(s) to be imported. You can also specify an optional description and the scheduled execution
# date, if the import should be deferred until that date and time.
#
# Different job types require different input files. For example, an Excel import can use a
# 'template' and one or more 'data' files, or a single 'combined' file. Any additional files
# to be imported as file attributes should be specified as 'attachment' files. These can be provided
# as relative or absolute paths or as `pathlib.Path` objects.

# +
import datetime
import pathlib

from ansys.grantami.jobqueue import ExcelImportJobRequest

separate_excel_import_request = ExcelImportJobRequest(
    name="Excel Import (separate template and data files)",
    description="An example excel import job",
    data_files=["data_file_1.xlsx", "data_file_2.xlsx"],
    template_files=["import_template.xlsx"],
)
separate_excel_import_request
# -

# +
try:
    # Python 3.11+
    tomorrow = datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=1)
except AttributeError:
    # Python 3.9 and 3.10
    tomorrow = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)
combined_excel_import_request = ExcelImportJobRequest(
    name="Excel Import (combined template and data file)",
    description="An example excel import job",
    scheduled_execution_date=tomorrow,
    combined_files=[pathlib.Path("combined_import_file.xlsx")],
)


combined_excel_import_request
# -

# ## Submit jobs
# Next, submit the jobs to the server. There are two ways to submit the job:
#
# * ``create_job()``: Submit the job request to the server and immediately return an
#   ``AsyncJob`` object in the 'pending' state.
# * ``create_job_and_wait()``: Submit the job request to the server and block until the job
#    either completes or fails. Return an ``AsyncJob`` object in the 'succeeded' or 'failed' state.

# +
completed_job = client.create_job_and_wait(separate_excel_import_request)

deferred_job = client.create_job(combined_excel_import_request)
deferred_job
# -

# ## Edit existing jobs
# The properties of a running or completed job can be edited with the associated ``AsyncJob``
# object. For example, a scheduled job can be brought forward, or the name and description can be
# changed.

deferred_job.update_name("Combined Excel Import (modified)")
deferred_job.update_description("A new description for a combined Excel import job")
try:
    # Python 3.11+
    now = datetime.datetime.now(datetime.UTC)
except AttributeError:
    # Python 3.9 and 3.10
    now = datetime.datetime.now(datetime.timezone.utc)
deferred_job.update_scheduled_execution_date_time(now)
client.jobs

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
# Finally, access the results of the job. Import jobs typically create log files, but the exact type
# of files generated varies based on the type of import template. In this case, the files are all
# plain text.

# Access the list of files generated by the job with the ``output_file_names`` property. This
# returns a list of file names.

deferred_job.output_file_names

# The following cell shows accessing the file content as ``bytes`` using the
# ``AsyncJob.get_file_content`` method.

# +
file_1_name = deferred_job.output_file_names[0]
file_1_content = deferred_job.get_file_content(file_1_name)
file_1_string = file_1_content.decode("utf-8")
print(f"{file_1_name} (first 200 characters):")
print(f"{file_1_string[:500]}...")
# -

# The following cell shows , or downloading the file to disk with the ``AsyncJob.download_file``
# method.

# +
file_2_name = deferred_job.output_file_names[1]
output_path = f"./{file_2_name}"
deferred_job.download_file(file_2_name, output_path)
f"{file_2_name} saved to disk"
# -
