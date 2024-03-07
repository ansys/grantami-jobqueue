.. _ref_grantami_jobqueue_examples:

Examples
========

The following examples demonstrate key aspects of Granta MI JobQueue.

To run these examples, install dependencies with this code:

.. code::

   pip install ansys-grantami-jobqueue[examples]

.. jinja:: examples

    {% if build_examples %}

    .. toctree::
       :maxdepth: 2

       0_Getting_started
       1_Excel_import_job
       2_Text_import_job
       3_Excel_export_job
       4_Admin_functions

    {% else %}

    .. toctree::
       :maxdepth: 2

       test_example

    {% endif %}
