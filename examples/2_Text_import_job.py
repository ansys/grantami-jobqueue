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

# # Create a text import job

# You use a text import job to import data from a plain text file with an accompanying import
# template.
#
# This example shows how to create a text import job request, submit it to the job
# queue, and interact with the resulting text import job object returned by the server.
#
# Information on how to create a text import template is outside the scope of this example.
# For information on how to import plain text data into Granta MI, see the Granta MI documentation
# or consult your ACE representative.

# ## Connect to Granta MI

# Import the ``Connection`` class and create the connection. For more information,
# see the [Connect and access the job queue](0_Getting_started.ipynb) example.

# + tags=[]
from ansys.grantami.jobqueue import Connection

server_url = "http://my_grantami_server/mi_servicelayer"
client = Connection(server_url).with_credentials("user_name", "password").connect()
# -

# ## Create a ``TextImportJobRequest`` object

# The first step in importing a text file with the job queue is to create a
# ``TextImportJobRequest`` object. When creating this object, specify the name of the job and the
# files to import. You can also specify an optional description and the scheduled execution
# date, if the import should be deferred until that date and time.
#
# A text import job requires data files, template files, and optionally additional files to be
# uploaded as attachments. These can be provided as relative or absolute paths or as `pathlib.Path`
# objects.

# +
import pathlib

from ansys.grantami.jobqueue import TextImportJobRequest

text_import_request = TextImportJobRequest(
    name="Text Import",
    description="An example text import job",
    template_file=pathlib.Path("./assets/text_import_template.xml"),
    data_files=["./assets/example_data.txt"],
)

text_import_request
# -

# ## Submit the job to the server
# Next, submit the jobs to the server. There are two methods for submitting job
# requests:
#
# * ``create_job()``: Submit the job request to the server and immediately return an
#   ``AsyncJob`` object in the *pending* state.
# * ``create_job_and_wait()``: Submit the job request to the server and block until the job
#    either completes or fails. Return an ``AsyncJob`` object in the *succeeded* or *failed* state.
#
# This example uses the ``create_job_and_wait()`` method. For an example that shows
# how to create and submit a job that runs asynchronously, see
# [Schedule and modify jobs](4_Scheduling_and_modifying_jobs.ipynb).

# +
text_import_job = client.create_job_and_wait(text_import_request)
text_import_job
# -

# ## Access output files
# Finally, access the results of the job. Import jobs typically create log files, but the exact type
# of files generated varies based on the type of import template. In this case, the files are all
# plain text.

# Access the list of files generated by the job with the ``output_file_names`` property. This
# returns a list of file names.

text_import_job.output_file_names

# In general, a text import job includes a log of the import operation on the server as ``<job name>.log``.

# This cell shows how to access the content of the log file as ``bytes`` using the
# ``AsyncJob.get_file_content()`` method:

# +
log_file_name = next(name for name in text_import_job.output_file_names if "log" in name)
log_file_content = text_import_job.get_file_content(log_file_name)
log_file_string = log_file_content.decode("utf-8")
print(f"{log_file_name} (first 200 characters):")
print(f"{log_file_string[:500]}...")
# -
