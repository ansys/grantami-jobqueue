# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.13.1
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# # Connect and access the job queue

# This example shows how to connect to Granta MI and access the job queue. For more information
# on creating and interacting with jobs, see the subsequent examples.

# ## Connect to Granta MI

# First, use the ``ansys.grantami.jobqueue.Connection`` class to connect to the Granta MI
# server. The ``Connection`` class uses a fluent interface to build the connection, which is always
# invoked in the following sequence:
#
# 1. Specify the URL for your Granta MI service layer as a parameter to the ``Connection`` class.
# 2. Specify the authentication method using a ``Connection.with_*()`` method.
# 3. Use the ``Connection.connect()`` method to finalize the connection.
#
# This returns an ``ansys.grantami.jobqueue.JobQueueApiClient`` object, which is called ``client``
# in these examples.

# + tags=[]
from ansys.grantami.jobqueue import Connection

server_url = "http://my_grantami_server/mi_servicelayer"
# -

# If you are running your Python script on Windows, you are generally able to use ``.with_autologon()``.

# + tags=[]
client = Connection(server_url).with_autologon().connect()
client
# -

# If the Python script is running on Linux without Kerberos enabled, or you want to use an account
# other than your logged-in account, you can specify credentials explicitly.

# + tags=[]
client = Connection(server_url).with_credentials("my_username", "my_password").connect()
client
# -

# OIDC and anonymous authentication methods are also available, but they are beyond the scope of
# this example. For more information, see the PyAnsys [OpenAPI-Common documentation](https://github.com/pyansys/openapi-common).

# ## Access the job queue
# You use the ``client`` object to determine the activities that you can perform with the job queue.

# + tags=[]
f"The current user is an administrator: {client.is_admin_user}"
# -

# + tags=[]
f"The current user can write jobs: {client.can_write_job}"
# -

# You can also access information on how the job queue processes jobs.

f"Concurrency enabled: {'Yes' if client.processing_configuration.concurrency else 'No'}"

# Finally, you can access the job queue itself. The job queue might be empty if no
# jobs have been submitted recently.)

client.jobs

# Note: The jobs accessible in the queue depend on the user's role.
# Standard users can only access their own jobs, whereas administrator users
# can access jobs created by all users.
