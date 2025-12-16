.. _ref_grantami_jobqueue_examples:

Examples
========

The following examples demonstrate key aspects of Granta MI JobQueue.

To run these examples, install dependencies with this command:

.. code::

   pip install ansys-grantami-jobqueue[examples]

And launch ``jupyterlab`` with this command:

.. code::
   jupyter lab


.. jinja:: examples

    {% if build_examples %}

    .. toctree::
       :maxdepth: 2

       0_Getting_started
       1_Excel_import_job
       2_Text_import_job
       3_Excel_export_job
       4_Scheduling_and_modifying_jobs

    {% else %}

    .. toctree::
       :maxdepth: 2

       test_example

    {% endif %}
