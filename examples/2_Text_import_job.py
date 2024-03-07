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

# # Creating a Text import job

# A Text import job is used to import data from a plan text file with an accompanying import
# template.
#
# This example shows how to create an Text import job request, submit it to the job queue, and to
# interact with the resulting Text import job object returned by the server.
#
# The details of how to create a text import template are outside the scope of this example. Consult
# the Granta MI documentation or your ACE representative for information on how to import plain text
# data into Granta MI.

# ## Connecting to Granta MI

# Import the ``Connection`` class and create the connection. See the
# [Getting started](0_Getting_started.ipynb) example for more detail.

# + tags=[]
from ansys.grantami.jobqueue import Connection

server_url = "http://my_grantami_server/mi_servicelayer"
client = Connection(server_url).with_credentials("user_name", "password").connect()
# -

# ## Create a Text import job request object

# The first step in importing a text file with the job queue is to create a
# ``TextImportJobRequest`` object. When creating this object, specify the name of the job and the
# file(s) to be imported. You can also specify an optional description and the scheduled execution
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
    data_files=["./text_import_data.txt", "./text_import_data.RLT"],
    template_files=[pathlib.Path("./text_import_template.xml")],
)

text_import_request
# -

# ## Submit jobs
# Next, submit the jobs to the server. There are two ways to submit the job:
#
# * ``create_job()``: Submit the job request to the server and immediately return an
#   ``AsyncJob`` object in the 'pending' state.
# * ``create_job_and_wait()``: Submit the job request to the server and block until the job
#    either completes or fails. Return an ``AsyncJob`` object in the 'succeeded' or 'failed' state.
#
# This example submits the job and waits for a response.

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

# The following cell shows accessing the content of the log file as ``bytes`` using the
# ``AsyncJob.get_file_content`` method.

# +
log_file_name = next(name for name in text_import_job.output_file_names if "log" in name)
log_file_content = text_import_job.get_file_content(log_file_name)
log_file_string = log_file_content.decode("utf-8")
print(f"{log_file_name} (first 200 characters):")
print(f"{log_file_string[:500]}...")
# -

# The following cell shows downloading the import summary file to disk with the
# `AsyncJob.download_file`` method.

# +
summary_file_name = next(
    name for name in text_import_job.output_file_names if name == "summary.json"
)
output_path = f"./{summary_file_name}"
text_import_job.download_file(summary_file_name, output_path)
f"{summary_file_name} saved to disk"
# -
