|pyansys| |python| |pypi| |GH-CI| |codecov| |MIT| |black|

.. |pyansys| image:: https://img.shields.io/badge/Py-Ansys-ffc107.svg?labelColor=black&logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAIAAACQkWg2AAABDklEQVQ4jWNgoDfg5mD8vE7q/3bpVyskbW0sMRUwofHD7Dh5OBkZGBgW7/3W2tZpa2tLQEOyOzeEsfumlK2tbVpaGj4N6jIs1lpsDAwMJ278sveMY2BgCA0NFRISwqkhyQ1q/Nyd3zg4OBgYGNjZ2ePi4rB5loGBhZnhxTLJ/9ulv26Q4uVk1NXV/f///////69du4Zdg78lx//t0v+3S88rFISInD59GqIH2esIJ8G9O2/XVwhjzpw5EAam1xkkBJn/bJX+v1365hxxuCAfH9+3b9/+////48cPuNehNsS7cDEzMTAwMMzb+Q2u4dOnT2vWrMHu9ZtzxP9vl/69RVpCkBlZ3N7enoDXBwEAAA+YYitOilMVAAAAAElFTkSuQmCC
   :target: https://docs.pyansys.com/
   :alt: PyAnsys

.. |python| image:: https://img.shields.io/pypi/pyversions/ansys-grantami-jobqueue?logo=pypi
   :target: https://pypi.org/project/ansys-grantami-jobqueue/
   :alt: Python

.. |pypi| image:: https://img.shields.io/pypi/v/ansys-grantami-jobqueue.svg?logo=python&logoColor=white
   :target: https://pypi.org/project/ansys-grantami-jobqueue
   :alt: PyPI

.. |codecov| image:: https://codecov.io/gh/ansys/grantami-jobqueue/branch/main/graph/badge.svg
   :target: https://codecov.io/gh/ansys/grantami-jobqueue
   :alt: Codecov

.. |GH-CI| image:: https://github.com/ansys/grantami-jobqueue/actions/workflows/ci_cd.yml/badge.svg
   :target: https://github.com/ansys/grantami-jobqueue/actions/workflows/ci_cd.yml
   :alt: GH-CI

.. |MIT| image:: https://img.shields.io/badge/License-MIT-yellow.svg
   :target: https://opensource.org/licenses/MIT
   :alt: MIT

.. |black| image:: https://img.shields.io/badge/code%20style-black-000000.svg?style=flat
   :target: https://github.com/psf/black
   :alt: Black


PyGranta JobQueue
=================

..
   _after-badges


PyGranta JobQueue allows you to import and export correctly formatted Excel and text files to and from
Granta MI.


Dependencies
------------
.. readme_software_requirements

This version of the ``ansys.grantami.jobqueue`` package requires Granta MI 2024 R2 or newer. Use
`the PyGranta documentation <https://grantami.docs.pyansys.com/version/stable/package_versions>`_ to find the
version of this package compatible with older Granta MI versions.

The ``ansys.grantami.jobqueue`` package currently supports Python from version 3.10 to version 3.13.

.. readme_software_requirements_end



Installation
------------
.. readme_installation

To install the latest PyGranta JobQueue release from `PyPI <https://pypi.org/project/ansys-grantami-jobqueue/>`_,
run this command:

.. code::

    pip install ansys-grantami-jobqueue

To install a release compatible with a specific version of Granta MI, install the
`PyGranta <https://grantami.docs.pyansys.com/>`_ metapackage with a requirement specifier:

.. code::

    pip install pygranta==2024.2.0

To see which individual PyGranta package versions are installed with each version of the PyGranta metapackage, consult
the `Package versions <https://grantami.docs.pyansys.com/version/dev/package_versions.html>`_ section of the PyGranta
documentation.

Alternatively, to install the latest development version from the `PyGranta JobQueue repository <https://github.com/ansys/grantami-jobqueue>`_,
run this command:

.. code::

    pip install git+https://github.com/ansys/grantami-jobqueue.git


To install a local *development* version with Git and Poetry, run these commands:

.. code::

    git clone https://github.com/ansys/grantami-jobqueue
    cd grantami-jobqueue
    poetry install


The preceding commands install the package in development mode so that you can modify
it locally. Your changes are reflected in your Python setup after restarting the Python kernel.

.. readme_installation_end
