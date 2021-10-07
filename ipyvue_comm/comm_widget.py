from ipywidgets.widgets.widget import widget_serialization
from ipywidgets import DOMWidget
from traitlets import Unicode, Any

from .force_load import force_load

class CommWidget(DOMWidget):
    r"""
    A widget that has a direct Comm channel to its clients.

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
        self._clients = set()

        # The number of widget outputs in the frontend that we have created but
        # that have not connected to the backend.
        self._pending = 0

        # A map of command names to callbacks.
        self._commands = {
            'register': self._register_client
        }

        # Start accepting connections from the frontend.
        self._register_comm_target()

    def call(self, target, endpoint, *args):
        for client in self._clients:
            client.message("call", {
                "target": target,
                "endpoint": endpoint,
                "args": args,
            })

    def query(self, target, endpoint, *args):
        class Query:
            def __init__(self, queries):
                self._queries = queries

            @property
            async def values(self):
                import asyncio
                return [await query.value for query in self._queries]

            def done(self):
                return all([query.done() for query in self._queries])

        return Query([client.query({
            "target": target,
            "endpoint": endpoint,
            "args": args}) for client in self._clients])

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
        from ipykernel.comm import Comm
        comm = Comm(data["target"], {})
        self._clients.add(self._create_client(comm))
        self._pending -= 1
        assert self._pending >= 0

    def _create_client(self, comm):
        r"""
        Return the ``comm`` wrapped as a client object.
        """
        from .client import Client
        return Client(comm, self.log)

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
