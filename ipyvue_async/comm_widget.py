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

import asyncio

from ipywidgets.widgets.widget import widget_serialization
from ipywidgets import DOMWidget
from traitlets import Unicode, Any

from ipyvue_async.force_load import force_load

class CommWidget(DOMWidget):
    r"""
    A widget that has a direct Comm channel to each of its representations in the frontend.

    Normally, widgets use the traitlet mechanism to talk between the
    JavaScript frontend and the Python backend. While this is great for many
    applications, this kind of communication is too slow for real time
    streaming of measurement data in practice. Also Comms are easily saturated
    when using the traitlets mechanism and it is hard to keep everything
    responsive. Using a Comm directly, allows us to have better control over
    these communication channels. However, actually directly using a Comm can
    be a bit tedious, so this class provides a widget with a wrapper, namely a
    `Client` for each frontend widget that is attached to this widget.
    """
    __force = Any(force_load, read_only=True).tag(sync=True, **widget_serialization)
    target = Unicode().tag(sync=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.target = f"{self.model_id}-comm-widget"

        # The currently registered clients, i.e., widget outputs in the frontend.
        self._channels = set()

        # A map of command names to callbacks.
        self._commands = {
            'register': self._register_client
        }

        # Start accepting connections from the frontend.
        self._register_comm_target()

        self._display_callbacks.register_callback(self._create_channel)

    def _create_channel(self, *args, **kwargs):
        from ipyvue_async.channel import Channel
        self._channels.add(Channel(self.log))

    async def call(self, target, endpoint, *args):
        for channel in self._channels:
            await channel.message("call", {
                "target": target,
                "endpoint": endpoint,
                "args": args,
            })

    async def poll(self, coroutine):
        future = asyncio.ensure_future(coroutine)

        events = 1
        delay = .001

        import jupyter_ui_poll
        async with jupyter_ui_poll.ui_events() as poll:
            while not future.done():
                await poll(events)

                events = min(events + 1, 64)

                await asyncio.sleep(delay)

                # Wait for at most 250ms, the reaction time of most
                # people, https://stackoverflow.com/a/44755058/812379.
                delay = min(2*delay, .25)

        return await future

    async def query(self, target, endpoint, *args, return_when=asyncio.ALL_COMPLETED):
        queries = [channel.query({
            "target": target,
            "endpoint": endpoint,
            "args": args}) for channel in self._channels]

        if not queries:
            raise ValueError("Cannot query when there is nothing displayed in the frontend yet.")

        results = [asyncio.get_running_loop().create_task(query) for query in queries]

        done, pending = await asyncio.wait(results, return_when=return_when)

        for awaitable in pending:
            awaitable.cancel()

        results = [result.result() for result in done]

        if return_when == asyncio.FIRST_COMPLETED:
            assert len(results) >= 1
            return results[0]
        else:
            return results

    def _receive(self, message):
        r"""
        Handle an incoming ``message``.
        """
        self.log.debug(f'CommWidget received message: {message}')
        try:
            data = message.get("content", {}).get("data", {})
            command = data.get("command", None)

            if command not in self._commands:
                raise NotImplementedError(f"Unsupported command {command}")

            self._commands[command](data)
        except Exception as e:
            self.log.error(e)

    def _register_client(self, data):
        r"""
        Called when the frontend sends a 'register' message.

        Open a comm in the opposite direction to this specific widget and wrap
        it in a client object.

        Note that client are currently never deregistered. This is usually not
        a big issue since all connections are essentially blocking and so
        inactive clients do not consume bandwidth to the frontend.
        """
        target = data["target"]

        self.log.debug(f"Registering client for {target}")

        from ipykernel.comm import Comm
        comm = Comm(target, {})

        for channel in self._channels:
            if not channel.is_connected():
                channel.connect(comm)
                return

        # This happens when a notebook is loaded with cells already
        # executed, e.g., when refreshing in the browser or opening the
        # same notebook twice.
        # There is no hope to reconnect this frontend to an existing
        # (orphaned) channel so we create a new one.
        self._create_channel()
        return self._register_client(data)

    def _register_comm_target(self):
        r"""
        Register a name that the frontend can connect to with a Comm.
        """
        def configure_comm(comm, open_msg):
            r"""
            Called when the initial message is received from the frontend.
            """
            @comm.on_msg
            def _recv(msg):
                r"""
                Called when any following message is received from the frontend.
                """
                self._receive(msg)

        self.comm.kernel.comm_manager.register_target(self.target, configure_comm)
