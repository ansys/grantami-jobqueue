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

# # Create an Excel import job

# You use an Excel import job to import data from a properly formatted Excel spreadsheet.
#
# This example shows how to create an Excel import job request, submit it to the job
# queue, and interact with the resulting Excel import job object returned by the server.
#
# Information on how to create a properly formatted Excel import template is
# outside the scope of this example. For information on using Excel to import data into
# Granta MI, see the Granta MI documentation or consult your ACE representative.

# ## Connect to Granta MI

# Import the ``Connection`` class and create the connection. For more information,
# see the [Connect and access the job queue](0_Getting_started.ipynb) example.

# + tags=[]
from ansys.grantami.jobqueue import Connection

server_url = "http://my_grantami_server/mi_servicelayer"
client = Connection(server_url).with_credentials("user_name", "password").connect()
# -

# ## Create an ``ExcelImportJobRequest`` object

# The first step in importing an Excel file with the job queue is to create an
# ``ExcelImportJobRequest`` object. When creating this object, specify the name of the job and the
# files to import. You can also specify an optional description and the scheduled execution
# date, if the import should be deferred until that date and time.
#
# Different job types require different input files. For example, an Excel import can use a
# *template*, one or more *data* files, or *combined* files, which include both the template
# and data files. You should specicy any additional files to imported as file or picture attributes
# as *attachment* files. You can provide these additional files as relative or absolute paths or as
# ``pathlib.Path`` objects.

# +
from ansys.grantami.jobqueue import ExcelImportJobRequest

separate_excel_import_request = ExcelImportJobRequest(
    name="Excel Import (separate template and data files)",
    description="An example excel import job",
    template_file="assets/import_template.xlsx",
    data_files=["assets/data_file_1.xlsx", "assets/data_file_2.xlsx"],
)
separate_excel_import_request
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
completed_job = client.create_job_and_wait(separate_excel_import_request)
# -

# ## Access output files
# Finally, access the results of the job. Import jobs typically create log files, but the exact type
# of files generated varies based on the type of import template. In this case, the files are all
# plain text.

# Access the list of files generated by the job with the ``output_file_names`` property. This
# returns a list of file names.

completed_job.output_file_names

# In general, an Excel import job returns two files:
#
# - ``<job name>.log``: Log file of the import operation on the server
# - ``summary.json``: Data file that summarizes the number of records impacted by the import
#    job and provides details of any errors that occurred during processing.

# This cell shows how to access the content of the log file as ``bytes`` using the
# ``AsyncJob.get_file_content()`` method:

# +
log_file_name = next(name for name in completed_job.output_file_names if "log" in name)
log_file_content = completed_job.get_file_content(log_file_name)
log_file_string = log_file_content.decode("utf-8")
print(f"{log_file_name} (first 200 characters):")
print(f"{log_file_string[:500]}...")
# -

# This next cell shows how to download the import summary file to disk using the
# ``AsyncJob.download_file()`` method:

# +
summary_file_name = next(name for name in completed_job.output_file_names if name == "summary.json")
output_path = f"./{summary_file_name}"
completed_job.download_file(summary_file_name, output_path)
f"{summary_file_name} saved to disk"
# -
