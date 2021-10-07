from traitlets import Unicode
from ipywidgets import DOMWidget

class ForceLoad(DOMWidget):
    r"""
    ipyvue-comm includes this widget to force the `activate()` function in the
    JavaScript part of ipyvue-comm to run.

    We need this to make sure that the `<comm/>` component gets
    registered with Vue.js before any Vue code gets rendered by ipyvue.
    """
    _model_name = Unicode('ForceLoadModel').tag(sync=True)
    _model_module = Unicode('ipyvue-comm').tag(sync=True)
    _model_module_version = Unicode('^1.0.0').tag(sync=True)

force_load = ForceLoad()
