#*******************************************************************************
# Copyright (c) 2021 Julian Rüth <julian.rueth@fsfe.org>
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
#*******************************************************************************

from traitlets import Unicode
from ipywidgets import DOMWidget

class ForceLoad(DOMWidget):
    r"""
    ipyvue-async includes this widget to force the `activate()` function in the
    JavaScript part of ipyvue-async to run.

    We need this to make sure that the `<comm/>` component gets
    registered with Vue.js before any Vue code gets rendered by ipyvue.
    """
    _model_name = Unicode('ForceLoadModel').tag(sync=True)
    _model_module = Unicode('ipyvue-async').tag(sync=True)
    _model_module_version = Unicode('^1.0.0').tag(sync=True)

force_load = ForceLoad()
