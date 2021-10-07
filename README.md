ipyvue-comm
===========

Asynchronous communication channels between Vue components in Jupyter and Python.

Installation
------------

To install use pip:

    pip install ipyvue_comm

Development
-----------

Install a local copy of this package:

    git clone https://github.com/flatsurf/ipyvue-comm.git
    cd ipyvue-comm
    pip install -e .

When working with the classical notebook:

    jupyter nbextension install --py --symlink --overwrite --sys-prefix ipyvue_comm
    jupyter nbextension enable --py --sys-prefix ipyvue_comm

When working with JupyterLab:

    jupyter labextension develop --overwrite ipyvue_comm

To rebuild the JavaScript code after making changes to anything in the `js/`
directory:

    cd js
    yarn run build

When working with JupyterLab you also need to reinstall the Python package:

    cd ..
    pip install -e . --no-deps

You then need to refresh the Notebook/JupyterLab page for the changes to take effect.
