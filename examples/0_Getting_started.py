# Copyright (C) 2024 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: MIT
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

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

# # Getting started

# This example shows how to connect to Granta MI and access the job queue. For more information
# about creating and interacting with jobs, see the subsequent examples.

# ## Connect to Granta MI

# First, use the ``ansys.grantami.jobqueue.Connection`` class to connect to the Granta MI
# server. The ``Connection`` class uses a fluent interface to build the connection, which is always
# invoked in the following sequence:
#
# 1. Specify your Granta MI Service Layer URL as a parameter to the ``Connection`` class.
# 2. Specify the authentication method using a ``Connection.with_...()`` method.
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
# this example. For more information, see the
# [ansys-openapi-common](https://github.com/pyansys/openapi-common) package documentation.

# ## Access the Job Queue
# The ``client`` object can be used to determine the activities we can perform with the job queue.

# + tags=[]
f"The current user is an administrator: {client.is_admin_user}"
# -

# + tags=[]
f"The current user can write jobs: {client.can_write_job}"
# -

# We can also access information about how the job queue will process jobs.

f"Concurrency enabled: {'Yes' if client.processing_configuration.concurrency else 'No'}"

# Finally, we can access the job queue itself (the job queue may be empty if the current user
# has not submitted a job recently):

client.jobs

# Note: these are only the jobs accessible to the current user, which depends on the user's role.
# Standard users can only access their own jobs, whereas admin users can access jobs created by
# all users.
