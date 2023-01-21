ipyvue-async does not work with recent versions of Jupyter anymore.

All the features of ipyvue-async are available in [ipyµvue](https://github.com/flatsurf/ipymuvue) which we recommend to use instead.

---

ipyvue-async
===========

Asynchronous communication channels between Vue components in Jupyter and Python.

Installation
------------

To install use pip:

    pip install ipyvue_async

Development
-----------

Install a local copy of this package:

    git clone https://github.com/flatsurf/ipyvue-async.git
    cd ipyvue-async
    pip install -e .

When working with the classical notebook:

    jupyter nbextension install --py --symlink --overwrite --sys-prefix ipyvue_async
    jupyter nbextension enable --py --sys-prefix ipyvue_async

When working with JupyterLab:

    jupyter labextension develop --overwrite ipyvue_async

To rebuild the JavaScript code after making changes to anything in the `js/`
directory:

    cd js
    yarn run build

You then need to refresh the Notebook/JupyterLab page for the changes to take effect.
