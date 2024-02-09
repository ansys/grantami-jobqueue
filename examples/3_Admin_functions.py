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

# # Administrator functions

# The JobQueue API provides access to administrator functions. These are demonstrated in this
# example.

# ## Connecting to Granta MI

# Import the ``Connection`` class and create the connection. See the
# [Getting started](0_Getting_started.html) example for more detail.

# + tags=[]
from ansys.grantami.jobqueue import Connection

server_url = "http://my_grantami_server/mi_servicelayer"
client = Connection(server_url).with_credentials("user_name", "password").connect()
# -

# ## Clear the job queue

client.delete_jobs(client.jobs)

# ## Promote jobs to the top of the queue

# Need to design an example here. Create two jobs, promote one above?
